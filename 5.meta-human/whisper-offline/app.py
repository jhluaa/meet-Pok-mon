#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import io
import soundfile as sf
from flask import Flask, request, jsonify
import logging

# Whisper 相关
from whisper.model import load_model
from whisper.transcribe import transcribe

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# 加载 Whisper 模型（可根据需要修改："tiny", "base", "small", "medium", "large"...）
MODEL_NAME = os.getenv("WHISPER_MODEL", "small")
model = load_model(MODEL_NAME)


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    """接收音频文件并进行语音转写"""
    app.logger.debug("🔊 接收到音频请求")
    if 'audio' not in request.files:
        app.logger.error("❌ 没有音频文件")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    app.logger.debug(f"📁 文件名：{audio_file.filename}")

    try:
        # 将文件读到内存中并用 soundfile 读取为 NumPy 数组
        wav_stream = io.BytesIO(audio_file.read())
        audio_array, samplerate = sf.read(wav_stream)
        app.logger.debug(f"🎵 采样率：{samplerate}，音频长度：{len(audio_array)}")
    except Exception as e:
        app.logger.error(f"🚫 读取失败：{e}")
        return jsonify({"error": f"Failed to read audio file: {str(e)}"}), 500

    try:
        # 使用 Whisper 进行转写
        result = transcribe(
            model=model,
            audio=audio_array,
            verbose=True,
            temperature=0.0,
            best_of=5,
            beam_size=5,
            language="zh"
        )

        # 为避免 JSON 序列化时出现 float32 无法序列化的问题，把 start/end 转为 Python float
        segments = []
        for seg in result.get("segments", []):
            seg["start"] = float(seg["start"])
            seg["end"] = float(seg["end"])
            segments.append(seg)

        app.logger.debug(f"✅ 识别结果：{result['text']}")
        return jsonify({"text": result["text"], "segments": segments})
    except Exception as e:
        app.logger.error(f"⚠️ 识别失败：{e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 调试模式下直接运行 Flask 服务
    # 如果要线上部署，请使用 WSGI 服务器（gunicorn、uwsgi 等）
    app.run(host="0.0.0.0", port=5021, debug=True)
