#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

# API 服务器地址（注意要和上面 server.py 中设置的 HOST、PORT 对应）
API_URL = "http://localhost:5021/transcribe"

# 测试音频文件路径
AUDIO_FILE = "test.wav"

def format_timestamp(seconds):
    """将秒转换为 00:00:00.000 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"

def transcribe_audio(audio_path):
    """将本地音频文件发送到服务器进行语音转写，并打印结果。"""
    try:
        with open(audio_path, "rb") as audio_file:
            files = {"audio": audio_file}
            response = requests.post(API_URL, files=files)

        if response.status_code == 200:
            # 成功获取结果
            result = response.json()
            segments = result.get("segments", [])

            if segments:
                print("\n🎙️ 转写结果：\n")
                for segment in segments:
                    start_time = format_timestamp(segment["start"])
                    end_time = format_timestamp(segment["end"])
                    text = segment["text"].strip()
                    print(f"[{start_time} --> {end_time}] {text}")
            else:
                print("❌ 未检测到语音内容。")
        else:
            # 如果接口返回错误
            print(f"❌ 请求失败，状态码：{response.status_code}")
            print(response.json())

    except Exception as e:
        print(f"❌ 发生错误：{str(e)}")

if __name__ == "__main__":
    # 执行测试
    transcribe_audio(AUDIO_FILE)
