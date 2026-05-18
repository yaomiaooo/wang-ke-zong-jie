from django.urls import path
from . import views

urlpatterns = [
    path('process_video', views.process_video, name='process_video'),
    path('get_progress', views.get_progress, name='get_progress'),
]