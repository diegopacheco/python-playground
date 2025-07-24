from django.urls import path
from . import views

urlpatterns = [
    path('check/<uuid:id>', views.check_id, name='check_id'),
]