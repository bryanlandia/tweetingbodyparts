import json

from flask import Flask
from flask_redis import FlaskRedis

import tweepy


app = Flask(__name__)
app.config.from_object('tweetmapper.default_settings')
app.config.from_envvar('TWEETMAPPER_SETTINGS')

redis_store = FlaskRedis(app)

states_to_do = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
     "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

# states_to_do = [
# "WY"
# ]

if redis_store.get('states_to_do') is None:
	redis_store.set('states_to_do', ",".join(states_to_do))

# this has to come last
from tweetmapper import views

with open(app.config['TWITTER_AUTH_FILE_PATH'], 'r') as json_auth:
    auth_dict = json.load(json_auth)

bearer_token = auth_dict['bearer_token']
twitter_client = tweepy.Client(bearer_token=bearer_token)
