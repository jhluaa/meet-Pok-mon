#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
完整自包含的百度 TTS 实现示例

实现内容：
  1. 自定义配置加载模块 (configUtil)
  2. 自定义日志模块 (Log)
  3. 百度 TTS 语音合成（单句和长文本自动分句）
  4. 播放合成后的语音（使用 pygame 播放）

注意事项：
https://juejin.cn/post/7266634807449337893  tts
https://ai.baidu.com/ai-doc/SPEECH/mlbxh7xie  实例文档
  - 请在运行前根据实际情况设置 configUtil.voice_config 中的
    "baidu_api_key" 与 "baidu_secret_key"
  - 本示例中生成的音频文件将保存在 BASE_DIR/resources/temp 目录下，
    运行前请确保有写入权限。
"""

import os
import time
import hashlib
import requests
import pygame
import re
from pypinyin import lazy_pinyin


# ---------------------- 自定义配置模块 ----------------------
class configUtil:
    #  百度TTS APi的Key
    voice_config = {
        "baidu_api_key": "tLMJWS0UKBmzpWVyHp6QF8DS",  # API Key
        "baidu_secret_key": "7E4lNDs4HAaJtymiKe2RmHj61XkKaqMM",  # Secret Key
        "soundType": 0,  # 语音类型：0 表示女声，1 表示男声，4 表示情感合成 表示人
        "speed": 5,  # 语速，取值 0~15，5为默认
        "pitch": 5  # 音调，取值 0~15，5为默认
    }

    @staticmethod
    def load_config():
        # 此处可扩展从文件加载配置，本示例只做提示
        print("[INFO] 配置加载完成。")


# ---------------------- 自定义日志模块 ----------------------
class Log:
    def error(self, message):
        print("[ERROR]", message)

    def info(self, message):
        print("[INFO]", message)


# ---------------------- 全局变量与目录设置 ----------------------
# BASE_DIR 指当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 生成音频文件保存目录：BASE_DIR/resources/temp
TEMP_DIR = os.path.join(BASE_DIR, "resources", "temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


# ---------------------- 百度 TTS 实现类 ----------------------
class BaiduTTS:
    def __init__(self):
        self.history_data = []  # 缓存已合成的文本与文件路径，格式为 (text, filepath)
        self.stop_synthesis = False
        self.log = Log()
        self.token = None
        self.token_expire = 0
        self._load_config()

    def _load_config(self):
        """加载 TTS 配置"""
        self.api_key = configUtil.voice_config.get("baidu_api_key")
        self.secret_key = configUtil.voice_config.get("baidu_secret_key")
        self.voice_type = configUtil.voice_config.get("soundType", 0)
        self.speed = configUtil.voice_config.get("speed", 5)
        self.pitch = configUtil.voice_config.get("pitch", 5)

    def _get_token(self):
        """获取百度 API Token（自动缓存 Token，提前 1 小时过期）"""
        if time.time() < self.token_expire:
            return self.token

        url = "https://openapi.baidu.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        try:
            response = requests.get(url, params=params)
            result = response.json()
            self.token = result["access_token"]
            # 提前 1 小时失效
            self.token_expire = time.time() + result["expires_in"] - 3600
            self.log.info("成功获取 Token")
            return self.token
        except Exception as e:
            self.log.error(f"获取Token失败: {str(e)}")
            return None

    def _generate_filename(self, text):
        """生成唯一文件名，基于文本的 md5 值"""
        md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"tts_{md5}.mp3"

    def _clean_text(self, text):
        """清洗文本：去除空白字符和 <br/> 标签"""
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"<br\s*/?>", "", text)
        return text.strip()

    def _split_sentences(self, text, max_len=50):
        """
        智能分句：根据标点和最大长度对长文本进行分句
        例如：中文句号、感叹号、问号、分号、以及省略号
        """
        sentences = []
        current = []
        current_len = 0

        for char in text:
            current.append(char)
            current_len += 1
            if char in ["。", "！", "？", "；", "…"] and current_len >= max_len // 2:
                sentences.append("".join(current))
                current = []
                current_len = 0
            elif current_len >= max_len:
                sentences.append("".join(current))
                current = []
                current_len = 0

        if current:
            sentences.append("".join(current))
        return sentences

    def text_to_speech(self, text, callback=None):
        """
        主合成方法：对单段文本进行语音合成，并调用回调函数返回合成后音频文件路径

        Args:
            text (str): 待合成文本
            callback (function): 回调函数，传入参数为音频文件路径
        """
        if not text:
            return None

        text = self._clean_text(text)
        filename = self._generate_filename(text)
        filepath = os.path.join(TEMP_DIR, filename)

        # 检查缓存，避免重复合成
        for data in self.history_data:
            if data[0] == text and os.path.exists(data[1]):
                if callback:
                    callback(data[1])
                return data[1]

        token = self._get_token()
        if not token:
            return None

        # 构造 TTS 请求参数
        params = {
            "tex": text,
            "tok": token,
            "cuid": "my-tts-client",
            "ctp": 1,  # 固定为 1（网页端通常用 1）
            "lan": "zh",
            "spd": self.speed,
            "pit": self.pitch,
            "vol": 9,
            "per": self.voice_type
        }

        try:
            response = requests.post(
                "http://tsn.baidu.com/text2audio",
                params=params,
                headers={"Content-Type": "audio/mp3"}
            )

            if response.headers.get("Content-Type", "").startswith("audio/"):
                with open(filepath, "wb") as f:
                    f.write(response.content)
                self.history_data.append((text, filepath))
                self.log.info("语音合成成功，文件保存在：" + filepath)
                if callback:
                    callback(filepath)
                return filepath
            else:
                error = response.json()
                self.log.error(f"合成失败: {error.get('err_msg', '未知错误')}")
        except Exception as e:
            self.log.error(f"请求异常: {str(e)}")
        return None

    def long_text_synthesis(self, long_text, callback):
        """
        长文本合成：自动分句后逐句合成，并依次调用回调函数

        Args:
            long_text (str): 待合成长文本
            callback (function): 回调函数，格式为 callback(index, filepath)
        """
        self.stop_synthesis = False
        sentences = self._split_sentences(long_text)

        for idx, sentence in enumerate(sentences):
            if self.stop_synthesis:
                break
            # 每句合成后回调传入索引（从 1 开始）和生成的文件路径
            self.text_to_speech(sentence, lambda path, i=idx + 1: callback(i, path))
            time.sleep(0.2)  # 控制请求频率


# ---------------------- 音频播放辅助函数 ----------------------
def play_audio(filepath):
    """
    使用 pygame 播放给定音频文件

    Args:
        filepath (str): 音频文件路径
    """
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print("[ERROR] 播放音频失败:", e)


# ---------------------- 主流程示例 ----------------------
if __name__ == "__main__":
    # 加载配置
    configUtil.load_config()
    # 创建 BaiduTTS
    tts = BaiduTTS()

    # 示例 1：单句合成并播放
    print("单句合成示例：")
    tts.text_to_speech("欢迎使用语音合成系统", play_audio)

    time.sleep(2)  # 稍作等待

    # 示例 2：长文本合成后依次播放
    print("长文本合成示例：")
    long_text = (
        "这是一个长文本示例，演示如何自动分割长文本并进行分段合成。"
        "系统将根据标点符号和最大长度限制自动分句，确保合成效果自然流畅。"
    )
    tts.long_text_synthesis(long_text, lambda idx, path: play_audio(path))
