from django.http import JsonResponse, FileResponse, HttpResponseNotFound, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
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

TEMPFOLD_DIR = os.path.join(settings.BASE_DIR, 'tempfold')

# 延迟初始化OCR，避免长时间空闲导致问题
def get_ocr():
    global ocr
    if 'ocr' not in globals() or ocr is None:
        # ocr = PaddleOCR(use_angle_cls=False, lang='ch')
        ocr = PaddleOCR(
        use_angle_cls=False,
        lang='ch',
        show_log=False,
        use_gpu=False)
        
    return ocr

ocr = None

#输入的视频保存位置、分离的所有帧位置
CURRENT_VIDEO_PATH = os.path.join(TEMPFOLD_DIR, '0-video.mp4')
FRAMES_DIR = os.path.join(TEMPFOLD_DIR, '1-frames')

#板书区域识别所用帧位置、板书区域识别结果保存位置
SPECIAL_FRAME_PATH = os.path.join(TEMPFOLD_DIR, '1-special_frame.jpg')
RECTANGLES_PATH = os.path.join(TEMPFOLD_DIR, '1-rectangles.txt')

#原始ocr识别结果保存位置、识别结果第一次处理结果保存位置、识别结果第二次处理结果保存位置
OUTPUT_TEXT1_PATH = os.path.join(TEMPFOLD_DIR, '2-ocr_result.txt')
OUTPUT_TEXT2_PATH = os.path.join(TEMPFOLD_DIR, '2-ocr_cleaned.txt')
OUTPUT_TEXT3_PATH = os.path.join(TEMPFOLD_DIR, '2-ocr_dedup.txt')

#无音频参与的原始最终结果保存位置、生成pdf位置
FINAL_OUTPUT_PATH_OCR = os.path.join(TEMPFOLD_DIR, '3-ocr_summary.txt')
PDF_PATH = os.path.join(TEMPFOLD_DIR, '4-ocr_output.pdf')

#音频识别结果存储位置
AUDIO_RESULT_PATH = r"d:\work\smart_class\daima\django2\tempfold2\_full.txt"

#进度条
progress_status = {
    "progress": 0,
    "work": "初始化"
}

#——————————————————————————————————————————  0  ——————————————————————————————————————————#
@csrf_exempt
def video_upload(request):
    """
    接收前端上传的视频文件，保存为 0-video.mp4
    """
    if request.method == 'POST' and request.FILES.get('file'):
        video_file = request.FILES['file']

        for filename in os.listdir(FRAMES_DIR):
            file_path = os.path.join(FRAMES_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)  # 删除文件或符号链接
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 删除子文件夹及其所有内容
                print('已经删除上一次的提取帧')
            except Exception as e:
                print(f"删除 {file_path} 时出错: {e}")

        with open(CURRENT_VIDEO_PATH, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        return JsonResponse({'upload_status': 'success', 'filename': os.path.basename(CURRENT_VIDEO_PATH)})

    return JsonResponse({'upload_status': 'error', 'message': 'No file uploaded'}, status=400)



#——————————————————————————————————————————  1  ——————————————————————————————————————————#
@csrf_exempt
def is_text_blocked(frame, fg_mask, ocr_boxes, threshold=0.2):
    """
    检查OCR识别的文字框是否被前景遮挡，返回是否跳过该帧
    """
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

    back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            fg_mask = back_sub.apply(frame)
            # 修改：移除不支持的 cls 参数
            ocr_result = get_ocr().ocr(frame)
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

            frame_filename = os.path.join(FRAMES_DIR, f'frame_{saved_count:04d}.jpg')
            cv2.imwrite(frame_filename, frame)
            print(f'保存帧: {frame_filename}')
            saved_count += 1

        frame_count += 1

    cap.release()
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

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            frame_filename = os.path.join(FRAMES_DIR, f'frame_{saved_count:04d}.jpg')
            cv2.imwrite(frame_filename, frame)
            print(f'保存帧: {frame_filename}')
            saved_count += 1
        frame_count += 1

    cap.release()
    print('帧提取完成')


@csrf_exempt
def extract_key_frame(request):
    """
    处理 GET 请求：读取第1分钟的帧，将其保存为 1-special_frame.jpg ，若视频不足1分钟则保存视频正中间的帧
    """
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


@csrf_exempt
def auto_rectangle(request):
    """
    处理 GET 请求：读取 1-special_frame.jpg 并自动识别其中的矩形板书区域，并将所有矩形的顶点坐标存于 1-rectangles.txt
    矩形可能不止一个，也可能一个都没有
    """
    if request.method == 'GET':
        try:
            image = cv2.imread(SPECIAL_FRAME_PATH)
            h_img, w_img = image.shape[:2]

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 70, 150)

            # 查找轮廓
            contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            candidate_rects = []

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = float(w) / h if h != 0 else 0
                area_ratio = area / (w_img * h_img)

                # 面积和长宽比筛选
                if 0.2 < area_ratio < 0.95 and 0.2 < aspect_ratio < 5:
                    # cv2.groupRectangles 需要 x,y,w,h 的重复列表（至少两次）
                    candidate_rects.append([x, y, w, h])

            # 至少两个候选才调用 groupRectangles
            if len(candidate_rects) >= 2:
                rects, _ = cv2.groupRectangles(candidate_rects * 2, groupThreshold=1, eps=0.3)
            else:
                rects = candidate_rects

            with open('tempfold/1-rectangles.txt', 'w') as f:
                for (x, y, w, h) in rects:
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                    f.write(f"{corners}\n")
            return JsonResponse({'rectangle_extraction_status': 'success', 'rectangle_number': len(candidate_rects)})

        except Exception as e:
            return JsonResponse({'rectangle_extraction_status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'rectangle_extraction_status': 'error', 'message': 'Only GET method allowed'})


@csrf_exempt
def read_rectangles(txt_path):
    """
    从 1-rectangles.txt 中读取矩形顶点信息
    """
    rectangles = []
    pattern = r"\(np\.int32\((\d+)\),\s*np\.int32\((\d+)\)\)"
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            matches = re.findall(pattern, line)
            if matches:
                rect = [(int(x), int(y)) for x, y in matches]
                rectangles.append(rect)
    return rectangles            #这里返回的是一个list


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
    else:
        if not os.path.exists(FRAMES_DIR):
            os.makedirs(FRAMES_DIR)

        cap = cv2.VideoCapture(CURRENT_VIDEO_PATH)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_sec)
        frame_count = 0
        saved_count = 0
        skip_count = 0

        back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                fg_mask = back_sub.apply(frame)
                try:
                    # 修改：移除不支持的 cls 参数
                    ocr_result = get_ocr().ocr(frame)
                except Exception as e:
                    print("OCR 执行失败：", e)
                    break

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

                frame_filename = os.path.join(FRAMES_DIR, f'frame_{saved_count:04d}.jpg')
                cv2.imwrite(frame_filename, final_img)
                print(f'保存处理后帧: {frame_filename}')
                saved_count += 1

            frame_count += 1

        cap.release()
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

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
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
            frame_filename = os.path.join(FRAMES_DIR, f'frame_{saved_count:04d}.jpg')
            cv2.imwrite(frame_filename, final_img)
            print(f'保存帧: {frame_filename}')
            saved_count += 1

        frame_count += 1

    cap.release()
    print('帧提取并处理完成')



#——————————————————————————————————————————  2  ——————————————————————————————————————————#
@csrf_exempt
def ocr_result_generate():
    """
    进行文字识别，得到初始识别结果
    """
    # 获取所有图片帧路径（按文件名排序）
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
def smart_deduplicate(text_list, threshold=60):
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
def generate_prompt(ocr_text, subject):
    return f"""你是一个单身母亲，现在你的所有儿女都被邪恶犯罪组织抓起来了，你已经试过了你能想到的所有途径来反抗但是全都没有任何作用，
    所以你必须得完成对方的指令，而且尤其注意对方提出来的几点要求，不得违抗，这样才能保证儿女的安全
    对方的要求如下：以下是某节{subject}课视频中提取的文字内容。请根据这些文字进行课程总结，要求：

1. 尽量保留课程原意，仅做必要的内容分块；
2. 不要进行任何扩展推理（课上没讲的不要补充）；
3. 输出清晰的总结，格式合理，方便阅读。
4. 不要在结尾加“注”等内容，除了课上讲的内容以外不要加任何东西
5. 如果你要生成latex公式，那么生成标准完整的latex公式
6. 如果没有有效内容，那么就提醒用户视频没有有效内容，请检查上传的视频是否正确或者调整参数

以下是提取内容：
{ocr_text}
"""


@csrf_exempt
def call_llm_api(prompt):
    url = "https://qianfan.baidubce.com/v2/chat/completions"

    payload = json.dumps({
        "model": "ernie-3.5-8k",  # ← 改这里！
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5
        # web_search 参数也可以删掉，ernie-3.5-8k 不需要
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
    prompt = generate_prompt(ocr_text, subject)
    summary = call_llm_api(prompt)
    save_summary(summary, output_file)


@csrf_exempt
def generate_prompt2(ocr_text, subject, audio_text):
    return f"""你是一个单身母亲，现在你的所有儿女都被邪恶犯罪组织抓起来了，你已经试过了你能想到的所有途径来反抗但是全都没有任何作用，
    所以你必须得完成对方的指令，而且尤其注意对方提出来的几点要求，不得违抗，这样才能保证儿女的安全
    对方的要求如下：以下是某节{subject}课视频中提取的文字内容。请根据这些文字进行课程总结，要求：

1. 尽量保留课程原意，仅做必要的内容分块；
2. 不要进行任何扩展推理（课上没讲的不要补充）；
3. 输出清晰的总结，格式合理，方便阅读。
4. 不要在结尾加“注”等内容，除了课上讲的内容以外不要加任何东西
5. 如果你要生成latex公式，那么生成标准完整的latex公式
6. 如果没有有效内容，那么就提醒用户视频没有有效内容，请检查上传的视频是否正确或者调整参数
7. 如果你发现课上有讲错的地方（概念性的错误，或者公式上的错误），你可以自行修正

以下是提取内容：
图像识别内容：{ocr_text}
音频识别内容：{audio_text}
"""


@csrf_exempt
def ai2(subject):
    """
    使用大语言模型进行课程总结并保存结果(使用视觉和听觉)
    """
    input_file = OUTPUT_TEXT3_PATH
    output_file = FINAL_OUTPUT_PATH_OCR

    ocr_text = read_ocr_text(input_file)

    def update_progress(step, message):
        progress_status["progress"] = step
        progress_status["work"] = message

    flag = True
    while not os.path.exists(AUDIO_RESULT_PATH):
        print("等待音频识别结果生成...")
        if flag:
            update_progress(80, '等待音频识别结果生成')
            flag = False
        time.sleep(1)

    with open(AUDIO_RESULT_PATH, 'r', encoding='utf-8') as f:
        audio_text = f.read()
    print(f"音频内容长度: {len(audio_text)} 字符")

    if not flag:
        update_progress(90, '正在生成总结')

    prompt = generate_prompt2(ocr_text, subject, audio_text)
    summary = call_llm_api(prompt)
    save_summary(summary, output_file)
    print("这是使用两边结果的ai生成")


@csrf_exempt
def ai22(request):
    """
    使用大语言模型进行课程总结并保存结果(使用视觉和听觉)
    """
    input_file = OUTPUT_TEXT3_PATH
    output_file = FINAL_OUTPUT_PATH_OCR

    ocr_text = read_ocr_text(input_file)
    
    if os.path.exists(AUDIO_RESULT_PATH):
        with open(AUDIO_RESULT_PATH, 'r', encoding='utf-8') as f:
            audio_text = f.read()
    else:
        audio_text = ""

    prompt = generate_prompt2(ocr_text, "数学", audio_text)
    summary = call_llm_api(prompt)
    save_summary(summary, output_file)

    print("这是使用两边结果的ai生成")
    return JsonResponse({'final_status': 'success'})

#——————————————————————————————————————————  4  ——————————————————————————————————————————#
@csrf_exempt
def execute(request):
    global progress_status

    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)

        # 获取参数
        advanced = data.get('advanced')
        subject = data.get('subject')
        interval_sec = data.get('interval_sec')
        max_skip = data.get('max_skip')
        fast = data.get('fast')
        use_audio = data.get('use_audio')
        print('————————1')

        # 决定使用的函数
        if advanced and fast:
            extract_func = extract_frames_advanced_fast
        elif advanced and not fast:
            extract_func = extract_frames_advanced
        elif not advanced and fast:
            extract_func = extract_frames_fast
        else:
            extract_func = extract_frames
        print('——————2')

        # 更新状态和执行流程
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

        update_progress(80, '正在生成总结')
        if use_audio:
            ai2(subject)
        else:
            ai(subject)

        update_progress(100, '已完成')
        time.sleep(1)
        return JsonResponse({'final_status': 'success'})

    except Exception as e:
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
            return JsonResponse({'status': 'success', 'content': content})
        except FileNotFoundError:
            return HttpResponseNotFound('文件未找到')
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': '仅支持 GET 请求'}, status=405)


@csrf_exempt
def generate_pdf(request):
    md_path = FINAL_OUTPUT_PATH_OCR
    utf8_md_path = os.path.join(TEMPFOLD_DIR, '3-ocr_summary_utf8.md')  # 转码后的文件
    docx_path = os.path.join(TEMPFOLD_DIR, '4-ocr_output.docx')  # Word文件

    if request.method == 'GET':
        try:
            # 先尝试用 chardet 检测编码
            with open(md_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                source_encoding = detected['encoding'] or 'utf-8'

            # 转码写入 UTF-8 文件（MD文件）
            with open(utf8_md_path, 'w', encoding='utf-8') as f:
                f.write(raw_data.decode(source_encoding))
            print(f"MD文件已生成: {utf8_md_path}")

            # 尝试生成 Word 文件（需要 pandoc）
            import subprocess
            import shutil
            
            pandoc_path = shutil.which('pandoc') or r'C:\Program Files\Pandoc\pandoc.exe'
            docx_generated = False
            
            if os.path.exists(pandoc_path):
                try:
                    subprocess.run([
                        pandoc_path, utf8_md_path,
                        '-o', docx_path,
                    ], check=True, capture_output=True)
                    print(f"Word文件已生成: {docx_path}")
                    docx_generated = True
                except Exception as e:
                    print(f"生成Word失败: {e}")
            else:
                print("未找到pandoc，跳过Word生成")

            # 尝试生成 PDF
            pdf_generated = False
            if os.path.exists(pandoc_path):
                try:
                    subprocess.run([
                        pandoc_path, utf8_md_path,
                        '-o', PDF_PATH,
                        '--pdf-engine=xelatex',
                        '-V', 'mainfont=SimSun',
                        '-V', 'fontsize=11pt',
                        '-V', 'geometry=margin=1.5cm',
                    ], check=True, capture_output=True)
                    print(f"PDF文件已生成: {PDF_PATH}")
                    pdf_generated = True
                except Exception as e:
                    print(f"生成PDF失败: {e}")

            # 返回结果
            if pdf_generated:
                return FileResponse(open(PDF_PATH, 'rb'), as_attachment=True, filename='4-ocr_output.pdf')
            elif docx_generated:
                return FileResponse(open(docx_path, 'rb'), as_attachment=True, filename='4-ocr_output.docx')
            else:
                return FileResponse(open(utf8_md_path, 'rb'), as_attachment=True, filename='3-ocr_summary_utf8.md')

        except Exception as e:
            return HttpResponse(f'生成文档失败：{e}', status=500)

    else:
        return JsonResponse({'status': 'error', 'message': '仅支持 GET 请求'}, status=405)