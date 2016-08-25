import base64
import copy 
import re
import math
import random
import time

from urllib import quote_plus
import requests
import json
import fiona
from shapely import geometry
import twitter

from celery.contrib import rdb as pdb
from flask.ext.celery import Celery

from tweetmapper import app, redis_store


celery = Celery(app)


class TwitterRateError(twitter.TwitterError):

    def __init__(self, status):
        self.status = status


@celery.task()
def update_subject_counts():
    """
    task called by celerybeat will update tweet subject count for
    a single state every X seconds as set in scheduler config.
    Twitter API limit is 450 requests every 15 minutes
    """
    # don't do anything if we are rate-limited by Twitter

    try:
        check_do_twitter_update()
    except TwitterRateError as e:
        reset = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(e.status.reset))
        return "Used {} API requests.  Waiting for Twitter ratelimit reset at {}".format(e.status.limit, reset)

    datapath = app.config['STATES_SHAPE_FILE_PATH']
    
    states_to_do = redis_store.get('states_to_do').split(',')
    state = states_to_do.pop()
    print "getting locations for state {}".format(state)

    locations = get_locations(datapath, state)
    try:
        subject_tweets_json = get_subject_tweets(locations)
    except twitter.error.TwitterError, e:
        states_to_do.append(state)
        redis_store.set('states_to_do', ','.join(states_to_do))
        return "Hit TwitterError {}.  Probably hit a RateLimit mid-run.  Wait and try again...".format(str(e))
        
    # overwrite old json object properties with new, add other new
    from_store = json.loads(redis_store.get('subject_data'))
    if from_store is None:
        from_store = {}

    new = json.loads(subject_tweets_json)
    from_store.update(new)
    merged = from_store
    redis_store.set('subject_data', json.dumps(merged))
    states_to_do.insert(0, state)
    redis_store.set('states_to_do', ','.join(states_to_do))


def check_do_twitter_update():
    subjects = get_subjects_to_search()
    subjects_len = len([word for word in [subj for subj in subjects.keys()]])
    max_terms = app.config["TWITTER_MAX_TERMS_PER_SEARCH"]
    num_queries_for_subjects = float(subjects_len)/float(max_terms)
    num_queries_for_subjects = int(math.ceil(num_queries_for_subjects))
    queries_by_task_run = app.config["MAX_LOCATIONS"] * num_queries_for_subjects


    # check if we might even have run out of requests to check our RateLimit
    check_rate_api = get_twitter_API(application_only=False, sleep_on_rate_limit=True)  # use user auth for this one 
    rlstatusstatus = check_rate_api.CheckRateLimit("https://api.twitter.com/1.1/application/rate_limit_status.json")
    if rlstatusstatus.remaining < 1:
        return False

    api = get_twitter_API()

    # TO DO also check the ratelimit for checking the ratelimit check endpoint
    # so we don't go over API limit on that too!
    rlstatus = api.CheckRateLimit("https://api.twitter.com/1.1/search/tweets.json")
    print "Twitter API limit:{}, remaining:{}".format(rlstatus.limit, rlstatus.remaining)
    if rlstatus.remaining < queries_by_task_run:
        raise TwitterRateError(rlstatus) 
    return True


def get_subjects_to_search():
    with open('static/data/bodyparts.json', 'r') as json_subjects:
        subjects = json.load(json_subjects)['subjects']
        return subjects
    

def get_twitter_API(application_only=True, sleep_on_rate_limit=False):
    with open(app.config['TWITTER_AUTH_FILE_PATH'], 'r') as json_auth:
        auth = json.load(json_auth)

    api = twitter.Api(consumer_key=auth['consumer_key'],
                      consumer_secret=auth['consumer_secret'],
                      access_token_key=auth['access_token_key'],
                      access_token_secret=auth['access_token_secret'],
                      application_only_auth=application_only,
                      sleep_on_rate_limit=sleep_on_rate_limit)
    
    return api


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
        rec = collection.next()
        while True:
            if rec['properties']['STATE_ABBR'] == state:
                break
            rec = collection.next()

        shape = geometry.asShape( rec['geometry'])
        (minx, miny, maxx, maxy) = shape.bounds
        x = minx 
        y = miny

        default_step = app.config["TWITTER_SEARCH_LATLNG_INTERVAL"]    
        with open('static/data/stephints.json', 'r') as sleep_hints:
            hints = json.load(sleep_hints)
            try:
                step_lat = hints[state]['steplat']
                step_lng = hints[state]['steplng']
                step_initial = hints[state].get('step_initial', [0,0])
            except KeyError:
                step_lat = step_lng = default_step
                step_initial = [0,0]

        y+= step_initial[0]
        x+= step_initial[1]

        while y < maxy:
            while x < maxx:
                p = geometry.Point(x,y)
                if shape.contains(p):
                    locations.append({'lat':y, 'lng':x})
                x += step_lng
            x = minx
            y+= step_lat
    return locations


def explode_subjects(subjects):
    keys = subjects.keys()
    explode_1 = [subjects[key] for key in keys]
    explode_2 = [item for sublist in explode_1 for item in sublist]
    return explode_2


def get_subject_tweets(locations):
    subjects =  get_subjects_to_search()
    search_word_count = 0
    max_terms = app.config["TWITTER_MAX_TERMS_PER_SEARCH"]
    search_strings = ['', ]
    subjects_list = subjects.keys()
    subjects_tweets = {}
    subjects_list_exploded = explode_subjects(subjects)
    for subject in subjects_list:
        subj, words = subject, subjects[subject]
        for word in words:
            concatenator = search_word_count == 0 and '' or ' OR '
            subjects_str = quote_plus('{}{}'.format(concatenator, word))
            if search_word_count % max_terms == 0:
                search_strings.append('')
            search_strings[int(math.floor(search_word_count / max_terms))] += subjects_str
            search_word_count += 1
            # subjects_str += quote_plus(' -'+' -'.join(APPLE_COMPUTER_RELATED_EXCLUDE).replace('\'','"'))
    
    api = get_twitter_API()
    loc_subjects = {}
    for loc in locations[:int(app.config['MAX_LOCATIONS'])]:
        subjects_count = dict.fromkeys(subjects_list, 0)

        # qry="q=pear%20&geocode={},{},10mi&result_type=recent&count=100".format(loc['lat'],loc['lng'])
        try:
            for search_str in search_strings:
                if search_str == '':
                    break
                if search_str.find('+OR+') == 0:  # make sure we don't start with an OR
                    search_str=search_str[4:]

                qry ="q={}&geocode={},{},50mi&result_type=recent&count={}".format(
                search_str, loc['lat'],loc['lng'], app.config['MAX_TWEETS_PER_SEARCH']).replace('++','+')
                results = api.GetSearch(raw_query=qry)
                # print "{},{} results:{}\n\n".format(loc['lat'],loc['lng'],results)
                for tweet in results:
                    try:
                        text = ' '+tweet.text.encode('ascii', 'ignore')+' '  # pre-/append a space for word searching
                        text = re.sub(r'https?:\/\/.*', '', text, flags=re.MULTILINE)
                        if 'retweet' in text.lower() or 'rt @' in text.lower():
                            continue
                        # find where the subject is mentioned...
                        # it may just be found in a word part in which case we reject this tweet
                        # so we'll prepend and append a space 
                        i = 0
                        try:
                            while text.lower().find(' '+subjects_list_exploded[i].lower()+' ') == -1:
                                i +=1
                        except IndexError:
                            # we didn't find the term                            
                            continue

                        # which subject is it?
                        word_found = subjects_list_exploded[i]
                        for subj in subjects:
                            if word_found in subjects[subj]:
                                subjects_count[subj] +=1
                                subjects_tweets[subj] = text
                                break
                        # print "{},{}\n------------\n{}".format(loc['lat'],loc['lng'],subjects_count)

                    except (ValueError, IndexError):
                        pass
        except twitter.error.TwitterError:
            raise 

        if not len(subjects_tweets.keys()):
            # didn't find any matches!
            continue

        most_subject = max(subjects_count.iterkeys(), key=(lambda key: subjects_count[key]))
        # print "{},{}:{}\n".format(loc['lat'],loc['lng'],most_subject)
        loc_subjects["{},{}".format(loc['lng'],loc['lat'])] = {"subj":most_subject, "tweet":subjects_tweets[most_subject]}
        # loc_subjects["{},{}".format(loc['lng'],loc['lat'])] = most_subject
    return json.dumps(loc_subjects)


# if __name__ == '__main__':
#     result = update_fruit_counts.delay()
#     redis_store.set('fruit_data', result)
