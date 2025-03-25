from moviepy.video.io.VideoFileClip import VideoFileClip

video_path = "test.mp4"  # 确保该文件存在
audio_path = "output.wav"  # 输出的音频文件

# 加载视频
clip = VideoFileClip(video_path)

# 提取音频并保存
clip.audio.write_audiofile(audio_path)

print("音频提取完成，保存为:", audio_path)
