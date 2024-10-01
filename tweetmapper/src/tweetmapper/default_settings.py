CELERY = {
    "broker_url": 'redis://localhost',
    "result_backend": 'redis://localhost',
    "beat_schedule": {
        'update-subject-counts': {
        'task': 'tasks.update_subject_counts',
        'schedule': 30,
        },
    }
}
MAX_LOCATIONS = 20
MAX_TWEETS_PER_SEARCH = 35
TWITTER_SEARCH_LATLNG_INTERVAL = 1.75
TWITTER_MAX_TERMS_PER_SEARCH = 35
TWEET_SEARCH_MILES_RADIUS = 30
TWEET_SEARCH_THROTTLE_ASS = 0.3  # don't search for 'butt/ass' results sometimes


DEPLOYMENT = "production"