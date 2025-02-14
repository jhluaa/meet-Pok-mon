import sounddevice as sd
import soundfile as sf
from kokoro_onnx import Kokoro
import numpy as np

"""
https://github.com/thewh1teagle/kokoro-onnx/tree/main

https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
1. Install dependencies:
   sudo apt-get install portaudio19-dev
   pip install kokoro-onnx sounddevice
2. Download a model (choose one):
   - INT8 (88MB):
     wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.int8.onnx
   - FP16 (169MB):
     wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.fp16.onnx
3. Download voices-v1.0.bin:
   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
"""


def generate_silence(duration_seconds, sample_rate):
    """
    生成指定长度（秒）的静音音频片段（numpy array）。
    """
    return np.zeros(int(duration_seconds * sample_rate))

def init_kokoro(model_path="kokoro-v1.0.onnx", voices_path="voices-v1.0.bin"):
    """
    初始化 Kokoro 引擎，返回一个 Kokoro 对象。
    model_path: onnx 模型文件路径
    voices_path: .bin 语音模型文件路径
    """
    return Kokoro(model_path, voices_path)

def synthesize_text(kokoro, text, voice="af_sarah", speed=1.0, lang="en-us"):
    """
    用 kokoro 生成对应文本的音频数据（samples）和采样率（sample_rate）。
    kokoro: 已经初始化好的 Kokoro 对象
    text: 要合成的文本
    voice: 使用的声音名称（如 "af_sarah"）
    speed: 语速
    lang: 语言代码
    """
    samples, sample_rate = kokoro.create(
        text,
        voice=voice,
        speed=speed,
        lang=lang,
    )
    return samples, sample_rate

def play_audio(samples, sample_rate):
    """
    播放音频数据，并在播放结束后等待（阻塞）。
    """
    sd.play(samples, sample_rate)
    sd.wait()

def save_audio(filename, samples, sample_rate):
    """
    将音频数据保存成 .wav 文件。
    filename: 保存的文件名，如 "output.wav"
    samples: 需要保存的音频数据（numpy array）
    sample_rate: 采样率
    """
    sf.write(filename, samples, sample_rate)

def generate_and_save_podcast(kokoro, sentences, output_path="podcast.wav",
                              speed=1.0, lang="en-us", random_pause=False):
    """
    将一系列的句子（含 voice、text）合成为单个音频并保存为 podcast.wav。

    sentences: list of dict, 每一项形如: {"voice": "af_sarah", "text": "xxx"}
    output_path: 输出文件名，比如 "podcast.wav"
    speed: 全局语速
    lang: 语言代码
    random_pause: 是否在句子之间插入随机长度的停顿
    """
    all_audio = []
    sample_rate = 22050  # 先给一个默认值，后面第一次合成会覆盖

    for s in sentences:
        voice = s["voice"]
        text = s["text"]
        print(f"Generating with {voice}: {text}")

        samples, sample_rate = kokoro.create(
            text,
            voice=voice,
            speed=speed,
            lang=lang
        )
        all_audio.append(samples)

        # 如果需要在句子之间插入随机静音
        if random_pause:
            import random
            pause_duration = random.uniform(0.5, 2.0)  # 随机 0.5 - 2 秒
            silence = generate_silence(pause_duration, sample_rate)
            all_audio.append(silence)

    # 将所有音频数组拼接
    full_audio = np.concatenate(all_audio, axis=0)
    # 保存到文件
    sf.write(output_path, full_audio, sample_rate)
    print(f"Saved podcast audio to {output_path}")
