#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import time
import pyaudio
import collections
import audioop
import wave
import configparser

from base import setting
from utils.asr import FunASR

class Recorder:
    def __init__(self, funasr_event):
        self.funasr_event = funasr_event
        self.asr_client = FunASR()
        self.asr_client.start()

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

        # 缓冲区，比如2秒，避免漏掉开头
        self.BUFFER_SECONDS = 2.0
        self.BUFFER_SIZE = int(self.RATE / self.CHUNK * self.BUFFER_SECONDS)

        # 用于回溯的环形缓冲，随时存最新2秒音频
        self.audio_buffer = collections.deque(maxlen=self.BUFFER_SIZE)

        # 动态音量检测
        self.MAX_LEVEL = 25000
        self.history_level = []
        self.dynamic_threshold = 0.2
        self.MAX_HISTORY = 500
        self.ratio = 0.8

        # 结束判定：说话结束后多少个CHUNK的静音才停止
        self.SILENCE_SECONDS = 0.7
        self.MAX_SILENCE_FRAMES = int(self.RATE / self.CHUNK * self.SILENCE_SECONDS)

        # 录音状态
        self.is_recognizing = False
        self.frames = []  # 真正要送ASR的语音片段

    @staticmethod
    def get_config_value(group, key):
        con = configparser.ConfigParser()
        con.read(setting.CONFIG_DIR, encoding="utf-8")
        return con.get(group, key)

    def record_audio(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        print("[Recorder]麦克风已开启，等待唇动触发...")

        try:
            while True:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_buffer.append(data)

                # ------ 动态音量检测 ------
                level = audioop.rms(data, 2)
                self.update_history_level(level)
                dynamic_threshold = self.dynamic_threshold * self.ratio
                percentage = level * 5 / self.MAX_LEVEL
                sound_detected = (percentage > dynamic_threshold)
                # 如果唇动检测线程已经 set 了事件 => 说明正在说话
                is_talking = self.funasr_event.is_set()

                # 情形1：正处于说话阶段 + 音量检测到声音
                if is_talking and sound_detected:
                    if not self.is_recognizing:
                        # 第一次检测到说话 -> 复制环形缓冲区到 frames
                        # 这样可以回溯2秒，避免漏字
                        print("[Recorder] ▶ 侦测到唇动+声音，开始录音（含前2秒缓冲）...")
                        self.frames = list(self.audio_buffer)
                        self.is_recognizing = True
                    else:
                        # 已经在录音，就不断追加
                        self.frames.append(data)

                # 情形2：已经在录音，但当前帧音量不够 or lip事件变clear
                elif self.is_recognizing:
                    # 判断一下是否完全安静 -> 如果连续0.7秒安静就结束一段录音
                    silence_frames = 0
                    while silence_frames < self.MAX_SILENCE_FRAMES:
                        data2 = stream.read(self.CHUNK, exception_on_overflow=False)
                        self.frames.append(data2)
                        self.audio_buffer.append(data2)

                        level2 = audioop.rms(data2, 2)
                        self.update_history_level(level2)
                        percentage2 = level2 * 5 / self.MAX_LEVEL
                        sound_detected2 = (percentage2 > dynamic_threshold)

                        if sound_detected2:
                            silence_frames = 0  # 又有声音，就继续录
                        else:
                            silence_frames += 1

                    # 执行到这里，说明连续0.7秒无声音 => 这段说话结束
                    print("[Recorder] ⏹ 录音结束，开始ASR识别...")
                    self.recognize_speech(self.frames)
                    self.is_recognizing = False
                    self.frames = []

                # 如果唇动没检测到，且没声音，就什么也不做
                time.sleep(0.005)
        except KeyboardInterrupt:
            print("[Recorder] 录音已停止（Ctrl+C）")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def update_history_level(self, level):
        """根据实时音量动态调整阈值"""
        self.history_level.append(level)
        if len(self.history_level) > self.MAX_HISTORY:
            self.history_level.pop(0)

        history_average = self.get_history_average(30)
        history_percentage = (history_average / self.MAX_LEVEL) * 1.05 + 0.02

        if history_percentage > self.dynamic_threshold:
            self.dynamic_threshold += (history_percentage - self.dynamic_threshold) * 0.0025
        else:
            self.dynamic_threshold += (history_percentage - self.dynamic_threshold) * 1

    def get_history_average(self, number):
        recent = self.history_level[-number:]
        if not recent:
            return 0
        return sum(recent)/len(recent)

    def recognize_speech(self, frames):
        """将录下来的音频送去ASR，并可选保存一份调试音频"""
        audio_data = b"".join(frames)
        # 可选：保存整段录音到文件查看
        self.save_audio_to_file(frames, "full_recording.wav")

        try:
            self.asr_client.send_byte_array(bytearray(audio_data))
        except Exception as e:
            print("ASR识别异常:", e)

    def save_audio_to_file(self, frames, filename="debug_record.wav"):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(pyaudio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"[Recorder] 已保存录音到: {filename}")
