from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from app.models import UserProfile, LectureCategory, LectureArchive
from django.db.models import Q
from django.conf import settings
import json
import os


# ==================== 用户认证模块 ====================

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    用户注册接口
    请求方式: POST
    参数: username, email, password, confirm_password
    """
    try:
        data = json.loads(request.body)

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # 数据验证
        if not username or not email or not password:
            return JsonResponse({
                'success': False,
                'message': '请填写所有必填项'
            }, status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return JsonResponse({
                'success': False,
                'message': '两次输入的密码不一致'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'message': '密码长度不能少于8位'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查用户名是否存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': '用户名已存在'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查邮箱是否存在
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': '邮箱已被注册'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # 创建用户扩展信息
        UserProfile.objects.create(user=user)

        # 生成Token
        token, _ = Token.objects.get_or_create(user=user)

        return JsonResponse({
            'success': True,
            'message': '注册成功',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    用户登录接口
    请求方式: POST
    参数: username, password
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '请填写用户名和密码'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证用户
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({
                'success': False,
                'message': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return JsonResponse({
                'success': False,
                'message': '账号已被禁用'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 获取或创建Token
        token, _ = Token.objects.get_or_create(user=user)

        return JsonResponse({
            'success': True,
            'message': '登录成功',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    用户登出接口
    """
    try:
        # 删除Token
        request.user.auth_token.delete()
        return JsonResponse({
            'success': True,
            'message': '登出成功'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'登出失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """
    获取当前用户信息
    """
    try:
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'avatar': profile.avatar.url if profile.avatar else None,
                'phone': profile.phone,
                'bio': profile.bio,
                'created_at': user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    更新用户个人资料
    """
    try:
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        data = json.loads(request.body)

        # 更新用户信息
        if 'email' in data:
            user.email = data['email']
            user.save()

        # 更新扩展信息
        if 'phone' in data:
            profile.phone = data['phone']
        if 'bio' in data:
            profile.bio = data['bio']

        profile.save()

        return JsonResponse({
            'success': True,
            'message': '资料更新成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'avatar': profile.avatar.url if profile.avatar else None,
                'phone': profile.phone,
                'bio': profile.bio
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 讲义分类管理 ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    """
    获取用户的所有分类列表
    """
    try:
        categories = LectureCategory.objects.filter(user=request.user)
        data = [{
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'color': cat.color,
            'lecture_count': cat.lectures.count(),
            'created_at': cat.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for cat in categories]

        return JsonResponse({
            'success': True,
            'categories': data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取分类失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    """
    创建新的分类
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({
                'success': False,
                'message': '分类名称不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否已存在同名分类
        if LectureCategory.objects.filter(user=request.user, name=name).exists():
            return JsonResponse({
                'success': False,
                'message': '该分类已存在'
            }, status=status.HTTP_400_BAD_REQUEST)

        category = LectureCategory.objects.create(
            user=request.user,
            name=name,
            description=data.get('description', ''),
            color=data.get('color', '#5c4d82')
        )

        return JsonResponse({
            'success': True,
            'message': '分类创建成功',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'color': category.color,
                'created_at': category.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建分类失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_category(request, category_id):
    """
    更新分类信息
    """
    try:
        category = LectureCategory.objects.get(id=category_id, user=request.user)
        data = json.loads(request.body)

        if 'name' in data:
            # 检查是否与其他分类重名
            if LectureCategory.objects.filter(user=request.user, name=data['name']).exclude(id=category_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': '该分类名称已存在'
                }, status=status.HTTP_400_BAD_REQUEST)
            category.name = data['name'].strip()

        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        category.save()

        return JsonResponse({
            'success': True,
            'message': '分类更新成功',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'color': category.color
            }
        }, status=status.HTTP_200_OK)
    except LectureCategory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '分类不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新分类失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, category_id):
    """
    删除分类
    """
    try:
        category = LectureCategory.objects.get(id=category_id, user=request.user)
        category.delete()

        return JsonResponse({
            'success': True,
            'message': '分类删除成功'
        }, status=status.HTTP_200_OK)
    except LectureCategory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '分类不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'删除分类失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 讲义存档管理 ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lectures(request):
    """
    获取用户的讲义列表
    支持按分类、标签、时间筛选
    """
    try:
        # 获取查询参数
        category_id = request.GET.get('category_id')
        tag = request.GET.get('tag')
        status_filter = request.GET.get('status')
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # 构建查询
        lectures = LectureArchive.objects.filter(user=request.user)

        if category_id:
            try:
                lectures = lectures.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass

        if tag:
            lectures = lectures.filter(tags__contains=tag)

        if status_filter:
            lectures = lectures.filter(status=status_filter)

        if search:
            lectures = lectures.filter(
                Q(title__icontains=search) |
                Q(subject__icontains=search) |
                Q(tags__icontains=search)
            )

        # 分页
        total = lectures.count()
        start = (page - 1) * page_size
        end = start + page_size
        lectures = lectures[start:end]

        # 序列化
        data = [{
            'id': lecture.id,
            'title': lecture.title,
            'subject': lecture.subject,
            'category': {
                'id': lecture.category.id,
                'name': lecture.category.name,
                'color': lecture.category.color
            } if lecture.category else None,
            'status': lecture.status,
            'tags': lecture.get_tags_list(),
            'summary_preview': lecture.summary_file[:200] + '...' if len(lecture.summary_file) > 200 else lecture.summary_file,
            'has_pdf': bool(lecture.pdf_file),
            'created_at': lecture.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': lecture.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for lecture in lectures]

        return JsonResponse({
            'success': True,
            'lectures': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取讲义列表失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lecture(request, lecture_id):
    """
    获取单个讲义详情
    """
    try:
        lecture = LectureArchive.objects.get(id=lecture_id, user=request.user)

        return JsonResponse({
            'success': True,
            'lecture': {
                'id': lecture.id,
                'title': lecture.title,
                'subject': lecture.subject,
                'category': {
                    'id': lecture.category.id,
                    'name': lecture.category.name,
                    'color': lecture.category.color
                } if lecture.category else None,
                'status': lecture.status,
                'tags': lecture.get_tags_list(),
                'summary_file': lecture.summary_file,
                'pdf_url': lecture.pdf_file.url if lecture.pdf_file else None,
                'processing_params': lecture.processing_params,
                'created_at': lecture.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': lecture.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)
    except LectureArchive.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '讲义不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取讲义详情失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lecture(request):
    """
    创建新讲义记录
    """
    try:
        data = json.loads(request.body)

        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({
                'success': False,
                'message': '讲义标题不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        lecture = LectureArchive.objects.create(
            user=request.user,
            title=title,
            subject=data.get('subject', ''),
            category_id=data.get('category_id'),
            tags=data.get('tags', ''),
            status=data.get('status', 'processing'),
            processing_params=data.get('processing_params', {})
        )

        return JsonResponse({
            'success': True,
            'message': '讲义创建成功',
            'lecture': {
                'id': lecture.id,
                'title': lecture.title,
                'subject': lecture.subject,
                'status': lecture.status
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建讲义失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_lecture(request, lecture_id):
    """
    更新讲义信息
    """
    try:
        lecture = LectureArchive.objects.get(id=lecture_id, user=request.user)
        data = json.loads(request.body)

        if 'title' in data:
            lecture.title = data['title'].strip()
        if 'subject' in data:
            lecture.subject = data['subject']
        if 'category_id' in data:
            lecture.category_id = data['category_id']
        if 'tags' in data:
            if 'tags' in data:
                lecture.tags = data['tags'] if not isinstance(data['tags'], list) else lecture.set_tags(data['tags']) or lecture.tags
        if 'summary_file' in data:
            lecture.summary_file = data['summary_file']
        if 'status' in data:
            lecture.status = data['status']
        if 'processing_params' in data:
            lecture.processing_params = data['processing_params']

        lecture.save()

        return JsonResponse({
            'success': True,
            'message': '讲义更新成功',
            'lecture': {
                'id': lecture.id,
                'title': lecture.title,
                'subject': lecture.subject,
                'status': lecture.status,
                'tags': lecture.get_tags_list()
            }
        }, status=status.HTTP_200_OK)
    except LectureArchive.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '讲义不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新讲义失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_lecture_content(request, lecture_id):
    """
    保存讲义内容（用于实时保存编辑内容）
    """
    try:
        lecture = LectureArchive.objects.get(id=lecture_id, user=request.user)
        data = request.data

        # 数据验证
        content = data.get('content', '')
        title = data.get('title', '').strip()
        
        if not title:
            return JsonResponse({
                'success': False,
                'message': '讲义标题不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(title) > 200:
            return JsonResponse({
                'success': False,
                'message': '讲义标题不能超过200个字符'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(content) > 1000000:  # 限制内容大小 1MB
            return JsonResponse({
                'success': False,
                'message': '讲义内容过大，请压缩后保存'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 更新讲义内容到数据库
        lecture.title = title
        lecture.summary_file = content
        lecture.save()

        # 同时更新 md 文件（供前端 get_ocr_summary 读取）
        try:
            tempfold_dir = os.path.join(settings.BASE_DIR, 'tempfold')
            md_file_path = os.path.join(tempfold_dir, '3-ocr_summary.txt')
            os.makedirs(tempfold_dir, exist_ok=True)
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            # 文件写入失败不影响返回成功
            print(f"警告: 讲义文件写入失败: {e}")

        return JsonResponse({
            'success': True,
            'message': '讲义内容已保存',
            'lecture': {
                'id': lecture.id,
                'title': lecture.title,
                'content': lecture.summary_file,
                'updated_at': lecture.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_200_OK)
        
    except LectureArchive.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '讲义不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '数据格式错误'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lecture(request, lecture_id):
    """
    删除讲义
    """
    try:
        lecture = LectureArchive.objects.get(id=lecture_id, user=request.user)
        lecture.delete()

        return JsonResponse({
            'success': True,
            'message': '讲义删除成功'
        }, status=status.HTTP_200_OK)
    except LectureArchive.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '讲义不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'删除讲义失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_statistics(request):
    """
    获取用户讲义统计信息
    """
    try:
        total_lectures = LectureArchive.objects.filter(user=request.user).count()
        completed_lectures = LectureArchive.objects.filter(user=request.user, status='completed').count()
        processing_lectures = LectureArchive.objects.filter(user=request.user, status='processing').count()
        total_categories = LectureCategory.objects.filter(user=request.user).count()

        # 获取所有标签及使用次数
        lectures = LectureArchive.objects.filter(user=request.user, tags__isnull=False).exclude(tags='')
        tag_count = {}
        for lecture in lectures:
            for tag in lecture.get_tags_list():
                tag_count[tag] = tag_count.get(tag, 0) + 1

        top_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:10]

        return JsonResponse({
            'success': True,
            'statistics': {
                'total_lectures': total_lectures,
                'completed_lectures': completed_lectures,
                'processing_lectures': processing_lectures,
                'total_categories': total_categories,
                'top_tags': [{'tag': tag, 'count': count} for tag, count in top_tags]
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
