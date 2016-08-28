import json
from tweetmapper import app, redis_store, states_to_do
from flask import render_template
from os import getenv


@app.route("/")
def index():
	"""
	show the map
	"""
	return render_template("index.html")

@app.route("/data")
def get_latest_subject_data():
	"""
	return stored JSON of all locations and the fruits the people there are
	tweeting about
	"""
	# start with stored dummy data
	# with open("tweetmapper/src/tweetmapper/tests/data/sampletwitter.json", "r") as json_data:
	# 	return json_data.read()
	return redis_store.get('subject_data')


if app.config['DEPLOYMENT'] == 'dev':
	@app.route("/reset_data")
	def reset_map_data():
		"""
		reset redis_store values
		"""
		redis_store.set('subject_data','{}')
		redis_store.set('states_to_do', ','.join(states_to_do))
		return "\n\nReset Redis store for subject_data and states_to_do"

	@app.route("/get_data")
	def get_data():
		"""
		return redis_store values
		"""
		subjs = redis_store.get('subject_data')
		states_to_do = redis_store.get('states_to_do')

		return "Redis store data:<br/><br/>states_to_do:<br/>{}<br/><br/>subject_data<br/>{}".format(states_to_do, subjs)

