import os
from celery import Celery
from django.conf import settings
# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FileSharingSystem.settings')
app = Celery('FileSharingSystem')
# Celery will apply all configuration keys with defined namespace
app.config_from_object('django.conf:settings')
# Load tasks from all registered apps 
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
