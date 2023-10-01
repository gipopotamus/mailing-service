# mailings/models.py

from django.db import models


class Client(models.Model):
    id = models.AutoField(primary_key=True)
    phone_number = models.CharField(max_length=12, unique=True, help_text="Номер телефона в формате 7XXXXXXXXXX")
    mobile_operator_code = models.CharField(max_length=5, help_text="Код мобильного оператора")
    tag = models.CharField(max_length=255, help_text="Произвольная метка")
    timezone = models.CharField(max_length=50, help_text="Часовой пояс")

    def __str__(self):
        return self.phone_number


class Mailing(models.Model):
    id = models.AutoField(primary_key=True)
    start_datetime = models.DateTimeField(help_text="Дата и время запуска рассылки")
    end_datetime = models.DateTimeField(help_text="Дата и время окончания рассылки")
    message_text = models.TextField(help_text="Текст сообщения для доставки клиенту")
    client_filter_mobile_operator = models.CharField(max_length=5, help_text="Код мобильного оператора для фильтрации клиентов")
    client_filter_tag = models.CharField(max_length=255, help_text="Тег для фильтрации клиентов")

    def __str__(self):
        return f"Рассылка {self.id}"


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    created_datetime = models.DateTimeField(auto_now_add=True, help_text="Дата и время создания сообщения")
    status = models.CharField(max_length=50, help_text="Статус отправки")
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, help_text="Рассылка, в рамках которой было отправлено сообщение")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, help_text="Клиент, которому отправили")
    error_message = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Сообщение {self.id} для {self.client.phone_number}"
