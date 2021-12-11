""" coding=utf-8 """

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoTest.settings')

app = Celery('django_test')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
