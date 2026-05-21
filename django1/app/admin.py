from django.contrib import admin
from app.models import UserProfile, LectureCategory, LectureArchive


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('created_at',)


@admin.register(LectureCategory)
class LectureCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at', 'color')


@admin.register(LectureArchive)
class LectureArchiveAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'created_at')
    search_fields = ('title', 'subject', 'tags', 'user__username')
    list_filter = ('status', 'created_at', 'category')
    readonly_fields = ('created_at', 'updated_at')
