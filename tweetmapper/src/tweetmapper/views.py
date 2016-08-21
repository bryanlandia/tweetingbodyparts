import json
from tweetmapper import app, redis_store
from flask import render_template


@app.route("/")
def index():
	"""
	show the map
	"""
	return render_template("index.html")

@app.route("/data")
def get_latest_fruit_data():
	"""
	return stored JSON of all locations and the fruits the people there are
	tweeting about
	"""
	# start with stored dummy data
	# with open("tweetmapper/src/tweetmapper/tests/data/sampletwitter.json", "r") as json_data:
	# 	return json_data.read()
	return redis_store.get('fruit_data')

