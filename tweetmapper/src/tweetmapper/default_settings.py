from datetime import timedelta

CELERY_BROKER_URL = 'redis://localhost'
CELERY_RESULT_BACKEND = 'redis://localhost'
CELERYBEAT_SCHEDULE = {
    'update-fruit-counts-every-30-seconds': {
    'task': 'tasks.update_fruit_counts',
    'schedule': timedelta(seconds=30),
	},
}
MAX_LOCATIONS = 25
MAX_TWEETS_PER_SEARCH = 100
