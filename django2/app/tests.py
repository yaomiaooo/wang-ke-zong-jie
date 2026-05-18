import sys
print("Python路径：", sys.executable)

try:
    from moviepy import VideoFileClip
    print("moviepy 正常导入")
except Exception as e:
    print("导入失败：", e)