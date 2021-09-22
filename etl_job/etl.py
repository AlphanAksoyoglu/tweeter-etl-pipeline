'''
Runs every 55 minutes
Reads everything from MongoDB assigns a sentiment score to tweets and dumps them to Postgres
Then gets rid of the MongoDB collection
The timestamp used is the timestamp of the posted tweet (original tweet in case of retweets)
'''

import pandas
import pymongo
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
from pymongo import MongoClient
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

while True:
    #POSTGRES INIT

    HOST = 'postgres'
    PORT = '5432'
    USERNAME = os.getenv("POSTGRES_USER")
    PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB = os.getenv("POSTGRES_DB")

    conn_string = f'postgres://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB}'
    engine = create_engine(conn_string)

    #MONGODB INIT
    client = pymongo.MongoClient("mongodb")
    db = client.tweets
    collection = db.tweet_data


    #GET EVERYTHING FROM MONGODB
    data = pd.DataFrame(list(collection.find()))
    #DROP THE _id COLUMN
    del data['_id']
    data['timestamp'] = pd.to_datetime(data['timestamp'])


    s = SentimentIntensityAnalyzer()
    data['sentiment_score'] = data['text'].apply(lambda x: x.replace('@','')).apply(lambda x: s.polarity_scores(x)['compound'])

    data.to_sql('tweets', engine, if_exists='append')

    client.drop_database('tweets')

    time.sleep(60*55)