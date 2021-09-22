'''
Reads the highest and lowest scoring tweet from Postgres and sends these tweets to Slackbot
Keeps track of the last_time the information is pulled so at each iteration tweets collected
in the last hour are queried
'''

import requests
import config
from sqlalchemy import create_engine
import time
import pandas as pd
import logging
import os

last_time = '2000-01-01 00:00:00'
#SLACKBOT INIT
WEBHOOK = config.WEBHOOK


#POSTGRES INIT

HOST = 'postgres'
PORT = '5432'
USERNAME = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB = os.getenv("POSTGRES_DB")

conn_string = f'postgres://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB}'
engine = create_engine(conn_string)





time.sleep(20)
# while loop to constantly run slackbot, displaying query in two text blocks:
while True: 

    query_worst = f"""
    SELECT timestamp, text, sentiment_score
    FROM   tweets
    WHERE  timestamp BETWEEN \'{last_time}\'::timestamp AND now()::timestamp
    ORDER BY sentiment_score LIMIT 1
    """

    query_best = f"""
    SELECT timestamp, text, sentiment_score
    FROM   tweets
    WHERE  timestamp BETWEEN \'{last_time}\'::timestamp AND now()::timestamp
    ORDER BY sentiment_score DESC LIMIT 1
    """
    
    # reading query and write to variable with pandas:
    tweet_worst = pd.read_sql_query(query_worst, con=engine)
    tweet_best = pd.read_sql_query(query_best, con=engine)

    #SET THE LAST_TIME TO CURRENT_TIME
    last_time = str(pd.Timestamp.now())

    # get value of text and sentiment
    text_tweet_best = tweet_best['text'].iloc[0]
    sentiment_tweet_best =  tweet_best['sentiment_score'].iloc[0]
    
    text_tweet_worst = tweet_worst['text'].iloc[0]
    sentiment_tweet_worst =  tweet_worst['sentiment_score'].iloc[0]
    
    data = {
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Since the Last Update",
                #"emoji": 'true'
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*The Best Tweet Received*\n:+1: With a Score of {sentiment_tweet_best}\n{text_tweet_best}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*The Worst Tweet Received*\n:-1: With a Score of {sentiment_tweet_worst}\n{text_tweet_worst}"
            }
        }
    ]
}
    requests.post(url=WEBHOOK, json = data)
    #logging.critical('tweet displayed via slackbot')
    time.sleep(60*60)         # timer