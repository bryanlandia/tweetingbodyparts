from os import getenv

from flask import Flask
from flask.ext.redis import FlaskRedis

app = Flask(__name__)
app.config.from_object('tweetmapper.default_settings')
app.config.from_envvar('TWEETMAPPER_SETTINGS')

redis_store = FlaskRedis(app)

from tweetmapper import views


# import fiona
# with fiona.open(app.config['STATES_SHAPE_FILE_PATH']) as collection:
# 	pass
