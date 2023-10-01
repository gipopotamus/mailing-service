import json
from celery import current_app
from celery.result import AsyncResult
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import Mailing, Client, Message


class MailingViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mailing_data = {
            'start_datetime': timezone.now(),
            'end_datetime': timezone.now() + timedelta(hours=1),
            'message_text': 'Test message',
            'client_filter_mobile_operator': '12345',
            'client_filter_tag': 'Test',
        }
        self.mailing = Mailing.objects.create(**self.mailing_data)

    def test_create_mailing(self):
        response = self.client.post('/api/mailings/', self.mailing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_start_mailing_now(self):
        response = self.client.post(f'/api/mailings/{self.mailing.id}/start_mailing/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = AsyncResult(str(self.mailing.id))
        self.assertTrue(result.status == 'PENDING')  # Проверьте статус задачи

    def test_start_mailing_future(self):
        future_start = timezone.now() + timedelta(hours=2)
        self.mailing.start_datetime = future_start
        self.mailing.save()

        response = self.client.post(f'/api/mailings/{self.mailing.id}/start_mailing/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = AsyncResult(str(self.mailing.id))
        self.assertTrue(result.status == 'PENDING')

    def test_update_mailing(self):
        updated_data = {
            'start_datetime': '2023-09-29T12:00:00Z',
            'end_datetime': '2023-09-30T12:00:00Z',
            'message_text': 'Updated message',
            'client_filter_mobile_operator': '12345',
            'client_filter_tag': 'Updated tag',
        }
        response = self.client.put(f'/api/mailings/{self.mailing.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Mailing.objects.get(id=self.mailing.id).message_text, 'Updated message')

    def test_delete_mailing(self):
        response = self.client.delete(f'/api/mailings/{self.mailing.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Mailing.objects.filter(id=self.mailing.id).exists())

    def test_statistics_all_mailings(self):
        mailing_data = {
            'start_datetime': timezone.now(),
            'end_datetime': timezone.now() + timedelta(hours=1),
            'message_text': 'Test message for statistics',
            'client_filter_mobile_operator': '12345',
            'client_filter_tag': 'Test',
        }
        Mailing.objects.create(**mailing_data)

        url = reverse('mailing-statistics')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверим, что в ответе есть информация о двух рассылках
        self.assertEqual(len(response.data), 2)
        # Проверим, что первая рассылка в ответе имеет ожидаемые данные
        self.assertEqual(response.data[0]['id'], self.mailing.id)
        self.assertEqual(response.data[0]['total_messages'], 0)
        self.assertEqual(response.data[0]['sent_messages'], 0)
        # Проверим, что вторая рассылка в ответе имеет ожидаемые данные
        self.assertEqual(response.data[1]['total_messages'], 0)
        self.assertEqual(response.data[1]['sent_messages'], 0)


class ClientViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_data = {
            "phone_number": "string",
            "mobile_operator_code": "1235",
            "tag": "Test",
            "timezone": "UTC",
        }
        self.client_obj = Client.objects.create(**self.client_data)

    def test_creates_clients(self):
        client = Client.objects.create(
            phone_number="71234567890",
            mobile_operator_code="123",
            tag="crazy",
            timezone="UTC",
        )
        self.assertIsInstance(client, Client)
        self.assertEqual(client.phone_number, "71234567890")

    def test_update_client(self):
        updated_data = {
            'phone_number': '87654321',  # Обновите телефонный номер
            'mobile_operator_code': '54321',  # Обновите код оператора
            'tag': 'Updated Test',  # Обновите тег
            'timezone': 'PST',  # Обновите часовой пояс
        }
        response = self.client.put(f'/api/clients/{self.client_obj.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Client.objects.get(id=self.client_obj.id).tag, 'Updated Test')

    def test_delete_client(self):
        response = self.client.delete(f'/api/clients/{self.client_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(id=self.client_obj.id).exists())

