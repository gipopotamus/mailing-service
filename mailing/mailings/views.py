from django.db.models import Count, Q, F
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Mailing, Client
from .serializers import MailingSerializer, ClientSerializer
from .tasks import send_messages
from django.utils import timezone


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    @action(detail=False, methods=['GET'])
    def statistics(self, request):
        statistics_data = Mailing.objects.annotate(
            total_messages=Count('message'),
            sent_messages=Count('message', filter=Q(message__status='sent')),
            mailing_status=F('message__status'),  # Пример: связь статуса сообщения с рассылкой
        ).values('id', 'total_messages', 'sent_messages', 'mailing_status')

        return Response(statistics_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def message_statistics(self, request, pk=None):
        mailing = get_object_or_404(Mailing, pk=pk)
        message_statistics = mailing.message_set.values('status').annotate(count=Count('id'))

        return Response(message_statistics, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        mailing = self.get_object()
        serializer = MailingSerializer(mailing, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        mailing = self.get_object()
        mailing.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'])
    def start_mailing(self, request, pk=None):
        mailing = self.get_object()
        current_time = timezone.now().astimezone(mailing.start_datetime.tzinfo)
        if mailing.start_datetime <= current_time <= mailing.end_datetime:
            send_messages.delay(mailing.pk)  # Вызывается сразу, если наступило время рассылки
            return Response({'message': 'Рассылка запущена.'}, status=status.HTTP_200_OK)
        elif current_time <= mailing.end_datetime:  # Проверка, что дата окончания не раньше текущей
            send_messages.apply_async((mailing.pk,), eta=mailing.start_datetime)
            return Response({'message': 'Рассылка запланирована на старт в будущем времени.'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Рассылка уже завершена или не может быть запущена.'},
                            status=status.HTTP_400_BAD_REQUEST)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def create(self, request):
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        client = self.get_object()
        serializer = ClientSerializer(client, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        client = self.get_object()
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
