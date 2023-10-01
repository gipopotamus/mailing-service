from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MailingViewSet, ClientViewSet

router = DefaultRouter()
router.register(r'mailings', MailingViewSet)
router.register(r'clients', ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]