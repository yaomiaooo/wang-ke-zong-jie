from django.db import models
from django.contrib.auth.models import User
import os


# 用户扩展信息模型
class UserProfile(models.Model):
    """用户扩展信息，用于存储额外用户数据"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    bio = models.TextField(blank=True, verbose_name='个人简介')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户扩展信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username} 的扩展信息'


# 讲义分类模型
class LectureCategory(models.Model):
    """讲义分类，用于组织和分类讲义"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_categories')
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='分类描述')
    color = models.CharField(max_length=20, default='#5c4d82', verbose_name='分类颜色')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'lecture_category'
        verbose_name = '讲义分类'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        unique_together = ['user', 'name']  # 同一用户下分类名称唯一

    def __str__(self):
        return self.name


# 讲义存档模型
class LectureArchive(models.Model):
    """讲义存档，存储用户上传视频生成的讲义"""
    STATUS_CHOICES = [
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '处理失败'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_archives')
    title = models.CharField(max_length=200, verbose_name='讲义标题')
    subject = models.CharField(max_length=100, blank=True, verbose_name='科目')
    category = models.ForeignKey(
        LectureCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lectures',
        verbose_name='所属分类'
    )
    video_file = models.FileField(upload_to='videos/', null=True, blank=True, verbose_name='原始视频')
    summary_file = models.TextField(blank=True, verbose_name='总结内容')
    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True, verbose_name='PDF文件')
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name='状态')
    processing_params = models.JSONField(default=dict, blank=True, verbose_name='处理参数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'lecture_archive'
        verbose_name = '讲义存档'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """删除时清理相关文件"""
        if self.video_file:
            if os.path.isfile(self.video_file.path):
                os.remove(self.video_file.path)
        if self.pdf_file:
            if os.path.isfile(self.pdf_file.path):
                os.remove(self.pdf_file.path)
        super().delete(*args, **kwargs)

    def get_tags_list(self):
        """获取标签列表"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def set_tags(self, tag_list):
        """设置标签"""
        self.tags = ','.join(tag_list)


# 帧图片模型
class FrameImage(models.Model):
    """帧图片，用于存储视频中提取的关键帧图片"""
    lecture = models.ForeignKey(
        LectureArchive,
        on_delete=models.CASCADE,
        related_name='frame_images',
        verbose_name='所属讲义'
    )
    frame_index = models.IntegerField(verbose_name='帧索引')
    timestamp = models.FloatField(verbose_name='时间戳(秒)')

    # 旧字段：保留，用于兼容历史数据
    # 以后新生成的图片可以不依赖这个字段
    image_file = models.ImageField(
        upload_to='frames/',
        verbose_name='帧图片',
        blank=True,
        null=True
    )

    # 新字段：真正把图片内容保存到 MySQL
    image_data = models.BinaryField(
        blank=True,
        null=True,
        verbose_name='图片二进制数据'
    )

    # 新字段：记录图片类型
    image_content_type = models.CharField(
        max_length=50,
        default='image/jpeg',
        verbose_name='图片类型'
    )

    ocr_text = models.TextField(blank=True, verbose_name='OCR识别文本')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'frame_image'
        verbose_name = '帧图片'
        verbose_name_plural = verbose_name
        ordering = ['frame_index']

    def __str__(self):
        return f'帧 {self.frame_index} - {self.timestamp:.2f}s'

    def delete(self, *args, **kwargs):
        """
        删除记录时只尝试清理旧 image_file 文件。
        image_data 存在数据库中，会随着数据库记录一起删除。
        """
        if self.image_file:
            try:
                if os.path.isfile(self.image_file.path):
                    os.remove(self.image_file.path)
            except Exception:
                pass
        super().delete(*args, **kwargs)
