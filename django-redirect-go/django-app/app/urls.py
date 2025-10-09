from django.urls import path
from app import views

urlpatterns = [
    path('save', views.save),
    path('read', views.read),
    path('getlast', views.getlast),
]
