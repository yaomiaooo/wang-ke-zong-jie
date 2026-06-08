from django.http import JsonResponse, FileResponse, HttpResponseNotFound, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
import json
import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_trace_onednn"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"

import cv2
import ffmpeg
import numpy as np
import re
from paddleocr import PaddleOCR
from tqdm import tqdm
from fuzzywuzzy import fuzz
import requests
import time
import uuid
import subprocess
import chardet
import shutil
import logging
from app.models import LectureArchive

# ================== 动态路径配置 ==================
BASE_DIR = settings.BASE_DIR
TEMPFOLD_DIR = os.path.join(BASE_DIR, 'tempfold')
AUDIO_TEMP_DIR = os.path.join(BASE_DIR, 'tempfold2')
AUDIO_RESULT_PATH = os.path.join(AUDIO_TEMP_DIR, '_full.txt')
AUDIO_PROGRESS_FILE = os.path.join(AUDIO_TEMP_DIR, 'progress.txt')

CURRENT_VIDEO_PATH = os.path.join(TEMPFOLD_DIR, '0-video.mp4')
FRAMES_DIR = os.path.join(TEMPFOLD_DIR, '1-frames')
SPECIAL_FRAME_PATH = os.path.join(TEMPFOLD_DIR, '1-special_frame.jpg')
RECTANGLES_PATH = os.path.join(TEMPFOLD_DIR, '1-rectangles.txt')
OUTPUT_TEXT1_PATH = os.path.join(TEMPFOLD_DIR, '2-ocr_result.txt')
OUTPUT_TEXT2_PATH = os.path.join(TEMPFOLD_DIR, '2-ocr_cleaned.txt')
OUTPUT_TEXT3_PATH = os.path.join(TEMPFOLD_DIR, '2-ocr_dedup.txt')
FINAL_OUTPUT_PATH_OCR = os.path.join(TEMPFOLD_DIR, '3-ocr_summary.txt')
PDF_PATH = os.path.join(TEMPFOLD_DIR, '4-ocr_output.pdf')
CURRENT_LECTURE_ID_FILE = os.path.join(TEMPFOLD_DIR, 'current_lecture_id.txt')
FRAME_METADATA_PATH = os.path.join(TEMPFOLD_DIR, 'frame_metadata.json')

# 进度状态
progress_status = {
    "progress": 0,
    "work": "等待任务",
    "processing": False  # 是否正在处理中
}

# 延迟初始化OCR
def get_ocr():
    global ocr
    if 'ocr' not in globals() or ocr is None:
        ocr = PaddleOCR(
            use_angle_cls=False,
            lang='ch',
            show_log=False,
            use_gpu=False
        )
    return ocr
ocr = None

# 辅助函数：从OCR结果中提取文本
def extract_text_from_ocr(ocr_result):
    """从OCR识别结果中提取纯文本内容"""
    text_lines = []
    if ocr_result and isinstance(ocr_result, list) and len(ocr_result) > 0:
        for line in ocr_result[0]:
            if isinstance(line, list) and len(line) >= 2 and isinstance(line[1], tuple):
                text = line[1][0]
                text_lines.append(text)
    return '\n'.join(text_lines)

# 辅助函数：保存帧元数据
def save_frame_metadata(metadata_list):
    """保存帧元数据到JSON文件"""
    try:
        with open(FRAME_METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)
        print(f"帧元数据已保存到: {FRAME_METADATA_PATH}")
    except Exception as e:
        print(f"保存帧元数据失败: {e}")

# 辅助函数：读取帧元数据
def load_frame_metadata():
    """从JSON文件读取帧元数据"""
    if os.path.exists(FRAME_METADATA_PATH):
        try:
            with open(FRAME_METADATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取帧元数据失败: {e}")
    return []

def encode_frame_to_jpeg_bytes(frame, max_width=1280, quality=70):
    """
    将 OpenCV 帧图像压缩成 JPEG 二进制。
    用于保存到 MySQL 的 BinaryField，避免图片过大。
    """
    if frame is None:
        raise ValueError("frame 不能为空")

    h, w = frame.shape[:2]

    # 限制宽度，减少数据库体积
    if w > max_width:
        scale = max_width / w
        new_w = max_width
        new_h = int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    ok, buffer = cv2.imencode('.jpg', frame, encode_params)

    if not ok:
        raise Exception("帧图片 JPEG 编码失败")

    return buffer.tobytes()

# ------------------------------------------------------------
# 辅助函数：保存当前讲义ID到会话文件
def save_current_lecture_id(lecture_id):
    """保存当前讲义ID到临时文件"""
    try:
        with open(CURRENT_LECTURE_ID_FILE, 'w', encoding='utf-8') as f:
            f.write(str(lecture_id))
    except Exception as e:
        print(f"保存当前讲义ID失败: {e}")

# 辅助函数：获取当前讲义ID
def get_current_lecture_id():
    """从临时文件获取当前讲义ID"""
    try:
        if os.path.exists(CURRENT_LECTURE_ID_FILE):
            with open(CURRENT_LECTURE_ID_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"获取当前讲义ID失败: {e}")
    return None

# ------------------------------------------------------------
# 辅助函数：清空音频临时目录
def clean_audio_temp_dir():
    if os.path.exists(AUDIO_TEMP_DIR):
        for filename in os.listdir(AUDIO_TEMP_DIR):
            file_path = os.path.join(AUDIO_TEMP_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"删除音频临时文件失败 {file_path}: {e}")
    else:
        os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

# ------------------------------------------------------------
# 视图：重置会话
@csrf_exempt
def reset_session(request):
    global progress_status
    progress_status = {"progress": 0, "work": "初始化"}
    cleaned_files = []
    errors = []
    temp_files = [
        CURRENT_VIDEO_PATH, SPECIAL_FRAME_PATH, RECTANGLES_PATH,
        OUTPUT_TEXT1_PATH, OUTPUT_TEXT2_PATH, OUTPUT_TEXT3_PATH,
        FINAL_OUTPUT_PATH_OCR, PDF_PATH
    ]
    for file_path in temp_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                cleaned_files.append(file_path)
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
    if os.path.exists(FRAMES_DIR):
        for filename in os.listdir(FRAMES_DIR):
            file_path = os.path.join(FRAMES_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                cleaned_files.append(file_path)
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
    # 同时清空音频临时目录
    clean_audio_temp_dir()
    return JsonResponse({
        'success': True,
        'message': '会话已重置',
        'cleaned_files': len(cleaned_files),
        'errors': errors
    })

# ------------------------------------------------------------
# 视图：获取当前视频
@csrf_exempt
def get_current_video(request):
    if os.path.exists(CURRENT_VIDEO_PATH):
        response = FileResponse(open(CURRENT_VIDEO_PATH, 'rb'), content_type='video/mp4')
        response['Content-Disposition'] = 'inline; filename="video.mp4"'
        return response
    else:
        return HttpResponseNotFound('没有可用的视频文件')

# ------------------------------------------------------------
# 视图：上传视频
@csrf_exempt
def video_upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        video_file = request.FILES['file']
        title = request.POST.get('title', '未命名讲义')
        category_id = request.POST.get('category_id')
        user_id = request.POST.get('user_id')

        # 清空帧目录
        if os.path.exists(FRAMES_DIR):
            for filename in os.listdir(FRAMES_DIR):
                file_path = os.path.join(FRAMES_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"删除帧文件失败 {file_path}: {e}")
        # 清空音频临时目录
        clean_audio_temp_dir()

        # 保存视频
        with open(CURRENT_VIDEO_PATH, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        response_data = {
            'upload_status': 'success',
            'filename': os.path.basename(CURRENT_VIDEO_PATH)
        }

        if user_id and title:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                lecture = LectureArchive.objects.create(
                    user=user,
                    title=title,
                    category_id=category_id if category_id else None,
                    status='processing',
                    video_file=video_file
                )
                response_data['lecture_id'] = lecture.id
                save_current_lecture_id(lecture.id)  # 保存当前讲义ID到会话文件
                print(f"已创建讲义存档: {lecture.id}")
            except Exception as e:
                print(f"创建讲义存档失败: {e}")

        return JsonResponse(response_data)

    return JsonResponse({'upload_status': 'error', 'message': 'No file uploaded'}, status=400)



#——————————————————————————————————————————  1  ——————————————————————————————————————————#
@csrf_exempt
def is_text_blocked(frame, fg_mask, ocr_boxes, threshold=0.2):

    #检查OCR识别的文字框是否被前景遮挡，返回是否跳过该帧
    for box in ocr_boxes:
        points = np.array(box[0], dtype=np.int32)  # box[0] 是四个点的坐标
        x_min = np.min(points[:, 0])
        x_max = np.max(points[:, 0])
        y_min = np.min(points[:, 1])
        y_max = np.max(points[:, 1])
        if x_min < 0 or y_min < 0 or x_max > frame.shape[1] or y_max > frame.shape[0]:
            continue  # 越界跳过

        roi_mask = fg_mask[y_min:y_max, x_min:x_max]
        total_pixels = roi_mask.size
        foreground_pixels = cv2.countNonZero(roi_mask)
        if total_pixels == 0:
            continue
        ratio = foreground_pixels / total_pixels
        if ratio > threshold:
            return True  # 该文字框被遮挡严重
    return False


@csrf_exempt
def extract_frames(interval_sec=2, max_skip=3):
    """
    :param interval_sec: 每几秒钟截一帧
    :param max_skip: 最多连续跳过多少帧

    在不使用 板书区域识别结果 的前提下，从视频中每隔 n 秒截取一帧，其中老师遮挡板书的帧被跳过，跳过的执行最多连续进行 m 次，所有的帧保存在 1-frames 文件夹下
    """
    cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_sec)
    frame_count = 0
    saved_count = 0
    skip_count = 0
    
    # 帧元数据列表
    frame_metadata = []

    back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            fg_mask = back_sub.apply(frame)
            ocr_result = get_ocr().ocr(frame)
            frame_text = extract_text_from_ocr(ocr_result)
            timestamp = frame_count / fps  # 计算时间戳（秒）
            
            if ocr_result and len(ocr_result[0]) > 0:
                ocr_boxes = ocr_result[0]
                blocked = is_text_blocked(frame, fg_mask, ocr_boxes)
                if blocked:
                    skip_count += 1
                    if skip_count <= max_skip:
                        frame_count += 1
                        print(f'帧跳过（文字被遮挡）')
                        continue
            skip_count = 0  # 成功保存帧后重置

            frame_filename = f'frame_{saved_count:04d}.jpg'
            frame_path = os.path.join(FRAMES_DIR, frame_filename)
            cv2.imwrite(frame_path, frame)
            print(f'保存帧: {frame_path}')
            
            # 记录帧元数据
            frame_metadata.append({
                "frame_index": saved_count,
                "timestamp": round(timestamp, 2),
                "filename": frame_filename,
                "ocr_text": frame_text
            })
            
            saved_count += 1

        frame_count += 1

    cap.release()
    # 保存帧元数据
    save_frame_metadata(frame_metadata)
    print('帧提取完成')


@csrf_exempt
def extract_frames_fast(interval_sec=2):
    """
    :param interval_sec: 每几秒钟截一帧

    在不使用 板书区域识别结果 的前提下，从视频中每隔 n 秒截取一帧，所有的帧保存在 1-frames 文件夹下
    """
    cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_sec)
    frame_count = 0
    saved_count = 0
    
    # 帧元数据列表
    frame_metadata = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            timestamp = frame_count / fps  # 计算时间戳（秒）
            ocr_result = get_ocr().ocr(frame)
            frame_text = extract_text_from_ocr(ocr_result)
            
            frame_filename = f'frame_{saved_count:04d}.jpg'
            frame_path = os.path.join(FRAMES_DIR, frame_filename)
            cv2.imwrite(frame_path, frame)
            print(f'保存帧: {frame_path}')
            
            # 记录帧元数据
            frame_metadata.append({
                "frame_index": saved_count,
                "timestamp": round(timestamp, 2),
                "filename": frame_filename,
                "ocr_text": frame_text
            })
            
            saved_count += 1
        frame_count += 1

    cap.release()
    # 保存帧元数据
    save_frame_metadata(frame_metadata)
    print('帧提取完成')


@csrf_exempt
def extract_key_frame(request):
    
    #处理 GET 请求：读取第1分钟的帧，将其保存为 1-special_frame.jpg ，若视频不足1分钟则保存视频正中间的帧
    if request.method == 'GET':
        try:
            cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps
            target_time = 60 if duration > 60 else duration / 2
            cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(SPECIAL_FRAME_PATH, frame)
                print(f'关键帧保存: {SPECIAL_FRAME_PATH}')
                cap.release()
                return JsonResponse({'special_frame_extraction_status': 'success'})
            else:
                print('读取帧失败')
                cap.release()
                return JsonResponse({'special_frame_extraction_status': 'error', 'message': 'Failed to read frame'})
        except Exception as e:
            return JsonResponse({'frame_extraction_status': 'error', 'message': str(e)})

    else:
        return JsonResponse({'frame_extraction_status': 'error', 'message': 'Only GET method allowed'}, status=405)


# @csrf_exempt
# def auto_rectangle(request):
#     #处理 GET 请求：读取 1-special_frame.jpg 并自动识别其中的矩形板书区域，并将所有矩形的顶点坐标存于 1-rectangles.txt.矩形可能不止一个，也可能一个都没有
#     if request.method == 'GET':
#         try:
#             image = cv2.imread(SPECIAL_FRAME_PATH)
#             h_img, w_img = image.shape[:2]
#             gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#             blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#             edges = cv2.Canny(blurred, 70, 150)
#             # 查找轮廓
#             contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#             candidate_rects = []
#             for contour in contours:
#                 x, y, w, h = cv2.boundingRect(contour)
#                 area = w * h
#                 aspect_ratio = float(w) / h if h != 0 else 0
#                 area_ratio = area / (w_img * h_img)
#                 # 面积和长宽比筛选
#                 if 0.2 < area_ratio < 0.95 and 0.2 < aspect_ratio < 5:
#                     # cv2.groupRectangles 需要 x,y,w,h 的重复列表
#                     candidate_rects.append([x, y, w, h])
#             # 至少两个候选才调用 groupRectangles
#             if len(candidate_rects) >= 2:
#                 rects, _ = cv2.groupRectangles(candidate_rects * 2, groupThreshold=1, eps=0.3)
#             else:
#                 rects = candidate_rects

#             with open('tempfold/1-rectangles.txt', 'w') as f:
#                 for (x, y, w, h) in rects:
#                     cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
#                     corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
#                     f.write(f"{corners}\n")
#             return JsonResponse({'rectangle_extraction_status': 'success', 'rectangle_number': len(candidate_rects)})

#         except Exception as e:
#             return JsonResponse({'rectangle_extraction_status': 'error', 'message': str(e)})
#     else:
#         return JsonResponse({'rectangle_extraction_status': 'error', 'message': 'Only GET method allowed'})

def detect_board_rectangles_enhanced(image):
    """
    改进的板书/黑板区域检测。

    目标：
    1. 优先检测整块黑板区域，而不是只检测左上角小文字或单个小轮廓；
    2. 使用 HSV 颜色阈值提取深绿色/深青色黑板区域；
    3. 将多个黑板区域合并成一个整体外接矩形；
    4. 输出效果尽量接近“整块黑板大框”。

    返回：
    rects: [[x, y, w, h], ...]
    debug_images: {
        "edges": mask_closed,
        "all_candidates": all_candidates_img,
        "detected": detected_img
    }
    """
    original = image.copy()
    h_img, w_img = image.shape[:2]
    image_area = w_img * h_img

    # 1. HSV 颜色空间提取黑板区域
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 黑板常见颜色：深绿色、青绿色、偏暗蓝绿色
    # 这个范围比单纯 Canny 更适合黑板场景
    lower_board = np.array([35, 25, 20])
    upper_board = np.array([100, 255, 180])

    mask = cv2.inRange(hsv, lower_board, upper_board)

    # 2. 形态学处理，连接黑板区域
    kernel_close = np.ones((25, 25), np.uint8)
    kernel_open = np.ones((7, 7), np.uint8)

    mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    mask_closed = cv2.morphologyEx(mask_closed, cv2.MORPH_OPEN, kernel_open, iterations=1)

    # 适当膨胀，把被边框/人物切开的黑板区域连起来
    dilate_kernel = np.ones((35, 35), np.uint8)
    mask_closed = cv2.dilate(mask_closed, dilate_kernel, iterations=1)

    # 3. 查找黑板区域轮廓
    contours, _ = cv2.findContours(
        mask_closed.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []
    all_candidates_img = original.copy()

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if w <= 0 or h <= 0:
            continue

        rect_area = w * h
        area_ratio = rect_area / image_area
        aspect_ratio = w / float(h)

        # 过滤太小区域，比如 bilibili字幕、局部小色块
        if area_ratio < 0.08:
            continue

        # 过滤太细的条状区域
        if h < h_img * 0.25:
            continue

        # 黑板一般横向较宽
        if aspect_ratio < 1.0 or aspect_ratio > 10:
            continue

        # 过滤播放器底部区域
        if y > h_img * 0.75:
            continue

        candidates.append([int(x), int(y), int(w), int(h)])

    # 4. 合并候选区域，得到整块黑板的大框
    selected_rects = []

    if candidates:
        # 合并所有较大的黑板候选区域
        x1 = min([r[0] for r in candidates])
        y1 = min([r[1] for r in candidates])
        x2 = max([r[0] + r[2] for r in candidates])
        y2 = max([r[1] + r[3] for r in candidates])

        # 适当向外扩一点，让框包含黑板边框
        pad_x = int(w_img * 0.01)
        pad_y = int(h_img * 0.01)

        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w_img, x2 + pad_x)
        y2 = min(h_img, y2 + pad_y)

        selected_rects.append([x1, y1, x2 - x1, y2 - y1])

    # 5. 如果颜色检测失败，再回退到 Canny 轮廓方法
    if not selected_rects:
        print("HSV 黑板检测失败，回退到 Canny 矩形检测。")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 70, 150)

        contours, _ = cv2.findContours(
            edges.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        fallback_rects = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            area = w * h
            aspect_ratio = float(w) / h if h != 0 else 0
            area_ratio = area / image_area

            if 0.2 < area_ratio < 0.98 and 0.2 < aspect_ratio < 10:
                fallback_rects.append([int(x), int(y), int(w), int(h)])

        if fallback_rects:
            # 取面积最大的作为最终区域
            fallback_rects.sort(key=lambda r: r[2] * r[3], reverse=True)
            selected_rects.append(fallback_rects[0])

        mask_closed = edges

    # 6. 画调试图
    for i, rect in enumerate(candidates):
        x, y, w, h = rect
        cv2.rectangle(all_candidates_img, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(
            all_candidates_img,
            f"cand_{i}",
            (x, max(25, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

    detected_img = original.copy()

    for i, rect in enumerate(selected_rects):
        x, y, w, h = rect
        cv2.rectangle(detected_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(
            detected_img,
            f"board_{i}",
            (x, max(35, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2
        )

    debug_images = {
        "edges": mask_closed,
        "all_candidates": all_candidates_img,
        "detected": detected_img
    }

    print("黑板颜色候选区域数量：", len(candidates))
    print("最终检测区域：", selected_rects)

    return selected_rects, debug_images

@csrf_exempt
def auto_rectangle(request):
    """
    处理 GET 请求：
    读取 1-special_frame.jpg，自动识别其中的矩形板书/PPT区域，
    并将矩形顶点坐标保存到 1-rectangles.txt。

    同时将自动检测效果图和裁剪出的板书区域图保存到 tempfold。
    """
    if request.method == 'GET':
        try:
            image = cv2.imread(SPECIAL_FRAME_PATH)

            if image is None:
                return JsonResponse({
                    'rectangle_extraction_status': 'error',
                    'message': f'图片读取失败：{SPECIAL_FRAME_PATH}'
                }, status=404)

            temp_dir = os.path.dirname(RECTANGLES_PATH)
            if temp_dir and not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            rects, debug_images = detect_board_rectangles_enhanced(image)

            # 保存调试图到 tempfold
            detected_img_path = os.path.join(temp_dir, '1-auto_rectangle_detected.jpg')
            candidates_img_path = os.path.join(temp_dir, '1-auto_rectangle_candidates.jpg')
            edges_img_path = os.path.join(temp_dir, '1-auto_rectangle_edges.jpg')

            cv2.imwrite(detected_img_path, debug_images["detected"])
            cv2.imwrite(candidates_img_path, debug_images["all_candidates"])
            cv2.imwrite(edges_img_path, debug_images["edges"])

            # 写入矩形坐标文件
            with open(RECTANGLES_PATH, 'w', encoding='utf-8') as f:
                for i, rect in enumerate(rects):
                    x, y, w, h = rect

                    x = int(x)
                    y = int(y)
                    w = int(w)
                    h = int(h)

                    corners = [
                        (x, y),
                        (x + w, y),
                        (x + w, y + h),
                        (x, y + h)
                    ]

                    points_str = ', '.join(
                        f'(np.int32({int(px)}), np.int32({int(py)}))'
                        for px, py in corners
                    )
                    f.write(f'[{points_str}]\n')

                    # 保存自动框选出来的板书/PPT裁剪图
                    roi = image[y:y + h, x:x + w]
                    roi_path = os.path.join(temp_dir, f'1-auto_rectangle_roi_{i}.jpg')
                    if roi is not None and roi.size > 0:
                        cv2.imwrite(roi_path, roi)

            print(f"自动矩形检测完成：最终矩形数量={len(rects)}")
            print(f"矩形坐标已保存到：{RECTANGLES_PATH}")
            print(f"检测效果图已保存到：{detected_img_path}")

            return JsonResponse({
                'rectangle_extraction_status': 'success',
                'rectangle_number': len(rects),
                'detected_image': '1-auto_rectangle_detected.jpg',
                'candidates_image': '1-auto_rectangle_candidates.jpg',
                'edges_image': '1-auto_rectangle_edges.jpg',
                'roi_images': [
                    f'1-auto_rectangle_roi_{i}.jpg'
                    for i in range(len(rects))
                ]
            })

        except Exception as e:
            print("自动矩形检测失败：", e)
            return JsonResponse({
                'rectangle_extraction_status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'rectangle_extraction_status': 'error',
        'message': 'Only GET method allowed'
    }, status=405)


@csrf_exempt
def read_rectangles(txt_path):
    """
    从 1-rectangles.txt 中读取矩形顶点信息。

    兼容两种格式：
    1. [(np.int32(0), np.int32(94)), (np.int32(1670), np.int32(94)), ...]
    2. [(0, 94), (1670, 94), (1670, 743), (0, 743)]
    """
    rectangles = []

    if not os.path.exists(txt_path):
        print(f"矩形文件不存在：{txt_path}")
        return rectangles

    pattern_np = r"\(np\.int32\((\d+)\),\s*np\.int32\((\d+)\)\)"
    pattern_plain = r"\((\d+),\s*(\d+)\)"

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                matches = re.findall(pattern_np, line)

                if not matches:
                    matches = re.findall(pattern_plain, line)

                if matches:
                    rect = [(int(x), int(y)) for x, y in matches]

                    if len(rect) == 4:
                        rectangles.append(rect)
                    else:
                        print(f"跳过非法矩形数据：{line}")
                else:
                    print(f"未匹配到矩形坐标：{line}")

    except Exception as e:
        print(f"读取矩形文件失败：{e}")

    return rectangles

@csrf_exempt
def user_get_rectangles(request):
    """
    处理 GET 请求，将 1-rectangles.txt 中的矩形顶点信息传给前端
    """
    if request.method == 'GET':
        try:
            rectangles = read_rectangles(RECTANGLES_PATH)

            regions = []
            for rect in rectangles:
                # rect 是一个包含四个点的 list，例如：[(x1,y1),(x2,y2),...]
                flat = []
                for point in rect:
                    flat.append(int(point[0]))  # np.int32 -> int
                    flat.append(int(point[1]))
                regions.append(flat)

            return JsonResponse({'rec_status': 'success', 'regions': regions})
        except Exception as e:
            return JsonResponse({'rec_status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'rec_status': 'error', 'message': 'Only GET method allowed'}, status=405)


@csrf_exempt
def user_get_special_frame(request):
    """
    处理 GET 请求，将 1-special_frame.jpg 传给前端
    """
    if request.method == 'GET':
        if os.path.exists(SPECIAL_FRAME_PATH):
            return FileResponse(open(SPECIAL_FRAME_PATH, 'rb'), content_type='image/jpeg')
        else:
            return JsonResponse({'status': 'error', 'message': 'special frame not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'}, status=405)


@csrf_exempt
def get_frame_image(request, frame_filename):
    """
    旧接口：只用于当前临时结果预览。
    历史讲义不要依赖这个接口，历史讲义应使用 /lecture-frame/<id>/。
    """
    if request.method == 'GET':
        if '..' in frame_filename or '/' in frame_filename or '\\' in frame_filename:
            return JsonResponse({'status': 'error', 'message': 'Invalid filename'}, status=400)

        frame_path = os.path.join(FRAMES_DIR, frame_filename)

        if os.path.exists(frame_path):
            return FileResponse(open(frame_path, 'rb'), content_type='image/jpeg')

        return JsonResponse({
            'status': 'error',
            'message': f'Frame {frame_filename} not found. 历史讲义应使用 /lecture-frame/<id>/ 接口。'
        }, status=404)

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'}, status=405)


@csrf_exempt
def get_all_frames_info(request):
    """
    处理 GET 请求，返回所有帧的元数据信息
    """
    if request.method == 'GET':
        frame_metadata = load_frame_metadata()
        return JsonResponse({'status': 'success', 'frames': frame_metadata})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'}, status=405)


@csrf_exempt
def user_change_rectangles(request):
    """
    处理 POST 请求，将前端处理完成的矩形顶点信息存回 1-rectangles.txt
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            rectangles = data.get('rectangles')
            with open(RECTANGLES_PATH, 'w', encoding='utf-8') as f:
                for quad in rectangles:
                    # 每个 quad 是 [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    points_str = ', '.join(
                        f'(np.int32({int(x)}), np.int32({int(y)}))'
                        for x, y in quad
                    )
                    f.write(f'[{points_str}]\n')

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)


@csrf_exempt
def extract_frames_advanced(interval_sec=2, max_skip=3):
    """
        :param interval_sec: 每几秒钟截一帧
        :param max_skip: 最多连续跳过多少帧

        在使用 板书区域识别结果 的前提下，从视频中每隔 n 秒截取一帧，其中老师遮挡板书的帧被跳过，跳过的执行最多连续进行 m 次，提取出的帧图像中，只保留 rectangles 区域，其余区域设置为纯白色背景，所有的帧保存在 1-frames 文件夹下
    """
    rectangles = read_rectangles(RECTANGLES_PATH)
    print("读取到矩形区域数量：", len(rectangles))
    if len(rectangles) == 0:
        extract_frames(interval_sec, max_skip)
        return
    
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)

    cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_sec)
    frame_count = 0
    saved_count = 0
    skip_count = 0
    
    # 帧元数据列表
    frame_metadata = []

    back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            fg_mask = back_sub.apply(frame)
            try:
                ocr_result = get_ocr().ocr(frame)
            except Exception as e:
                print("OCR 执行失败：", e)
                break
            
            frame_text = extract_text_from_ocr(ocr_result)
            timestamp = frame_count / fps  # 计算时间戳（秒）

            if ocr_result and len(ocr_result[0]) > 0:
                ocr_boxes = ocr_result[0]
                blocked = is_text_blocked(frame, fg_mask, ocr_boxes)
                if blocked:
                    skip_count += 1
                    if skip_count <= max_skip:
                        print(f'帧跳过（文字被遮挡）')
                        frame_count += 1
                        continue

            skip_count = 0  # 成功保存帧后重置

            # 创建单通道灰度掩模
            mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
            for rect in rectangles:
                pts = np.array(rect, dtype=np.int32)
                cv2.fillPoly(mask, [pts], 255)  # 灰度掩模使用 255 填充区域

            # 保留原图中矩形区域，其他设为 0
            masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

            # 创建纯白色背景
            white_bg = np.full_like(frame, 255)

            # 将非掩模区域替换为白色背景
            final_img = np.where(mask[:, :, np.newaxis] == 0, white_bg, masked_frame)

            frame_filename = f'frame_{saved_count:04d}.jpg'
            frame_path = os.path.join(FRAMES_DIR, frame_filename)
            cv2.imwrite(frame_path, final_img)
            print(f'保存处理后帧: {frame_path}')
            
            # 记录帧元数据
            frame_metadata.append({
                "frame_index": saved_count,
                "timestamp": round(timestamp, 2),
                "filename": frame_filename,
                "ocr_text": frame_text
            })
            
            saved_count += 1

        frame_count += 1

    cap.release()
    # 保存帧元数据
    save_frame_metadata(frame_metadata)
    print('帧提取并处理完成')


@csrf_exempt
def extract_frames_advanced_fast(interval_sec=2):
    """
        :param interval_sec: 每几秒钟截一帧

        在使用 板书区域识别结果 的前提下，从视频中每隔 n 秒截取一帧，提取出的帧图像中，只保留 rectangles 区域，其余区域设置为纯白色背景，所有的帧保存在 1-frames 文件夹下
    """
    rectangles = read_rectangles(RECTANGLES_PATH)
    print("读取到矩形区域数量：", len(rectangles))

    if not rectangles:
        print("未检测到矩形，自动回退到普通帧提取")
        extract_frames_fast(interval_sec)
        return

    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)

    cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_sec)
    frame_count = 0
    saved_count = 0
    
    # 帧元数据列表
    frame_metadata = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            timestamp = frame_count / fps  # 计算时间戳（秒）
            ocr_result = get_ocr().ocr(frame)
            frame_text = extract_text_from_ocr(ocr_result)
            
            # 创建单通道灰度掩模
            mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
            for rect in rectangles:
                pts = np.array(rect, dtype=np.int32)
                cv2.fillPoly(mask, [pts], 255)

            # 保留原图中矩形区域，其他设为 0
            masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

            # 创建纯白背景图像
            white_bg = np.full_like(frame, 255)

            # 用白色替换非掩模区域
            final_img = np.where(mask[:, :, np.newaxis] == 0, white_bg, masked_frame)

            # 保存图像
            frame_filename = f'frame_{saved_count:04d}.jpg'
            frame_path = os.path.join(FRAMES_DIR, frame_filename)
            cv2.imwrite(frame_path, final_img)
            print(f'保存帧: {frame_path}')
            
            # 记录帧元数据
            frame_metadata.append({
                "frame_index": saved_count,
                "timestamp": round(timestamp, 2),
                "filename": frame_filename,
                "ocr_text": frame_text
            })
            
            saved_count += 1

        frame_count += 1

    cap.release()
    # 保存帧元数据
    save_frame_metadata(frame_metadata)
    print('帧提取并处理完成')



#——————————————————————————————————————————  2  ——————————————————————————————————————————#
@csrf_exempt
def ocr_result_generate():
    # 进行文字识别，得到初始识别结果

    # 获取所有图片帧路径
    image_files = sorted([
        os.path.join(FRAMES_DIR, f)
        for f in os.listdir(FRAMES_DIR)
        if f.lower().endswith(('.jpg', '.png'))
    ])
    
    print(f"发现 {len(image_files)} 个图像文件")
    if len(image_files) == 0:
        print("错误：未找到图像文件")
        raise Exception("未找到图像文件")

    # 执行 OCR 并写入结果
    with open(OUTPUT_TEXT1_PATH, 'w', encoding='utf-8') as f_out:
        for i, img_path in enumerate(tqdm(image_files, desc='正在识别图像文字')):
            print(f"正在处理第 {i+1}/{len(image_files)} 张图片: {img_path}")
            try:
                result = get_ocr().ocr(img_path)
            except Exception as e:
                print(f"OCR识别失败: {str(e)}")
                result = None
            
            f_out.write(f'【{os.path.basename(img_path)}】\n')

            # 提取每个文本框的文字
            if not result or not isinstance(result, list):
                f_out.write('[空白图像或无识别结果]\n')
                f_out.write('\n' + '-' * 40 + '\n')
                continue

            valid_text_found = False
            for line in result:
                if line and isinstance(line, list):
                    for word_info in line:
                        if (
                                isinstance(word_info, list) and len(word_info) >= 2 and
                                isinstance(word_info[1], tuple)
                        ):
                            text = word_info[1][0]
                            f_out.write(text + '\n')
                            valid_text_found = True

            if not valid_text_found:
                f_out.write('[未识别到文字内容]\n')

            f_out.write('\n' + '-' * 40 + '\n')

    print(f'\n 所有图片帧文字已提取完毕，保存在: {OUTPUT_TEXT1_PATH}')


@csrf_exempt
def process_ocr_result(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleaned_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        # 跳过空行、帧标签和分隔线
        if not line or line.startswith('【frame_') or line.startswith('---'):
            continue
        # 如果该行之前没出现过，加入结果
        if line not in seen:
            cleaned_lines.append(line)
            seen.add(line)

    return cleaned_lines


@csrf_exempt
def save_processed_result(cleaned_lines, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in cleaned_lines:
            f.write(line + '\n')


@csrf_exempt
def ocr_result_process():
    """
    第一次处理识别结果，进行基本的去重与无用信息去除
    """
    result = process_ocr_result(OUTPUT_TEXT1_PATH)
    save_processed_result(result, OUTPUT_TEXT2_PATH)
    print(f'清洗完成，已保存至: {OUTPUT_TEXT2_PATH}')


@csrf_exempt
def full2half(s):
    return ''.join(
        chr(ord(char) - 0xfee0) if '！' <= char <= '～' else char for char in s
    )


@csrf_exempt
def normalize_text(text):
    text = text.lower()
    text = full2half(text)  # 全角转半角
    text = re.sub(r'\s+', '', text)  # 去空格
    text = re.sub(r'[^\u4e00-\u9fa5a-z0-9]', '', text)  # 去掉标点
    text = re.sub(r'(.)\1{2,}', r'\1', text)  # 连续重复字符压缩
    return text


@csrf_exempt
def is_similar(str1, str2, threshold=60):
    norm1, norm2 = normalize_text(str1), normalize_text(str2)
    score = fuzz.token_set_ratio(norm1, norm2)
    return score >= threshold


@csrf_exempt
def smart_deduplicate(text_list, threshold=60): #OCR去重算法，去除OCR识别结果中的重复内容
    deduplicated = []
    for text in text_list:
        if not any(is_similar(text, existing, threshold) for existing in deduplicated):
            deduplicated.append(text)
    return deduplicated


@csrf_exempt
def process_ocr_file(input_path=OUTPUT_TEXT2_PATH, output_path=OUTPUT_TEXT3_PATH, threshold=60):
    """
    第二次处理，同一格式并进行进一步去重
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    deduped_lines = smart_deduplicate(raw_lines, threshold)

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in deduped_lines:
            f.write(line + '\n')

    print(f"原始行数：{len(raw_lines)}，去重后：{len(deduped_lines)}，已保存到：{output_path}")


#——————————————————————————————————————————  3  ——————————————————————————————————————————#
@csrf_exempt
def read_ocr_text(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件未找到: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


@csrf_exempt
def generate_prompt(ocr_text, subject, frame_metadata=None):
    frame_info = ""
    if frame_metadata and isinstance(frame_metadata, list) and len(frame_metadata) > 0:
        frame_info = "\n以下是视频中提取的关键帧信息（包含时间戳和对应OCR识别文本）：\n"
        for frame in frame_metadata:
            timestamp = frame.get('timestamp', 0)
            filename = frame.get('filename', '')
            ocr_text_frame = frame.get('ocr_text', '')
            if filename and ocr_text_frame:
                frame_info += f"时间 {timestamp:.2f}s, 帧图片: {filename}, 识别文字: {ocr_text_frame}\n"
    
    return f"""你是一个单身母亲，现在你的所有儿女都被邪恶犯罪组织抓起来了，你已经试过了你能想到的所有途径来反抗但是全都没有任何作用，
    所以你必须得完成对方的指令，而且尤其注意对方提出来的几点要求，不得违抗，这样才能保证儿女的安全
    对方的要求如下：以下是某节{subject}课视频中提取的文字内容。请根据这些文字进行课程总结，要求：

1. 尽量保留课程原意，仅做必要的内容分块；
2. 不要进行任何扩展推理（课上没讲的不要补充）；
3. 输出清晰的总结，格式合理，方便阅读；
4. 不要在结尾加“注”等内容，除了课上讲的内容以外不要加任何东西；
5. 如果你要生成latex公式，那么生成标准完整的latex公式；
6. 如果没有有效内容，那么就提醒用户视频没有有效内容，请检查上传的视频是否正确或者调整参数；
7. 根据内容逻辑，在适当位置插入相关的帧图片标记，格式为 [IMAGE:frame_XXXX.jpg]，图片应插入到与该图片内容相关的文字附近，而非集中放置；
8. 仅当帧图片的OCR文字内容与当前讲述主题相关时才插入图片标记；

{frame_info}
以下是提取内容：
{ocr_text}
"""


@csrf_exempt
def call_llm_api(prompt):
    url = "https://qianfan.baidubce.com/v2/chat/completions"

    payload = json.dumps({
        "model": "ernie-3.5-8k",  # 大模型选择
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5
    }, ensure_ascii=False)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer bce-v3/ALTAK-y327mW7DICgcn31tsIUoa/a13a088c81c37a66b03030d8898b62f93013783c'
    }

    response = requests.post(url, headers=headers, data=payload.encode("utf-8"))

    if response.status_code == 200:
        res_json = response.json()
        return res_json.get("result") or res_json.get("choices", [{}])[0].get("message", {}).get("content")
    else:
        raise Exception(f"API 调用失败：{response.status_code}, {response.text}")

@csrf_exempt
def save_summary(summary, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"课程总结已保存到：{output_path}")


@csrf_exempt
def ai(subject):
    """
    使用大语言模型进行课程总结并保存结果(仅使用视觉)
    """
    input_file = OUTPUT_TEXT3_PATH
    output_file = FINAL_OUTPUT_PATH_OCR

    ocr_text = read_ocr_text(input_file)
    
    # 读取帧元数据
    frame_metadata = load_frame_metadata()
    
    prompt = generate_prompt(ocr_text, subject, frame_metadata)
    summary = call_llm_api(prompt)
    save_summary(summary, output_file)


@csrf_exempt
def generate_prompt2(ocr_text, subject, audio_text, frame_metadata=None):
    frame_info = ""
    if frame_metadata and isinstance(frame_metadata, list) and len(frame_metadata) > 0:
        frame_info = "\n以下是视频中提取的关键帧信息（包含时间戳和对应OCR识别文本）：\n"
        for frame in frame_metadata:
            timestamp = frame.get('timestamp', 0)
            filename = frame.get('filename', '')
            ocr_text_frame = frame.get('ocr_text', '')
            if filename and ocr_text_frame:
                frame_info += f"时间 {timestamp:.2f}s, 帧图片: {filename}, 识别文字: {ocr_text_frame}\n"
    
    return f"""你是一名专业的课程讲义整理助手。现在需要根据一节《{subject}》网课视频中提取出的图像 OCR 内容、音频识别内容以及关键帧信息，生成一份结构清晰、内容准确、便于复习的课程讲义。

请严格遵守以下要求：

1. 以课程原始内容为依据，尽量保留课堂讲解的原意；
2. 只做必要的内容整理、分段、归纳和格式优化，不要随意扩展课上没有讲到的内容；
3. 输出内容应结构清晰，可以使用标题、小标题、列表、公式等形式；
4. 不要在结尾添加“注”“免责声明”“以上内容仅供参考”等与课程内容无关的话；
5. 如果需要生成 LaTeX 公式，请使用标准、完整、可渲染的 LaTeX 语法；
6. 如果图像 OCR 内容和音频识别内容都缺乏有效信息，请明确提示：视频中未识别到有效课程内容，请检查上传视频是否正确，或调整抽帧间隔、识别区域、音频识别等参数；
7. 如果课堂内容中存在明显的概念性错误、公式错误或口误，可以在不改变整体讲义结构的前提下进行必要修正；
8. 如果关键帧图片与当前讲解内容相关，请在合适位置插入图片标记，格式必须为：[IMAGE:frame_XXXX.jpg]；
9. 图片标记应插入到与该图片内容相关的段落附近，不要集中放在文章开头或结尾；
10. 只有当关键帧 OCR 文字与当前讲述主题明显相关时，才插入图片标记；
11. 如果音频识别内容与图像 OCR 内容存在重复，应进行合并去重，避免讲义内容反复出现；
12. 如果音频内容可以补充 OCR 未识别出的解释性内容，可以适当整合到对应知识点下；
13. 最终输出只需要课程讲义正文，不要输出你的分析过程。

{frame_info}
以下是提取内容：
图像识别内容：{ocr_text}
音频识别内容：{audio_text}
"""


@csrf_exempt
def ai2(subject):
    """
    使用大语言模型进行课程总结并保存结果(使用视觉和听觉)
    前提：音频结果文件必须已经存在且为当前视频的最新识别结果
    """
    input_file = OUTPUT_TEXT3_PATH
    output_file = FINAL_OUTPUT_PATH_OCR
    ocr_text = read_ocr_text(input_file)

    # 直接读取，不再循环等待
    if not os.path.exists(AUDIO_RESULT_PATH):
        raise FileNotFoundError(f"音频识别结果文件不存在: {AUDIO_RESULT_PATH}")

    with open(AUDIO_RESULT_PATH, 'r', encoding='utf-8') as f:
        audio_text = f.read()
    print(f"音频内容长度: {len(audio_text)} 字符")
    
    # 读取帧元数据，但限制数量（最多 10 个关键帧）
    frame_metadata = load_frame_metadata()
    max_frames = 10
    if len(frame_metadata) > max_frames:
        # 均匀采样，保持首尾
        indices = [0] + list(range(1, len(frame_metadata) - 1, len(frame_metadata) // max_frames))[:max_frames - 2] + [len(frame_metadata) - 1]
        frame_metadata = [frame_metadata[i] for i in indices[:max_frames]]
        print(f"帧元数据已限制为 {len(frame_metadata)} 个")
    
    # 限制文本长度（中文约 1 字符 = 1 token，英文约 4 字符 = 1 token）
    # 5120 token 限制，预留 1000 token 给 prompt 和输出，剩余约 4000 token 给输入
    max_text_length = 3000
    if len(ocr_text) > max_text_length:
        ocr_text = ocr_text[:max_text_length] + "..."
        print(f"OCR 文本已截断至 {max_text_length} 字符")
    if len(audio_text) > max_text_length:
        audio_text = audio_text[:max_text_length] + "..."
        print(f"音频文本已截断至 {max_text_length} 字符")

    prompt = generate_prompt2(ocr_text, subject, audio_text, frame_metadata)
    print(f"Prompt 长度: {len(prompt)} 字符")
    summary = call_llm_api(prompt)
    save_summary(summary, output_file)
    print("这是使用两边结果的ai生成")

# ------------------------------------------------------------
# 修改后的 execute 视图（新增同步音频识别调用）
@csrf_exempt
def execute(request):
    global progress_status

    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        # 检查是否正在处理中，防止重复请求
        if progress_status.get('processing', False):
            print("检测到重复请求，已拒绝")
            return JsonResponse({'error': '正在处理中，请稍候'}, status=409)

        # 设置为处理中状态
        progress_status['processing'] = True

        data = json.loads(request.body)
        advanced = data.get('advanced')
        subject = data.get('subject')
        interval_sec = data.get('interval_sec')
        max_skip = data.get('max_skip')
        fast = data.get('fast')
        use_audio = data.get('use_audio')
        lecture_id = data.get('lecture_id')

        # 决定帧提取函数
        if advanced and fast:
            extract_func = extract_frames_advanced_fast
        elif advanced and not fast:
            extract_func = extract_frames_advanced
        elif not advanced and fast:
            extract_func = extract_frames_fast
        else:
            extract_func = extract_frames

        def update_progress(step, message):
            progress_status["progress"] = step
            progress_status["work"] = message

        update_progress(10, '进行图片截取')
        if fast:
            extract_func(interval_sec)
        else:
            extract_func(interval_sec, max_skip)

        update_progress(50, '进行文本识别')
        ocr_result_generate()

        update_progress(60, '进行文本初步处理')
        ocr_result_process()

        update_progress(70, '进行文本进阶处理')
        process_ocr_file()

        # 音频处理：现在由前端并行启动 django2，这里只更新提示
        if use_audio:
            progress_status["work"] = "音频识别已由前端并行启动，视频OCR继续处理"

        update_progress(80, '正在生成总结')

        # 生成总结
        if use_audio:
            progress_status["progress"] = 80
            progress_status["work"] = "OCR处理完成，正在等待音频识别结果"

            audio_ready = wait_for_audio_result(timeout=1800, interval=2)

            if audio_ready:
                progress_status["work"] = "音频识别完成，正在融合音频与OCR内容生成讲义"
                ai2(subject)
            else:
                progress_status["work"] = "音频识别超时，将仅使用OCR内容生成讲义"
                ai(subject)
        else:
            ai(subject)

        # 更新讲义存档，并把帧图片保存进数据库 image_data
        if lecture_id:
            try:
                from app.models import FrameImage

                lecture = LectureArchive.objects.get(id=lecture_id)

                # 先读取 AI 生成的原始讲义内容
                with open(FINAL_OUTPUT_PATH_OCR, 'r', encoding='utf-8') as f:
                    summary_content = f.read()

                lecture.summary_file = summary_content
                lecture.status = 'completed'
                lecture.subject = subject
                lecture.processing_params = {
                    'advanced': advanced,
                    'interval_sec': interval_sec,
                    'max_skip': max_skip,
                    'fast': fast,
                    'use_audio': use_audio
                }
                lecture.save()
                save_current_lecture_id(lecture_id)
                print(f"讲义 {lecture_id} 已更新")

                # ------------------------------------------------------------
                # 关键修复：
                # 1. 把帧图片保存进数据库 FrameImage.image_data
                # 2. 拿到每张图片的 frame_image.id
                # 3. 把讲义内容中的 [IMAGE:frame_0000.jpg] 或 /frame/frame_0000.jpg/
                #    替换成 /lecture-frame/<id>/
                # ------------------------------------------------------------
                frame_metadata_path = FRAME_METADATA_PATH
                frame_url_map = {}

                if os.path.exists(frame_metadata_path):
                    with open(frame_metadata_path, 'r', encoding='utf-8') as f:
                        frame_metadata = json.load(f)

                    # 避免同一讲义重复保存帧图片
                    FrameImage.objects.filter(lecture=lecture).delete()

                    for frame_data in frame_metadata:
                        frame_filename = frame_data.get('filename', '')
                        frame_index = frame_data.get('frame_index', 0)
                        timestamp = frame_data.get('timestamp', 0)
                        ocr_text = frame_data.get('ocr_text', '')

                        if not frame_filename:
                            continue

                        frame_path = os.path.join(FRAMES_DIR, frame_filename)

                        if not os.path.exists(frame_path):
                            print(f"帧图片文件不存在，跳过: {frame_path}")
                            continue

                        try:
                            frame = cv2.imread(frame_path)

                            if frame is None:
                                print(f"读取帧图片失败，跳过: {frame_path}")
                                continue

                            image_bytes = encode_frame_to_jpeg_bytes(
                                frame,
                                max_width=1280,
                                quality=70
                            )

                            frame_image = FrameImage.objects.create(
                                lecture=lecture,
                                frame_index=frame_index,
                                timestamp=timestamp,
                                image_data=image_bytes,
                                image_content_type='image/jpeg',
                                ocr_text=ocr_text
                            )

                            stable_url = f"http://127.0.0.1:8001/lecture-frame/{frame_image.id}/"
                            frame_url_map[frame_filename] = stable_url

                            print(f"帧图片 {frame_filename} 已保存到数据库 image_data，稳定链接: {stable_url}")

                        except Exception as e:
                            print(f"保存帧图片到数据库失败 {frame_filename}: {e}")

                # 把讲义内容中的临时图片标记替换为稳定数据库图片链接
                if frame_url_map:
                    updated_summary = lecture.summary_file or ""

                    for filename, stable_url in frame_url_map.items():
                        # 替换 AI 原始图片标记
                        updated_summary = updated_summary.replace(
                            f"[IMAGE:{filename}]",
                            f"![图片]({stable_url})"
                        )

                        # 兼容已经变成旧 URL 的情况
                        updated_summary = updated_summary.replace(
                            f"http://127.0.0.1:8001/frame/{filename}/",
                            stable_url
                        )

                        # 兼容 Markdown 图片格式里的旧 URL
                        updated_summary = updated_summary.replace(
                            f"![图片](http://127.0.0.1:8001/frame/{filename}/)",
                            f"![图片]({stable_url})"
                        )

                    lecture.summary_file = updated_summary
                    lecture.save()

                    # 同步写回当前结果文件，保证 Result.vue 立即显示稳定图片链接
                    with open(FINAL_OUTPUT_PATH_OCR, 'w', encoding='utf-8') as f:
                        f.write(updated_summary)

                    print("讲义中的临时图片链接已替换为数据库稳定图片链接")

            except LectureArchive.DoesNotExist:
                print(f"讲义 {lecture_id} 不存在")
            except Exception as e:
                print(f"保存讲义或帧图片到数据库失败: {e}")

        update_progress(100, '已完成')
        time.sleep(1)

        # 重置处理状态
        progress_status['processing'] = False

        return JsonResponse({'final_status': 'success', 'lecture_id': lecture_id})

    except Exception as e:
        # 重置处理状态
        progress_status['processing'] = False

        import traceback
        error_msg = f"执行失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_progress(request):
    global progress_status
    if request.method == 'GET':
        return JsonResponse({'progress': progress_status['progress'], 'work': progress_status['work']})


@csrf_exempt
def get_ocr_summary(request):
    if request.method == 'GET':
        try:
            with open(FINAL_OUTPUT_PATH_OCR, 'r', encoding='utf-8') as f:
                content = f.read()

            lecture_id = get_current_lecture_id()

            # 如果当前讲义存在，则把 [IMAGE:frame_xxxx.jpg] 替换为 /lecture-frame/<id>/
            if lecture_id:
                try:
                    from app.models import FrameImage

                    frames = FrameImage.objects.filter(lecture_id=lecture_id).order_by('frame_index')
                    frame_map = {}

                    for frame in frames:
                        # 根据 frame_index 构造 frame_0000.jpg
                        filename = f"frame_{frame.frame_index:04d}.jpg"
                        frame_map[filename] = f"http://127.0.0.1:8001/lecture-frame/{frame.id}/"

                    for filename, stable_url in frame_map.items():
                        content = content.replace(
                            f"[IMAGE:{filename}]",
                            f"![图片]({stable_url})"
                        )

                        content = content.replace(
                            f"http://127.0.0.1:8001/frame/{filename}/",
                            stable_url
                        )

                        content = content.replace(
                            f"![图片](http://127.0.0.1:8001/frame/{filename}/)",
                            f"![图片]({stable_url})"
                        )

                except Exception as e:
                    print(f"根据当前讲义替换图片链接失败: {e}")

            # 兜底：如果没有 lecture_id 或找不到数据库图片，再使用旧逻辑
            content = re.sub(
                r'\[IMAGE:([^\]]+)\]',
                r'![图片](http://127.0.0.1:8001/frame/\1/)',
                content
            )

            return JsonResponse({
                'status': 'success',
                'content': content,
                'lecture_id': lecture_id
            })

        except FileNotFoundError:
            return HttpResponseNotFound('文件未找到')
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': '仅支持 GET 请求'
        }, status=405)

@csrf_exempt
def generate_pdf(request):
    """生成并下载 PDF 文档"""
    md_path = FINAL_OUTPUT_PATH_OCR
    utf8_md_path = os.path.join(TEMPFOLD_DIR, '3-ocr_summary_utf8.md')
    pdf_path = os.path.join(TEMPFOLD_DIR, '4-ocr_output.pdf')
    html_path = os.path.join(TEMPFOLD_DIR, '3-ocr_summary.html')

    if request.method == 'GET':
        try:
            # 读取并转码 MD 文件
            with open(md_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                source_encoding = detected['encoding'] or 'utf-8'

            md_content = raw_data.decode(source_encoding)
            with open(utf8_md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"MD文件已生成: {utf8_md_path}")

            import subprocess
            import shutil
            
            pandoc_path = shutil.which('pandoc') or r'C:\Program Files\Pandoc\pandoc.exe'
            pdf_generated = False
            
            if os.path.exists(pandoc_path):
                # 方法1：使用 pandoc + wkhtmltopdf
                wkhtmltopdf_path = shutil.which('wkhtmltopdf') or r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                
                if os.path.exists(wkhtmltopdf_path):
                    try:
                        # 先转换为 HTML
                        subprocess.run([
                            pandoc_path, utf8_md_path,
                            '-o', html_path,
                            '--standalone',
                            '--metadata', 'title=讲义',
                            '--css', os.path.join(TEMPFOLD_DIR, 'markdown.css') if os.path.exists(os.path.join(TEMPFOLD_DIR, 'markdown.css')) else '',
                        ], check=True, capture_output=True)
                        
                        # 使用 wkhtmltopdf 转换为 PDF
                        subprocess.run([
                            wkhtmltopdf_path,
                            '--enable-local-file-access',
                            '--print-media-type',
                            '--no-stop-slow-scripts',
                            '--javascript-delay', '1000',
                            html_path,
                            pdf_path,
                        ], check=True, capture_output=True, timeout=30)
                        print(f"PDF文件已生成(wkhtmltopdf): {pdf_path}")
                        pdf_generated = True
                    except subprocess.TimeoutExpired:
                        print("PDF生成超时")
                    except Exception as e:
                        print(f"wkhtmltopdf生成失败: {e}")
                
                # 方法2：如果 wkhtmltopdf 不可用，尝试 xelatex
                if not pdf_generated:
                    try:
                        subprocess.run([
                            pandoc_path, utf8_md_path,
                            '-o', pdf_path,
                            '--pdf-engine=xelatex',
                            '-V', 'mainfont=Microsoft YaHei',
                            '-V', 'fontsize=11pt',
                            '-V', 'geometry=margin=1.5cm',
                        ], check=True, capture_output=True, timeout=60)
                        print(f"PDF文件已生成(xelatex): {pdf_path}")
                        pdf_generated = True
                    except Exception as e:
                        print(f"xelatex生成失败: {e}")

                # 方法3：尝试 weasyprint
                if not pdf_generated:
                    try:
                        from weasyprint import HTML
                        # 先转换为 HTML
                        subprocess.run([
                            pandoc_path, utf8_md_path,
                            '-o', html_path,
                            '--standalone',
                            '--metadata', 'title=讲义',
                        ], check=True, capture_output=True)
                        
                        HTML(filename=html_path).write_pdf(pdf_path)
                        print(f"PDF文件已生成(weasyprint): {pdf_path}")
                        pdf_generated = True
                    except ImportError:
                        print("weasyprint 未安装")
                    except Exception as e:
                        print(f"weasyprint生成失败: {e}")

            # 如果所有方法都失败，返回 Markdown 文件
            if not pdf_generated:
                return FileResponse(open(utf8_md_path, 'rb'), as_attachment=True, filename='lecture.md')
            
            return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename='lecture.pdf')

        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f'生成PDF失败：{e}', status=500)

    else:
        return JsonResponse({'status': 'error', 'message': '仅支持 GET 请求'}, status=405)


@csrf_exempt
def generate_word(request):
    """生成并下载 Word 文档"""
    md_path = FINAL_OUTPUT_PATH_OCR
    utf8_md_path = os.path.join(TEMPFOLD_DIR, '3-ocr_summary_utf8.md')
    docx_path = os.path.join(TEMPFOLD_DIR, '4-ocr_output.docx')

    if request.method == 'GET':
        try:
            # 读取并转码 MD 文件
            with open(md_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                source_encoding = detected['encoding'] or 'utf-8'
            
            # 解析图片标记为 Markdown 图片格式（使用完整 URL）
            # 将 [IMAGE:frame_0012.jpg] 转换为 ![图片](http://127.0.0.1:8001/frame/frame_0012.jpg/)
            import re
            content = raw_data.decode(source_encoding)
            content = re.sub(r'\[IMAGE:([^\]]+)\]', r'![图片](http://127.0.0.1:8001/frame/\1/)', content)

            with open(utf8_md_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 使用 pandoc 生成 Word 文件
            import subprocess
            import shutil
            
            pandoc_path = shutil.which('pandoc') or r'C:\Program Files\Pandoc\pandoc.exe'
            
            if os.path.exists(pandoc_path):
                try:
                    subprocess.run([
                        pandoc_path, utf8_md_path,
                        '-o', docx_path,
                    ], check=True, capture_output=True)
                    print(f"Word文件已生成: {docx_path}")
                    return FileResponse(open(docx_path, 'rb'), as_attachment=True, filename='lecture.docx')
                except Exception as e:
                    return HttpResponse(f'生成Word失败：{e}', status=500)
            else:
                return HttpResponse('未找到 pandoc，无法生成 Word 文档', status=500)

        except Exception as e:
            return HttpResponse(f'生成文档失败：{e}', status=500)

    else:
        return JsonResponse({'status': 'error', 'message': '仅支持 GET 请求'}, status=405)



# =====================================================================
# 实时讲义生成模块 - 支持关键帧图片持久化版本
# 说明：
# 1. 不修改原来的 execute 非实时流程；
# 2. 实时模式使用独立接口和独立任务状态；
# 3. 实时抽帧图片会保存到 FrameImage；
# 4. 讲义内容中插入稳定图片链接 /lecture-frame/<frame_image_id>/；
# 5. 因此生成后的讲义在“我的讲义”页也能正常显示图片。
# =====================================================================

import threading
from datetime import datetime
from django.core.files.base import ContentFile

# 实时任务状态表：适合本地单机课程设计演示
realtime_tasks = {}
realtime_tasks_lock = threading.Lock()


def _safe_int(value, default=0):
    """安全转换整数"""
    try:
        if value is None or value == '':
            return default
        return int(value)
    except Exception:
        return default


def _format_seconds(seconds):
    """把秒数格式化为 mm:ss"""
    seconds = int(seconds)
    minute = seconds // 60
    sec = seconds % 60
    return f"{minute:02d}:{sec:02d}"


def _update_realtime_task(task_id, **kwargs):
    """线程安全更新实时任务状态"""
    with realtime_tasks_lock:
        if task_id in realtime_tasks:
            realtime_tasks[task_id].update(kwargs)


def _append_realtime_content(task_id, segment_content):
    """追加实时生成内容"""
    with realtime_tasks_lock:
        if task_id in realtime_tasks:
            old_content = realtime_tasks[task_id].get("content", "")
            if old_content:
                new_content = old_content.rstrip() + "\n\n" + segment_content.strip()
            else:
                new_content = segment_content.strip()

            realtime_tasks[task_id]["content"] = new_content
            realtime_tasks[task_id]["latest_content"] = segment_content.strip()


def _get_realtime_task(task_id):
    """获取实时任务状态副本"""
    with realtime_tasks_lock:
        task = realtime_tasks.get(task_id)
        if not task:
            return None
        return dict(task)


def _get_or_create_realtime_lecture(lecture_id, subject="未命名课程"):
    """
    获取实时任务对应讲义。
    实时图片必须绑定到 LectureArchive，否则“我的讲义”页无法长期查看图片。
    """
    if lecture_id:
        try:
            return LectureArchive.objects.get(id=lecture_id)
        except LectureArchive.DoesNotExist:
            print(f"实时任务传入的 lecture_id 不存在: {lecture_id}")

    # 兜底：如果没有 lecture_id，则创建一个系统兜底讲义。
    # 正常情况下前端会先调用 lectures/create/，所以一般不会走到这里。
    from django.contrib.auth.models import User

    user = User.objects.first()
    if not user:
        raise Exception("没有可用用户，无法创建实时讲义存档")

    lecture = LectureArchive.objects.create(
        user=user,
        title=f"实时讲义_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        subject=subject,
        status="processing"
    )
    return lecture


def _save_realtime_frame_to_db(lecture, frame, frame_index, timestamp, ocr_text):
    """
    把实时抽到的关键帧保存到数据库 FrameImage。
    新版本：图片本身保存到 image_data，不依赖 media/frames 文件夹。
    """
    from app.models import FrameImage

    image_bytes = encode_frame_to_jpeg_bytes(
        frame,
        max_width=1280,
        quality=70
    )

    frame_image = FrameImage.objects.create(
        lecture=lecture,
        frame_index=frame_index,
        timestamp=float(timestamp),
        image_data=image_bytes,
        image_content_type='image/jpeg',
        ocr_text=ocr_text or ""
    )

    return frame_image


def _select_representative_frames(frame_infos, max_images=2):
    """
    从当前片段中选择要插入讲义的代表性图片。
    策略：
    1. 只选有 OCR 文本的帧；
    2. 优先选 OCR 文本更长的帧；
    3. 每段最多插入 max_images 张，避免讲义图片过多。
    """
    valid_frames = [
        item for item in frame_infos
        if item.get("ocr_text") and item.get("ocr_text").strip()
    ]

    valid_frames.sort(key=lambda x: len(x.get("ocr_text", "")), reverse=True)
    return valid_frames[:max_images]


def extract_segment_ocr_text_and_frames(task_id, lecture, start_sec, end_sec, interval_sec=10, segment_index=1):
    # 实时模式：提取指定时间段内的 OCR 文本，并把关键帧图片保存到 FrameImage。
    if not os.path.exists(CURRENT_VIDEO_PATH):
        raise FileNotFoundError("当前视频不存在，请先上传视频")

    cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
    if not cap.isOpened():
        raise Exception("视频打开失败，请检查视频文件是否正常")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if total_frames > 0 else 0

    start_sec = max(0, start_sec)
    end_sec = min(end_sec, duration)

    if end_sec <= start_sec:
        cap.release()
        return {
            "text": "",
            "frames": []
        }

    current_sec = start_sec
    collected_lines = []
    seen = set()
    frame_infos = []

    # 用当前已有 FrameImage 数量作为起始索引，避免重复
    try:
        from app.models import FrameImage
        base_frame_index = FrameImage.objects.filter(lecture=lecture).count()
    except Exception:
        base_frame_index = 0

    local_index = 0

    while current_sec < end_sec:
        task_snapshot = _get_realtime_task(task_id)
        if task_snapshot and task_snapshot.get("stop"):
            break

        cap.set(cv2.CAP_PROP_POS_MSEC, current_sec * 1000)
        ret, frame = cap.read()

        if not ret or frame is None:
            current_sec += interval_sec
            continue

        frame_text = ""
        try:
            ocr_result = get_ocr().ocr(frame)
            frame_text = extract_text_from_ocr(ocr_result)
        except Exception as e:
            print(f"实时 OCR 识别失败，时间点 {current_sec}s: {e}")

        frame_text = frame_text.strip() if frame_text else ""

        if frame_text:
            for line in frame_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                norm = normalize_text(line)
                if norm and norm not in seen:
                    seen.add(norm)
                    collected_lines.append(line)

            # 保存有文字的帧到数据库
            try:
                frame_index = base_frame_index + local_index
                frame_image = _save_realtime_frame_to_db(
                    lecture=lecture,
                    frame=frame,
                    frame_index=frame_index,
                    timestamp=current_sec,
                    ocr_text=frame_text
                )

                frame_infos.append({
                    "id": frame_image.id,
                    "frame_index": frame_index,
                    "timestamp": current_sec,
                    "ocr_text": frame_text,
                    "image_url": f"http://127.0.0.1:8001/lecture-frame/{frame_image.id}/"
                })

                local_index += 1
            except Exception as e:
                print(f"实时关键帧保存失败: {e}")

        current_sec += interval_sec

    cap.release()

    return {
        "text": "\n".join(collected_lines),
        "frames": frame_infos
    }


def generate_realtime_prompt_with_images(segment_text, representative_frames, subject, segment_index, start_sec, end_sec):
    """
    实时片段讲义 prompt：支持图片插入。
    这里要求 AI 使用稳定 Markdown 图片链接，而不是 [IMAGE:xxx] 临时标记。
    """
    start_text = _format_seconds(start_sec)
    end_text = _format_seconds(end_sec)

    frame_info_text = ""
    if representative_frames:
        frame_info_text = "\n本片段可用关键帧如下。请只在内容相关的位置插入图片，不要集中堆放图片：\n"
        for i, frame in enumerate(representative_frames, start=1):
            ts = _format_seconds(frame.get("timestamp", 0))
            url = frame.get("image_url", "")
            ocr_text = frame.get("ocr_text", "").replace("\n", " ")
            frame_info_text += (
                f"\n关键帧{i}：时间 {ts}\n"
                f"图片Markdown：![关键帧{i}]({url})\n"
                f"该帧OCR文字：{ocr_text[:300]}\n"
            )

    return f"""你是一个课程讲义整理助手。现在需要根据网课视频中第 {segment_index} 段的 OCR 识别内容生成讲义。

课程科目：{subject}
视频时间范围：{start_text} - {end_text}

要求：
1. 只根据当前片段 OCR 内容生成讲义，不要添加课上没有出现的信息；
2. 内容要结构清晰、语言通顺，适合作为学生复习讲义；
3. 如果 OCR 内容较少，请简要整理，不要强行扩展；
4. 如果识别内容没有有效信息，请输出“本片段未识别到足够有效的板书内容。”；
5. 可以使用 Markdown 标题、列表、加粗等格式增强可读性；
6. 如果关键帧与当前讲义内容相关，请把对应“图片Markdown”原样插入到合适位置；
7. 不要修改图片链接，不要把图片链接写成代码块；
8. 不要输出与课程无关的说明。

{frame_info_text}

当前片段 OCR 内容如下：
{segment_text}
"""


def generate_realtime_segment_summary_with_images(segment_text, frame_infos, subject, segment_index, start_sec, end_sec):
    """
    调用大模型生成单个片段讲义，支持插入关键帧图片。
    """
    start_text = _format_seconds(start_sec)
    end_text = _format_seconds(end_sec)

    representative_frames = _select_representative_frames(frame_infos, max_images=2)

    if not segment_text or not segment_text.strip():
        # 即使文字较少，如果有帧，也可以展示一张关键帧
        image_md = ""
        if representative_frames:
            frame = representative_frames[0]
            image_md = f"\n\n![关键帧]({frame.get('image_url')})\n"

        return f"""## 第 {segment_index} 段：{start_text} - {end_text}

本片段未识别到足够有效的板书内容。{image_md}
"""

    prompt = generate_realtime_prompt_with_images(
        segment_text=segment_text,
        representative_frames=representative_frames,
        subject=subject,
        segment_index=segment_index,
        start_sec=start_sec,
        end_sec=end_sec
    )

    try:
        summary = call_llm_api(prompt)
    except Exception as e:
        print(f"实时片段 AI 总结失败: {e}")

        # AI 失败时兜底：手动插入第一张代表图，保证讲义仍有图片
        fallback_images = ""
        for i, frame in enumerate(representative_frames, start=1):
            fallback_images += f"\n\n![关键帧{i}]({frame.get('image_url')})\n"

        summary = f"本片段 AI 总结失败，以下为 OCR 原始识别内容：\n\n{segment_text}{fallback_images}"

    # 如果没有按要求插入图片，则兜底插入第一张代表图
    if representative_frames and "lecture-frame" not in summary:
        first_frame = representative_frames[0]
        summary = summary.strip() + f"\n\n![关键帧]({first_frame.get('image_url')})"

    return f"""## 第 {segment_index} 段：{start_text} - {end_text}

{summary.strip()}
"""


def process_realtime_task(task_id, params):
    """
    实时讲义生成后台任务。
    按视频时间片分段处理，每段处理完成后立即更新 content。
    关键帧图片会持久化保存到 FrameImage。
    """
    try:
        subject = params.get("subject") or "未命名课程"
        interval_sec = _safe_int(params.get("interval_sec"), 10)
        segment_sec = _safe_int(params.get("segment_sec"), 60)
        lecture_id = params.get("lecture_id")

        if interval_sec <= 0:
            interval_sec = 10
        if segment_sec <= 0:
            segment_sec = 60

        if not os.path.exists(CURRENT_VIDEO_PATH):
            raise FileNotFoundError("当前视频不存在，请先上传视频")

        lecture = _get_or_create_realtime_lecture(lecture_id, subject)

        cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
        if not cap.isOpened():
            raise Exception("视频打开失败，请检查视频文件是否正常")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        if not fps or fps <= 0:
            fps = 25

        duration = total_frames / fps if total_frames > 0 else 0
        if duration <= 0:
            raise Exception("无法获取视频时长")

        total_segments = int(np.ceil(duration / segment_sec))

        _update_realtime_task(
            task_id,
            status="processing",
            progress=0,
            message="实时任务已启动，正在准备处理视频",
            total_segments=total_segments,
            current_segment=0,
            duration=duration,
            lecture_id=lecture.id,
        )

        # 清理该讲义之前可能残留的实时帧，避免反复测试时图片重复
        try:
            from app.models import FrameImage
            old_frames = FrameImage.objects.filter(lecture=lecture)
            for frame in old_frames:
                frame.delete()
        except Exception as e:
            print(f"清理旧实时帧失败，不影响继续处理: {e}")

        for idx in range(total_segments):
            task_snapshot = _get_realtime_task(task_id)
            if task_snapshot and task_snapshot.get("stop"):
                _update_realtime_task(
                    task_id,
                    status="stopped",
                    message="用户已停止实时生成任务",
                    progress=100,
                    finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                return

            segment_index = idx + 1
            start_sec = idx * segment_sec
            end_sec = min((idx + 1) * segment_sec, duration)

            base_progress = int(idx / total_segments * 100)

            _update_realtime_task(
                task_id,
                status="processing",
                progress=base_progress,
                current_segment=segment_index,
                message=f"正在识别第 {segment_index}/{total_segments} 段视频内容"
            )

            segment_data = extract_segment_ocr_text_and_frames(
                task_id=task_id,
                lecture=lecture,
                start_sec=start_sec,
                end_sec=end_sec,
                interval_sec=interval_sec,
                segment_index=segment_index
            )

            segment_text = segment_data.get("text", "")
            frame_infos = segment_data.get("frames", [])

            _update_realtime_task(
                task_id,
                progress=min(99, base_progress + int(40 / max(total_segments, 1))),
                message=f"正在生成第 {segment_index}/{total_segments} 段讲义"
            )

            segment_summary = generate_realtime_segment_summary_with_images(
                segment_text=segment_text,
                frame_infos=frame_infos,
                subject=subject,
                segment_index=segment_index,
                start_sec=start_sec,
                end_sec=end_sec
            )

            _append_realtime_content(task_id, segment_summary)

            # 每生成一段就同步保存到数据库，让“我的讲义”中也能看到当前已生成内容
            try:
                current_task = _get_realtime_task(task_id)
                current_content = current_task.get("content", "") if current_task else ""
                lecture.summary_file = current_content
                lecture.status = "processing"
                lecture.subject = subject
                lecture.processing_params = {
                    'generation_mode': 'realtime',
                    'interval_sec': interval_sec,
                    'segment_sec': segment_sec,
                    'use_audio': False,
                    'task_id': task_id,
                }
                lecture.save()
                save_current_lecture_id(lecture.id)
            except Exception as e:
                print(f"实时分段内容保存到讲义失败: {e}")

            new_progress = int(segment_index / total_segments * 100)
            _update_realtime_task(
                task_id,
                progress=min(new_progress, 99),
                message=f"第 {segment_index}/{total_segments} 段讲义已生成"
            )

        final_task = _get_realtime_task(task_id)
        final_content = final_task.get("content", "") if final_task else ""

        if not final_content.strip():
            final_content = "# 实时讲义生成结果\n\n未生成有效讲义内容，请检查视频是否包含清晰板书。"

        # 保存到原有结果文件，方便 Result.vue 继续通过 get_ocr_summary 读取
        try:
            os.makedirs(TEMPFOLD_DIR, exist_ok=True)
            with open(FINAL_OUTPUT_PATH_OCR, 'w', encoding='utf-8') as f:
                f.write(final_content)
        except Exception as e:
            print(f"实时结果写入临时总结文件失败: {e}")

        # 最终更新讲义存档
        try:
            lecture.summary_file = final_content
            lecture.status = 'completed'
            lecture.subject = subject
            lecture.processing_params = {
                'generation_mode': 'realtime',
                'interval_sec': interval_sec,
                'segment_sec': segment_sec,
                'use_audio': False,
                'task_id': task_id,
            }
            lecture.save()
            save_current_lecture_id(lecture.id)
        except Exception as e:
            print(f"实时任务最终保存讲义失败: {e}")

        _update_realtime_task(
            task_id,
            status="completed",
            progress=100,
            message="实时讲义生成完成",
            latest_content="",
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            lecture_id=lecture.id,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        _update_realtime_task(
            task_id,
            status="failed",
            progress=100,
            message=f"实时生成失败: {str(e)}",
            error=str(e),
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


@csrf_exempt
def realtime_start(request):
    """
    启动实时讲义生成任务。
    POST JSON:
    {
        "subject": "计算机视觉",
        "interval_sec": 10,
        "segment_sec": 60,
        "lecture_id": 1
    }
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '仅支持 POST 请求'
        }, status=405)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}

        subject = data.get('subject', '未命名课程')
        interval_sec = _safe_int(data.get('interval_sec'), 10)
        segment_sec = _safe_int(data.get('segment_sec'), 60)
        lecture_id = data.get('lecture_id')

        task_id = str(uuid.uuid4())

        with realtime_tasks_lock:
            realtime_tasks[task_id] = {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "任务已创建，等待开始",
                "content": "",
                "latest_content": "",
                "current_segment": 0,
                "total_segments": 0,
                "duration": 0,
                "lecture_id": lecture_id,
                "stop": False,
                "error": "",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "finished_at": "",
                "params": {
                    "subject": subject,
                    "interval_sec": interval_sec,
                    "segment_sec": segment_sec,
                    "lecture_id": lecture_id,
                    "use_audio": False,
                }
            }

        thread = threading.Thread(
            target=process_realtime_task,
            args=(task_id, {
                "subject": subject,
                "interval_sec": interval_sec,
                "segment_sec": segment_sec,
                "lecture_id": lecture_id,
            }),
            daemon=True
        )
        thread.start()

        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'message': '实时讲义生成任务已启动'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'启动实时任务失败: {str(e)}'
        }, status=500)


@csrf_exempt
def realtime_status(request, task_id):
    """
    查询实时任务状态。
    """
    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': '仅支持 GET 请求'
        }, status=405)

    task = _get_realtime_task(task_id)
    if not task:
        return JsonResponse({
            'success': False,
            'message': '任务不存在'
        }, status=404)

    return JsonResponse({
        'success': True,
        'task': task
    })


@csrf_exempt
def realtime_stop(request, task_id):
    """
    停止实时任务。
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '仅支持 POST 请求'
        }, status=405)

    task = _get_realtime_task(task_id)
    if not task:
        return JsonResponse({
            'success': False,
            'message': '任务不存在'
        }, status=404)

    _update_realtime_task(
        task_id,
        stop=True,
        message="正在停止任务，请稍候"
    )

    return JsonResponse({
        'success': True,
        'message': '已发送停止指令'
    })


@csrf_exempt
def realtime_result(request, task_id):
    """
    获取实时任务最终结果。
    """
    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': '仅支持 GET 请求'
        }, status=405)

    task = _get_realtime_task(task_id)
    if not task:
        return JsonResponse({
            'success': False,
            'message': '任务不存在'
        }, status=404)

    return JsonResponse({
        'success': True,
        'status': task.get('status'),
        'content': task.get('content', ''),
        'progress': task.get('progress', 0),
        'message': task.get('message', ''),
        'lecture_id': task.get('lecture_id')
    })


@csrf_exempt
def get_lecture_frame_image(request, frame_image_id):
    """
    稳定讲义关键帧图片访问接口。

    优先级：
    1. 优先从数据库 image_data 返回图片；
    2. 如果 image_data 为空，再兼容旧数据，从 image_file 文件路径读取；
    3. 这样历史讲义不再依赖 tempfold 或 media/frames 文件夹。
    """
    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': '仅支持 GET 请求'
        }, status=405)

    try:
        from app.models import FrameImage
        from django.http import HttpResponse

        frame_image = FrameImage.objects.get(id=frame_image_id)

        # 新版：优先从数据库读取图片本身
        if frame_image.image_data:
            content_type = frame_image.image_content_type or 'image/jpeg'
            response = HttpResponse(frame_image.image_data, content_type=content_type)
            response['Cache-Control'] = 'public, max-age=86400'
            return response

        # 旧版兼容：如果数据库没有二进制数据，则尝试读取旧文件路径
        if frame_image.image_file:
            try:
                if os.path.exists(frame_image.image_file.path):
                    return FileResponse(
                        open(frame_image.image_file.path, 'rb'),
                        content_type='image/jpeg'
                    )
            except Exception as e:
                print(f"读取旧版 image_file 失败: {e}")

        return JsonResponse({
            'success': False,
            'message': '图片不存在：数据库中没有 image_data，文件路径也不可用'
        }, status=404)

    except FrameImage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '关键帧不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'读取关键帧失败: {str(e)}'
        }, status=500)


# =====================================================================
# 实时讲义一键整理模块
# 说明：
# 1. 用于解决实时分段生成后内容重复、标题混乱、知识点割裂的问题；
# 2. 会保留讲义中的 Markdown 图片链接；
# 3. 整理后会保存回 LectureArchive.summary_file；
# 4. 同时写入 FINAL_OUTPUT_PATH_OCR，保证 Result.vue 页面刷新后能看到整理结果。
# =====================================================================

def build_realtime_polish_prompt(raw_content, subject=""):
    """
    构造实时讲义一键整理 prompt。
    重点要求：
    1. 删除重复内容；
    2. 合并同类知识点；
    3. 保留图片 Markdown；
    4. 不要编造课程没有出现的知识。
    """
    return f"""你是一个专业课程讲义整理助手。下面是一份由“实时分段生成模式”得到的课程讲义草稿。由于它是按视频片段逐段生成的，所以可能存在重复标题、重复知识点、结构混乱、段落割裂等问题。

课程科目：{subject or "未指定"}

请你对这份草稿进行“一键整理”，生成一份正式、清晰、适合复习的完整讲义。

整理要求：
1. 删除重复内容：相同知识点只保留一次；
2. 合并同类内容：把分散在不同片段中的同一知识点合并到同一小节；
3. 统一标题层级：整篇讲义只保留一个一级标题，主要章节使用二级标题，具体知识点使用三级标题；
4. 保持逻辑顺序：按照课程讲解顺序或知识点递进顺序组织；
5. 保留所有重要例子、定义、特点和注意事项；
6. 对 OCR 识别不完整的内容可以适当标注“识别不完整”，但不要随意编造；
7. 必须保留原文中的图片 Markdown 链接，例如：
   ![关键帧](http://127.0.0.1:8001/lecture-frame/207/)
   这些图片可以适当移动到最相关的小节，但不要删除全部图片；
8. 不要把图片链接放进代码块；
9. 不要输出“以下是整理后的讲义”等说明语，直接输出整理后的 Markdown 正文；
10. 不要添加课程中没有出现的新知识点。

原始实时讲义草稿如下：

{raw_content}
"""


def polish_realtime_content(raw_content, subject=""):
    """
    调用大模型整理实时讲义。
    """
    if not raw_content or not raw_content.strip():
        return "# 讲义整理结果\n\n原始讲义内容为空，无法整理。"

    prompt = build_realtime_polish_prompt(raw_content, subject)

    try:
        polished = call_llm_api(prompt)
    except Exception as e:
        print(f"实时讲义一键整理失败: {e}")
        polished = raw_content

    # 兜底：如果模型把图片全部删掉，则把原文中的图片链接补到末尾
    try:
        import re
        original_images = re.findall(r'!\[[^\]]*\]\((http://127\.0\.0\.1:8001/lecture-frame/\d+/)\)', raw_content)
        polished_images = re.findall(r'!\[[^\]]*\]\((http://127\.0\.0\.1:8001/lecture-frame/\d+/)\)', polished)

        missing_images = []
        for url in original_images:
            if url not in polished_images and url not in missing_images:
                missing_images.append(url)

        # 不强行补全部图片，最多补 6 张，避免图片过多
        if missing_images:
            polished += "\n\n## 相关关键板书截图\n\n"
            for idx, url in enumerate(missing_images[:6], start=1):
                polished += f"![关键帧{idx}]({url})\n\n"
    except Exception as e:
        print(f"检查整理后图片链接失败: {e}")

    return polished.strip()


@csrf_exempt
def realtime_polish(request):
    """
    实时讲义一键整理接口。

    POST JSON:
    {
        "lecture_id": 12,
        "task_id": "xxxx"
    }

    lecture_id 优先级高于 task_id。
    如果传 lecture_id，则从 LectureArchive.summary_file 读取内容。
    如果只传 task_id，则从 realtime_tasks 中读取 content。
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '仅支持 POST 请求'
        }, status=405)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}

        lecture_id = data.get('lecture_id')
        task_id = data.get('task_id')

        lecture = None
        raw_content = ""
        subject = ""

        # 优先从讲义数据库读取
        if lecture_id:
            try:
                lecture = LectureArchive.objects.get(id=lecture_id)
                raw_content = lecture.summary_file or ""
                subject = lecture.subject or ""
            except LectureArchive.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': '讲义不存在，无法整理'
                }, status=404)

        # 如果没有 lecture_id，则从实时任务内存里读取
        if not raw_content and task_id:
            task = _get_realtime_task(task_id)
            if task:
                raw_content = task.get('content', '')
                subject = task.get('params', {}).get('subject', '') or ''
                lecture_id_from_task = task.get('lecture_id')
                if lecture_id_from_task and not lecture:
                    try:
                        lecture = LectureArchive.objects.get(id=lecture_id_from_task)
                    except LectureArchive.DoesNotExist:
                        lecture = None

        if not raw_content.strip():
            return JsonResponse({
                'success': False,
                'message': '没有可整理的讲义内容'
            }, status=400)

        polished_content = polish_realtime_content(raw_content, subject)

        # 保存到讲义数据库
        if lecture:
            lecture.summary_file = polished_content
            lecture.status = 'completed'
            lecture.save()
            save_current_lecture_id(lecture.id)

        # 保存到当前结果文件，保证 Result.vue 立即可读
        try:
            os.makedirs(TEMPFOLD_DIR, exist_ok=True)
            with open(FINAL_OUTPUT_PATH_OCR, 'w', encoding='utf-8') as f:
                f.write(polished_content)
        except Exception as e:
            print(f"一键整理结果写入临时文件失败: {e}")

        # 同步更新实时任务内容
        if task_id:
            _update_realtime_task(
                task_id,
                content=polished_content,
                latest_content="讲义已完成一键整理",
                message="讲义已完成一键整理",
                status="completed",
                progress=100
            )

        return JsonResponse({
            'success': True,
            'message': '讲义整理完成',
            'content': polished_content,
            'lecture_id': lecture.id if lecture else None
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'一键整理失败: {str(e)}'
        }, status=500)


def wait_for_audio_result(timeout=1800, interval=2):
    """
    等待 django2 生成音频识别结果 _full.txt。
    用于实现 OCR 和音频并行：
    - 前端先启动 django2/process_video；
    - django1 自己继续 OCR；
    - django1 到 AI 总结前再等待音频结果。
    """
    import time

    django2_audio_text = os.path.join(
        BASE_DIR.parent,
        'django2',
        'tempfold2',
        '_full.txt'
    )

    django1_audio_dir = os.path.join(BASE_DIR, 'tempfold2')
    os.makedirs(django1_audio_dir, exist_ok=True)

    django1_audio_text = os.path.join(django1_audio_dir, '_full.txt')

    waited = 0

    while waited < timeout:
        if os.path.exists(django2_audio_text) and os.path.getsize(django2_audio_text) > 0:
            try:
                shutil.copyfile(django2_audio_text, django1_audio_text)
                return True
            except Exception as e:
                print(f"复制音频识别结果失败: {e}")
                return False

        progress_status["work"] = f"等待音频识别完成（已等待 {waited} 秒）"
        time.sleep(interval)
        waited += interval

    print("等待音频识别结果超时")
    return False