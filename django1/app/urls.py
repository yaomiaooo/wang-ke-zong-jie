from django.urls import path
from . import views
import logging

urlpatterns = [
    path('video_upload/', views.video_upload, name='video_upload'),
    path('execute/', views.execute, name='execute'),
    path('get_progress', views.get_progress, name='get_progress'),
    path('get_ocr_summary', views.get_ocr_summary, name='get_ocr_summary'),
    path('extract_key_frame', views.extract_key_frame, name='extract_key_frame'),
    path('auto_rectangle', views.auto_rectangle, name='auto_rectangle'),
    path('user_get_rectangles', views.user_get_rectangles, name='user_get_rectangles'),
    path('user_get_special_frame', views.user_get_special_frame, name='user_get_special_frame'),
    path('user_change_rectangles', views.user_change_rectangles, name='user_change_rectangles'),
    path('extract_frames_fast', views.extract_frames_fast, name='extract_frames_fast'),
    path('generate_pdf', views.generate_pdf, name='generate_pdf'),
    path('ai22', views.ai22, name='ai22'),
]