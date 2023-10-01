import os
from celery import Celery
from django.conf import settings

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mailing.settings")

# Создаем объект Celery
app = Celery('mailings')

# Загружаем настройки из Django
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_url = settings.CELERY_BROKER_URL
# Автоматически находим и загружаем задачи из приложения mailings
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
    app.start()
