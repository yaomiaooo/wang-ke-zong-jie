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

Video_Path = r"d:\work\smart_class\daima\django1\tempfold\0-video.mp4"
PROGRESS_FILE = "tempfold2/progress.txt"


def update_progress(percent: float, message: str = ""):
    """将当前进度写入 progress.txt"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        f.write(f"{percent},{message}\n")

# ================== 核心功能 ==================
@csrf_exempt
def extract_audio_from_video(video_path: str, output_dir: str = None) -> str:
    """从视频提取音频并返回音频路径"""

    try:
        # 清空 tempfold2 文件夹内容
        temp_audio_dir = r"D:\Paraliesa\python\jisuanjishijue\keshe\django2\audioprocess\tempfold2"
        if os.path.exists(temp_audio_dir):
            for filename in os.listdir(temp_audio_dir):
                file_path = os.path.join(temp_audio_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

        update_progress(1, "提取音频中")
        video = VideoFileClip(video_path)
        output_dir = output_dir or os.path.dirname(video_path)
        os.makedirs(output_dir, exist_ok=True)

        audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3"
        audio_output_path = os.path.join("tempfold2/", audio_filename)

        video.audio.write_audiofile(audio_output_path,
                                    codec='libmp3lame',
                                    ffmpeg_params=['-y'])
        update_progress(7, "音频提取完成")
        return audio_output_path
    except Exception as e:
        update_progress(100, f"音频提取失败: {str(e)}")
        raise


@csrf_exempt
def transcribe_audio(audio_path: str, model_size: str = "small") -> dict:
    """语音转文字（返回包含分段和时间戳的完整结果）"""
    update_progress(7, f"加载Whisper模型（{model_size}）")
    print(f"——————————加载Whisper模型（{model_size}）")
    try:
        # 自动判断是否有可用 GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"——————————当前使用设备: {device}")

        # 加载 Whisper 模型到指定设备
        model = whisper.load_model(model_size, device=device)
        update_progress(14, "模型加载完成，开始语音识别")
        print("模型加载完成，开始语音识别")

        # 执行语音转文字
        result = model.transcribe(audio_path, language='zh')
        update_progress(98, "语音识别完成，开始生成结果")
        return result

    except Exception as e:
        update_progress(100, f"❌ 识别失败: {str(e)}")
        print(f"❌ 语音识别失败: {str(e)}")
        raise



@csrf_exempt
def save_results(result: Dict, original_path: str):
    """保存多种格式结果"""
    output_dir = os.path.dirname(original_path)

    # 保存三种格式
    formats = {
        "_full.txt": result['text'],
    }

    for suffix, content in formats.items():
        path = os.path.join(output_dir, suffix)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"——————————已保存: {path}")
        update_progress(100, "语音识别完成")


# ================== 主流程 ==================
@csrf_exempt
def process_video(request):
    """完整的视频处理流程"""
    if request.method == "GET":
        try:
            # 1. 提取音频
            audio_path = extract_audio_from_video(Video_Path)
            # 2. 语音转文字
            result = transcribe_audio(audio_path)
            # 3. 保存结果
            save_results(result, PROGRESS_FILE)
            return JsonResponse({"status": True})

        except Exception as e:
            print(f"\n🔴 处理失败: {str(e)}")
            return JsonResponse({"status": False,"error": str(e)})
    else:
        return JsonResponse({'status': False, 'message': 'Only GET method allowed'}, status=405)

@csrf_exempt
def get_progress(request):
    if request.method == "GET":
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                line = f.readline().strip()
                if ',' in line:
                    percent_str, message = line.split(',', 1)
                    percent = int(percent_str)
                else:
                    percent = 0
                    message = "读取格式错误"

            return JsonResponse({
                "percent": percent,
                "message": message
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "error": f"读取进度失败: {str(e)}"
            }, status=500)

    return JsonResponse({"error": "仅支持 GET 请求"}, status=405)
