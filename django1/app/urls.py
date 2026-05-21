from django.urls import path
from . import views, auth_views
import logging

urlpatterns = [
    # 原有视频处理相关路由
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

    # 用户认证相关路由
    path('auth/register/', auth_views.register, name='auth_register'),
    path('auth/login/', auth_views.login, name='auth_login'),
    path('auth/logout/', auth_views.logout, name='auth_logout'),
    path('auth/user_info/', auth_views.get_user_info, name='auth_user_info'),
    path('auth/update_profile/', auth_views.update_profile, name='auth_update_profile'),

    # 讲义分类管理路由
    path('categories/', auth_views.list_categories, name='list_categories'),
    path('categories/create/', auth_views.create_category, name='create_category'),
    path('categories/<int:category_id>/', auth_views.update_category, name='update_category'),
    path('categories/<int:category_id>/delete/', auth_views.delete_category, name='delete_category'),

    # 讲义存档管理路由
    path('lectures/', auth_views.list_lectures, name='list_lectures'),
    path('lectures/create/', auth_views.create_lecture, name='create_lecture'),
    path('lectures/<int:lecture_id>/', auth_views.get_lecture, name='get_lecture'),
    path('lectures/<int:lecture_id>/update/', auth_views.update_lecture, name='update_lecture'),
    path('lectures/<int:lecture_id>/delete/', auth_views.delete_lecture, name='delete_lecture'),
    path('lectures/statistics/', auth_views.get_statistics, name='get_statistics'),
]