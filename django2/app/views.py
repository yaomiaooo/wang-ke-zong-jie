from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
import whisper
from moviepy import VideoFileClip
from typing import Dict
import torch
import shutil

# ================== 配置区 ==================
FFMPEG_DIR = r"D:/ffmpeg/bin"
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ["PATH"]
FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg.exe")

# 注意：不再使用硬编码路径，改为函数参数传入

def update_progress(progress_file, percent: float, message: str = ""):
    """将当前进度写入指定的进度文件"""
    with open(progress_file, 'w', encoding='utf-8') as f:
        f.write(f"{percent},{message}\n")

# ================== 核心功能 ==================
def extract_audio_from_video(video_path: str, output_dir: str) -> str:
    """从视频提取音频并返回音频路径"""
    # 清空输出目录（可选，由调用方决定是否清空）
    os.makedirs(output_dir, exist_ok=True)
    # 注意：此处不应清空目录，清空操作由调用方负责，避免覆盖其他文件
    video = VideoFileClip(video_path)
    audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3"
    audio_output_path = os.path.join(output_dir, audio_filename)
    video.audio.write_audiofile(audio_output_path,
                                codec='libmp3lame',
                                ffmpeg_params=['-y'])
    return audio_output_path

def transcribe_audio(audio_path: str, model_size: str = "small") -> dict:
    """语音转文字（返回包含分段和时间戳的完整结果）"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"当前使用设备: {device}")
    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_path, language='zh')
    return result

def save_results(result: Dict, output_dir: str):
    """保存多种格式结果"""
    formats = {
        "_full.txt": result['text'],
    }
    for suffix, content in formats.items():
        path = os.path.join(output_dir, suffix)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已保存: {path}")

# ================== 对外提供的同步接口 ==================
def run_audio_recognition(video_path: str, output_dir: str, model_size: str = "small") -> dict:
    """
    完整的音频识别流程（同步执行）
    :param video_path: 视频文件路径
    :param output_dir: 输出目录（音频文件和识别结果都存放在此）
    :param model_size: Whisper 模型大小
    :return: 识别结果字典
    """
    progress_file = os.path.join(output_dir, 'progress.txt')
    update_progress(progress_file, 1, "提取音频中")
    audio_path = extract_audio_from_video(video_path, output_dir)
    update_progress(progress_file, 7, "音频提取完成")
    update_progress(progress_file, 7, f"加载Whisper模型（{model_size}）")
    result = transcribe_audio(audio_path, model_size)
    update_progress(progress_file, 98, "语音识别完成，开始生成结果")
    save_results(result, output_dir)
    update_progress(progress_file, 100, "语音识别完成")
    return result

# ================== Django 视图（向后兼容） ==================
@csrf_exempt
def process_video(request):
    """
    兼容旧版前端直接调用的 GET 请求，但内部会使用当前全局视频路径和默认输出目录。
    注意：此视图不会主动清空输出目录，可能导致旧文件残留。
    推荐前端改用主流程中的 execute（use_audio=True）方式。
    """
    if request.method == "GET":
        try:
            from django.conf import settings
            video_path = os.path.join(settings.BASE_DIR.parent, 'django1', 'tempfold', '0-video.mp4')
            output_dir = os.path.join(settings.BASE_DIR, 'tempfold2')
            # 清空输出目录以保证最新
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            run_audio_recognition(video_path, output_dir)
            return JsonResponse({"status": True})
        except Exception as e:
            print(f"处理失败: {str(e)}")
            return JsonResponse({"status": False, "error": str(e)})
    else:
        return JsonResponse({'status': False, 'message': 'Only GET method allowed'}, status=405)

@csrf_exempt
def get_progress(request):
    """获取音频识别进度（仅当单独调用 process_video 时有用）"""
    if request.method == "GET":
        try:
            from django.conf import settings
            progress_file = os.path.join(settings.BASE_DIR, 'tempfold2', 'progress.txt')
            if not os.path.exists(progress_file):
                return JsonResponse({"percent": 0, "message": "等待开始"})
            with open(progress_file, 'r', encoding='utf-8') as f:
                line = f.readline().strip()
                if ',' in line:
                    percent_str, message = line.split(',', 1)
                    percent = int(percent_str)
                else:
                    percent = 0
                    message = "读取格式错误"
            return JsonResponse({"percent": percent, "message": message})
        except Exception as e:
            return JsonResponse({"error": f"读取进度失败: {str(e)}"}, status=500)
    return JsonResponse({"error": "仅支持 GET 请求"}, status=405)