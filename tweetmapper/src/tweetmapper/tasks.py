from tweetmapper import app, redis_store
from flask.ext.celery import Celery

import re
import json
import fiona
from shapely import geometry
import twitter
from urllib import quote_plus


celery = Celery(app)


APPLE_COMPUTER_RELATED_EXCLUDE = [
"'Apple Watch'", 
# "'Apple computer'", 
# "'Apple computers'", 
# "'Apple laptop'", 
# "'Apple laptops'", 
# "'Apple macbook'", 
# "'Apple macboos'", 
"'Apple music'", 
"'Apple tv'", 
"'apple website'", 
# "'apple mail'", 
# "'apple ceo'", 
# "'apple stock'", 
]


@celery.task()
def update_fruit_counts():
	"""
	do some stuff
	"""
	datapath = app.config['STATES_SHAPE_FILE_PATH']
	# datapath = "/opt/sfpc/tweetsaboutfruit/data/states_21basic/states.shp"
	locations = get_locations(datapath, 'WA')
	fruits_tweets_json = get_fruit_tweets(locations)
	redis_store.set('fruit_data', fruits_tweets_json)


def get_locations(datapath, state):
	""" 
	return a list of lat/lng tuples for map requests based on boundary points from XML datafile,
	the zoom level, and map tile size desired
	"""

	# we want to get a list of every point for which to query Static Maps API
	# so this will be a large set of points which must all be contained inside the
	# shape of the state
	locations = []
	with fiona.open(datapath) as collection:
	    # In this case, we'll assume the shapefile only has one record/layer (e.g., the shapefile
	    # is just for the borders of a single country, etc.).
	    for rec in collection:
		    # while rec['properties']['STATE_ABBR'] != state:
		    # 	rec = collection.next()
		
			shape = geometry.asShape( rec['geometry'])
			(minx, miny, maxx, maxy) = shape.bounds
			x = minx 
			y = miny
			
			# step should be determined by zoom level and tile size
			step =  1  # dummy
			while y < maxy:
				while x < maxx:
					p = geometry.Point(x,y)
					if shape.contains(p):
						locations.append({'lat':y, 'lng':x})
					x += step
				x = minx
				y+= step
	print len(locations)
	return locations


def get_fruit_tweets(locations):
	with open('static/data/fruits.json', 'r') as json_fruits:
		fruits_list = json.load(json_fruits)['fruits']		
		fruits = quote_plus(' OR '.join(fruits_list).replace('\'','"'))
		fruits += quote_plus(' -'+' -'.join(APPLE_COMPUTER_RELATED_EXCLUDE).replace('\'','"'))
	with open(app.config['TWITTER_AUTH_FILE_PATH'], 'r') as json_auth:
		auth = json.load(json_auth)
	api = twitter.Api(consumer_key=auth['consumer_key'],
                      consumer_secret=auth['consumer_secret'],
                  	  access_token_key=auth['access_token_key'],
                  	  access_token_secret=auth['access_token_secret'])

	loc_fruits = {}
	for loc in locations[:int(app.config['MAX_LOCATIONS'])]:
		fruits_count = dict.fromkeys(fruits_list, 0)

		qry ="q={}&geocode={},{},10mi&result_type=recent&count={}".format(
			fruits, loc['lat'],loc['lng'], app.config['MAX_TWEETS_PER_SEARCH'])
		# qry="q=pear%20&geocode={},{},10mi&result_type=recent&count=100".format(loc['lat'],loc['lng'])
		results = api.GetSearch(raw_query=qry)
		# print "{},{} results:{}\n\n".format(loc['lat'],loc['lng'],results)
		for tweet in results:
			try:
				text = tweet.text.encode('ascii', 'ignore')
				text = re.sub(r'https?:\/\/.*', '', text, flags=re.MULTILINE)
				if 'retweet' in text.lower() or 'rt @' in text.lower():
					continue
				# find where the fruit is mentioned...
				i = 0
				while text.lower().find(fruits_list[i].lower()) == -1:
					i +=1
				# this gets the character index in text of the fruit word
				# index = text.lower().find(fruits_list[i].lower())

				# # grab 10 words before, 10 after fruit word
				# before = text[:index]
				# after = text[index:]
				# text = before.split(' ')[-10:] + after.split(' ')[:5]
				# text = ' '.join(text)
				# if fruit_str.find(text) == -1:
				# 	fruit_str += " " +text

				# which fruit is it?
				fruits_count[fruits_list[i]] +=1
				# print "{},{}\n------------\n{}".format(loc['lat'],loc['lng'],fruits_count)

			except (ValueError, IndexError):
				pass
		# print fruit_str+"\n\n-------------"
		most_fruit = max(fruits_count.iterkeys(), key=(lambda key: fruits_count[key]))
		# print "{},{}:{}\n".format(loc['lat'],loc['lng'],most_fruit)
		loc_fruits["{},{}".format(loc['lng'],loc['lat'])] = most_fruit
	return json.dumps(loc_fruits)


# if __name__ == '__main__':
#     result = update_fruit_counts.delay()
#     redis_store.set('fruit_data', result)
