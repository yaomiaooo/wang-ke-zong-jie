from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
import whisper
from moviepy import VideoFileClip
from typing import Dict
import torch
import shutil
import threading

# ================== 配置区 ==================
FFMPEG_DIR = r"D:/ffmpeg/bin"
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ["PATH"]
FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg.exe")

# ================== 全局进度状态 ==================
audio_progress_status = {
    "percent": 0,
    "message": "等待开始",
    "status": "idle"  # idle / processing / completed / failed
}

audio_progress_lock = threading.Lock()


def set_audio_progress(percent: int, message: str, status: str = "processing"):
    """同时更新内存进度状态"""
    percent = max(0, min(100, int(percent)))
    with audio_progress_lock:
        audio_progress_status["percent"] = percent
        audio_progress_status["message"] = message
        audio_progress_status["status"] = status


def get_audio_progress_snapshot():
    with audio_progress_lock:
        return dict(audio_progress_status)


def update_progress(progress_file, percent: float, message: str = ""):
    """将当前进度写入指定的进度文件，同时更新内存状态"""
    percent = int(percent)
    set_audio_progress(percent, message)
    with open(progress_file, 'w', encoding='utf-8') as f:
        f.write(f"{percent},{message}\n")


# ================== 核心功能 ==================
def extract_audio_from_video(video_path: str, output_dir: str) -> str:
    """从视频提取音频并返回音频路径"""
    os.makedirs(output_dir, exist_ok=True)

    video = VideoFileClip(video_path)
    audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3"
    audio_output_path = os.path.join(output_dir, audio_filename)

    video.audio.write_audiofile(
        audio_output_path,
        codec='libmp3lame',
        ffmpeg_params=['-y']
    )

    try:
        video.close()
    except Exception:
        pass

    return audio_output_path


def transcribe_audio(audio_path: str, model_size: str = "small") -> dict:
    """语音转文字（返回包含分段和时间戳的完整结果）"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"当前使用设备: {device}")

    set_audio_progress(12, f"正在加载 Whisper 模型（{model_size}）", "processing")
    model = whisper.load_model(model_size, device=device)

    set_audio_progress(25, "正在进行语音识别，请稍候", "processing")
    result = model.transcribe(audio_path, language='zh')

    return result


def save_results(result: Dict, output_dir: str):
    """保存识别结果"""
    formats = {
        "_full.txt": result.get('text', ''),
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
    """
    progress_file = os.path.join(output_dir, 'progress.txt')

    update_progress(progress_file, 1, "正在提取音频")
    audio_path = extract_audio_from_video(video_path, output_dir)

    update_progress(progress_file, 10, "音频提取完成")
    update_progress(progress_file, 15, f"正在加载 Whisper 模型（{model_size}）")

    result = transcribe_audio(audio_path, model_size)

    update_progress(progress_file, 95, "语音识别完成，正在保存结果")
    save_results(result, output_dir)

    update_progress(progress_file, 100, "语音识别完成")
    set_audio_progress(100, "语音识别完成", "completed")

    return result


# ================== Django 视图 ==================
@csrf_exempt
def process_video(request):
    """
    前端直接调用的音频识别接口。
    这个接口同步执行：
    请求没有返回前，说明音频识别还没结束。
    进度通过 /get_progress 获取。
    """
    if request.method == "GET":
        try:
            from django.conf import settings

            # 每次新任务开始，先立即清空旧进度
            set_audio_progress(0, "准备开始音频识别", "processing")

            video_path = os.path.join(
                settings.BASE_DIR.parent,
                'django1',
                'tempfold',
                '0-video.mp4'
            )
            output_dir = os.path.join(settings.BASE_DIR, 'tempfold2')

            # 清空输出目录，避免读取上一次 _full.txt 和 progress.txt
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)

            progress_file = os.path.join(output_dir, 'progress.txt')
            update_progress(progress_file, 0, "准备开始音频识别")

            if not os.path.exists(video_path):
                set_audio_progress(100, "视频文件不存在，音频识别失败", "failed")
                return JsonResponse({
                    "status": False,
                    "error": "视频文件不存在，请先上传视频"
                }, status=404)

            run_audio_recognition(video_path, output_dir)

            return JsonResponse({
                "status": True,
                "message": "语音识别完成"
            })

        except Exception as e:
            print(f"处理失败: {str(e)}")
            set_audio_progress(100, f"音频识别失败: {str(e)}", "failed")
            return JsonResponse({
                "status": False,
                "error": str(e)
            }, status=500)

    return JsonResponse({
        'status': False,
        'message': 'Only GET method allowed'
    }, status=405)


@csrf_exempt
def get_progress(request):
    """
    获取音频识别进度。
    优先返回内存状态，避免读到旧 progress.txt。
    """
    if request.method == "GET":
        snapshot = get_audio_progress_snapshot()
        return JsonResponse(snapshot)

    return JsonResponse({
        "error": "仅支持 GET 请求"
    }, status=405)