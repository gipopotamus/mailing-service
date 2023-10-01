# mailings/tasks.py
import requests
from celery import shared_task
from django.utils import timezone
from .models import Mailing, Client, Message


@shared_task(bind=True, max_retries=3)
def send_messages(self, mailing_id):
    mailing = Mailing.objects.get(pk=mailing_id)
    clients = Client.objects.filter(
        mobile_operator_code=mailing.client_filter_mobile_operator,
        tag=mailing.client_filter_tag
    )
    for client in clients:
        try:
            response = requests.post(
                'https://probe.fbrq.cloud/send',
                json={
                    'id': client.id,
                    'phone': client.phone_number,
                    'text': mailing.message_text,
                },
                headers={'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjcyNTEwNjIsImlzcyI6ImZhYnJpcXVlIiwibmFtZSI6Imh0dHBzOi8vdC5tZS9FZ29yX3gifQ.ers_DofPcttOQ3fLvkFDqMwLxAWcsBoWxjtoWp01oz0'},
            )

            if response.status_code == 200:
                Message.objects.create(
                    status='sent',
                    mailing=mailing,
                    client=client,
                )
            else:
                self.retry()

        except Exception as e:
            Message.objects.create(
                status='error',
                mailing=mailing,
                client=client,
                error_message=str(e),
            )
