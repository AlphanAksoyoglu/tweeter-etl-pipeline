'''
Tweet_Collector

Collects tweets from the Twitter API using the StreamListener of the Tweepy library
Collected tweets are written to mongoDB
DB and API credentials are read from ./config.py people to follow are stored in ./infos.py
'''

import config
import infos
import pymongo
from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener
import json
import time

def organize_tweet(status):
    '''
    Extended tweets and retweets keep the original poster and the tweet body in different places of the tweet
    This preprocessing function returns the original tweet text, and the original timestamp
    Also returns whether it is retweeted and the retweeting user info
    '''

    
    if 'RT' not in status['text']:

        retweet = False
        rt_user = False
    
        if (status['truncated'] == False):
            tweet_text = status['text']
        else:
            tweet_text = status['extended_tweet']['full_text']
    else:

        try:

            retweet = True
            rt_user = status['retweeted_status']['user']['screen_name']

            if (status['retweeted_status']['truncated'] == False):
                tweet_text = status['retweeted_status']['text']
            else:
                tweet_text = status['retweeted_status']['extended_tweet']['full_text']
        
        except:

            retweet = False 
            rt_user = False
            tweet_text = status['text']
            
    
    return retweet, rt_user, tweet_text, status['created_at']


def authenticate():
    """
    Handles tweeter API authentication. Credentials should be stored in ./config.py
    """
    auth = OAuthHandler(config.TW_API_KEY, config.TW_API_SECRET)
    auth.set_access_token(config.TW_ACC_TOKEN, config.TW_ACC_SECRET)

    return auth

class MaxTweetsListener(StreamListener):

    '''
    Inherits from StreamListener
    Defines on_connect, on_data, and on_error
    for detailed usage instructions see https://docs.tweepy.org/en/v3.2.0/streaming_how_to.html
    '''

    def __init__(self, max_tweets, *args, **kwargs):
        # initialize the StreamListener
        super().__init__(*args, **kwargs)
        # set the instance attributes
        self.max_tweets = max_tweets
        self.counter = 0
        self.tweet_list = []
        self.tweet_content = []

    def on_connect(self):
        '''
        On successful connection
        '''
        print('connected. listening for incoming tweets')



    def on_data(self, data):
        """
        Processes Tweet when it is intercepted. The tweet is first preprocessed by organize_tweet()
        Then the required info is pulled from the tweet and written to mongoDB
        """
        status = json.loads(data)
        # increase the counter
        self.counter += 1

        retweet, rt_user, tweet_text, created_time = organize_tweet(status)   

        if status['user']['id_str'] in infos.twitterids:

            who = status['user']['id_str']

            try:
                replied_to = status['in_reply_to_screen_name']
            except:
                replied_to = 'NULL'
       
        else:
            
            who = status['user']['screen_name']
            
            try:
                replied_to = infos.twitterids[status['in_reply_to_user_id_str']]
            except:
                replied_to = 'NULL'
            
        tweet = {
            
            'id': status['user']['id_str'], #status.user.id_str,
            'who': who,
            'replied_to': replied_to,
            'retweeted': retweet, #status['retweeted'], #status.retweeted,
            'retweeted_from': rt_user,
            'text': tweet_text,
            'timestamp' : created_time
        }

        #write to mongoDB here
        collection.insert_one(tweet)
        print(f'New tweet arrived: {tweet["text"]}')


        # check if we have enough tweets collected
        if self.max_tweets == self.counter:
            # reset the counter
            self.counter=0
            # return False to stop the listener
            return False


    def on_error(self, status):
        if status == 420:
            print(f'Rate limit applies. Stop the stream.')
            return False

if __name__ == '__main__':

    while True:

        # Set mongoDB Connection and get the tweet.data collection
        client = pymongo.MongoClient("mongodb")
        db = client.tweets
        collection = db.tweet_data

        # Authenticate API connection and listen to tweets (maximum 100 tweets per 5 mins)
        auth = authenticate()
        listener = MaxTweetsListener(max_tweets=100)
        stream = Stream(auth, listener)

        # Filter the tweets to only the ones we are interested in
        follow = list(infos.people.values())
        stream.filter(follow=follow, languages=['en'], is_async=False)

        time.sleep(60*5)
    