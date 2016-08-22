from os import getenv

from flask import Flask
from flask.ext.redis import FlaskRedis

app = Flask(__name__)
app.config.from_object('tweetmapper.default_settings')
app.config.from_envvar('TWEETMAPPER_SETTINGS')

redis_store = FlaskRedis(app)

from tweetmapper import views


states_to_do = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
     "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

if redis_store.get('states_to_do') is None:
	redis_store.set('states_to_do', ",".join(states_to_do))


# import fiona
# with fiona.open(app.config['STATES_SHAPE_FILE_PATH']) as collection:
# 	pass
