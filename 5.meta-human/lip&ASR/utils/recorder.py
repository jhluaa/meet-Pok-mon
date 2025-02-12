#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import time
import pyaudio
import collections
import audioop
from base import setting
import configparser
from utils.asr import FunASR


class Recorder:
    def __init__(self, funasr_event):
        self.funasr_event = funasr_event
        self.asr_client = FunASR()
        self.asr_client.start()

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1  # 声道
        self.RATE = 16000  # 采样率
        self.RECORD_SECONDS = 0.5  # 录制1秒
        __BUFFER_SECONDS = 0.5  # 缓冲1秒
        __BUFFER_SIZE = int(self.RATE / self.CHUNK * __BUFFER_SECONDS)
        self.audio_buffer = collections.deque(maxlen=__BUFFER_SIZE)
        self.MAX_LEVEL = 25000  # 最大音量级别
        self.history_level = []
        self.dynamic_threshold = 0.2  # 动态声音阈值的初始值
        self.MAX_HISTORY = 500  # 历史音量级别的最大长度
        self.MAX_SILENCE_FRAMES = int(self.RATE / self.CHUNK * self.RECORD_SECONDS)
        self.is_recognizing = False  # 是否正在进行语音识别
        self.frames = []  # 存储音频帧
        self.ratio = 0.8  # float(self.get_config_value("sound_threshold", "ratio"))

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

        try:
            while True:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_buffer.append(data)
                # 计算当前音频的音量级别
                level = audioop.rms(data, 2)

                self.update_history_level(level)
                # print("dynamic_threshold", self.dynamic_threshold)
                percentage = level * 5 / self.MAX_LEVEL
                # print("percentage", percentage)
                # print("dynamic_threshold", self.dynamic_threshold)
                # print("阈值比", percentage)
                # print("percentage", percentage)
                dynamic_threshold = self.dynamic_threshold * self.ratio
                # 判断是否有声音(使用动态阈值)
                sound_detected = percentage > dynamic_threshold
                # print("sound_detected", sound_detected)
                # print(" self.dynamic_threshold ", self.dynamic_threshold)
                # 检查用户是否处于talking状态
                is_talking = self.funasr_event.is_set()
                if sound_detected and is_talking:
                    # 有声音且处于talking状态，进行录音
                    if not self.is_recognizing:
                        print("检测到有声音且处于lip_open状态，开始语音识别...")
                        self.frames = list(self.audio_buffer)  # 获取缓冲的音频数据
                        self.is_recognizing = True
                    self.frames.append(data)
                elif self.is_recognizing:
                    # 如果之前在识别状态，现在需要结束识别
                    # 为了避免过早结束，继续录制一段时间
                    # silence_frames = 0
                    # while silence_frames < self.MAX_SILENCE_FRAMES:
                    #     data = stream.read(self.CHUNK, exception_on_overflow=False)
                    #     level = audioop.rms(data, 2)
                    #     self.frames.append(data)
                    #     self.update_history_level(level)
                    #     percentage = level * 5 / self.MAX_LEVEL
                    #     sound_detected = percentage > dynamic_threshold
                    #
                    #     if sound_detected:
                    #         silence_frames = 0  # 重置计数器
                    #     else:
                    #         silence_frames += 1

                    # 结束录音，进行ASR
                    self.recognize_speech(self.frames)
                    self.is_recognizing = False
                    self.frames = []
                    print("语音识别完成。")
                else:
                    pass
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("录音已停止。")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def update_history_level(self, level):
        # 更新历史音量级别列表
        self.history_level.append(level)
        if len(self.history_level) > self.MAX_HISTORY:
            self.history_level.pop(0)

        # 计算历史音量的平均值
        history_average = self.get_history_average(30)
        history_percentage = (history_average / self.MAX_LEVEL) * 1.05 + 0.02

        # 动态调整阈值
        if history_percentage > self.dynamic_threshold:
            self.dynamic_threshold += (
                history_percentage - self.dynamic_threshold
            ) * 0.0025
        elif history_percentage < self.dynamic_threshold:
            self.dynamic_threshold += (history_percentage - self.dynamic_threshold) * 1

    def get_history_average(self, number):
        # 计算最近number个音量级别的平均值
        total = 0
        num = 0
        for level in reversed(self.history_level[-number:]):
            total += level
            num += 1
        if num == 0:
            return 0
        return total / num

    def recognize_speech(self, frames):
        try:
            audio_data = b"".join(frames)
            audio_bytearray = bytearray(audio_data)
            self.asr_client.send_byte_array(audio_bytearray)
        except Exception as e:
            print(e)
