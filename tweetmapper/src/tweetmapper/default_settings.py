from datetime import timedelta

CELERY_BROKER_URL = 'redis://localhost'
CELERY_RESULT_BACKEND = 'redis://localhost'
CELERYBEAT_SCHEDULE = {
    'update-subject-counts-every-30-seconds': {
    'task': 'tasks.update_subject_counts',
    'schedule': timedelta(seconds=30),
	},
}
MAX_LOCATIONS = 20
MAX_TWEETS_PER_SEARCH = 100
TWITTER_SEARCH_LATLNG_INTERVAL = 1.75
TWITTER_MAX_TERMS_PER_SEARCH = 35

DEPLOYMENT = "production"