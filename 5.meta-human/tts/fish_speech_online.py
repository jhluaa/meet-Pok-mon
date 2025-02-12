import os
import time
import pygame
from fish_audio_sdk import Session, TTSRequest, ReferenceAudio
import re
from pydub import AudioSegment

#国内无法调用
class TTSConfig:
    """
    TTS 配置类，可根据需要调整各项参数
    """
    CACHE_DIR = "audio_cache"
    OUTPUT_FORMAT = "mp3"  # 音频格式
    # 使用参考示例中的发音人 ID
    VOICE_NAME = "e80ea225770f42f79d50aa98be3cedfc"  # 官网模型id 可以训练自己的声音


class Speech:
    def __init__(self, config=TTSConfig):
        """
        初始化TTS客户端，设置API URL、缓存目录和默认发音人
        """
        self.config = config
        self.history_data = []  # 缓存格式：(voice_name, text, file_path)
        self.cache_dir = config.CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.voice_type = config.VOICE_NAME

        # 使用 Session 初始化 TTS 客户端，传入 token
        self.session = Session("7acd296631f24c9d9616eec1ff008916")

    def get_history(self, voice_name, text):
        """
        检查缓存中是否已合成过相同文本，返回音频文件路径
        """
        for data in self.history_data:
            if data[0] == voice_name and data[1] == text:
                return data[2]
        return None

    def get_text_synthetic_audio_file(self, text):
        """
        获取文本对应的合成语音文件，优先检查缓存
        """
        voice_name = self.voice_type
        history_path = self.get_history(voice_name, text)
        if history_path:
            return history_path
        return self.create_audio_file(text, voice_name)

    def text_synthetic_audio(self, text, callback):
        """
        将文本合成为语音文件并通过回调函数处理
        """
        voice_name = self.voice_type
        history_path = self.get_history(voice_name, text)
        if not history_path:
            history_path = self.create_audio_file(text, voice_name)
        callback(1, history_path)

    def create_audio_file(self, text, voice_name):
        """
        调用API合成语音，并将返回的音频数据保存为 MP3 文件，同时缓存结果
        """
        normalized_text = self.clean_text(text)
        if not normalized_text:
            return None

        file_name = f"sample_{int(time.time() * 1000)}.{self.config.OUTPUT_FORMAT}"
        audio_file_path = os.path.join(self.cache_dir, file_name)

        # 创建 TTS 请求，使用参考示例中的 reference_id 和待合成文本
        tts_request = TTSRequest(
            text=normalized_text,  # 要合成的文本
            reference_id=self.voice_type  # 发音人 ID
        )

        try:
            with open(audio_file_path, "wb") as f:
                # 直接使用 Session.tts() 获取音频数据流
                for chunk in self.session.tts(tts_request):
                    f.write(chunk)
                self.history_data.append((voice_name, text, audio_file_path))
        except Exception as e:
            print(f"Error during TTS synthesis: {e}")

        return audio_file_path

    @staticmethod
    def clean_text(text):
        """
        清理文本：去除所有空格和换行符
        """
        return "".join(text.split())

    @staticmethod
    def split_long_sentence(text, max_length=50, pattern=r"[，。？！]"):
        """
        按照标点分割长文本为多个句子
        """
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def long_text_to_synthetic_audio(self, long_text, callback, sentence_index=1):
        """
        对长文本进行分句处理，并依次合成每句话的语音
        """
        sentences = self.split_long_sentence(long_text)
        for sentence in sentences:
            file_path = self.get_text_synthetic_audio_file(sentence)
            callback(sentence_index, file_path)
            sentence_index += 1
 

def convert_mp3_to_wav(mp3_path):
    """
    使用 pydub 将 MP3 转换为 WAV 格式
    """
    sound = AudioSegment.from_mp3(mp3_path)
    wav_path = mp3_path.replace(".mp3", ".wav")
    sound.export(wav_path, format="wav")
    return wav_path


def play_sound(index, file_path):
    """
    回调函数：原本用于播放音频，现在只保存文件，并打印提示信息
    """
    if index == 1:
        print("Audio file saved:", file_path)
        # 以下播放代码注释掉，不进行播放
        # wav_path = convert_mp3_to_wav(file_path)  # 转换 mp3 为 wav
        # pygame.mixer.music.load(wav_path)
        # pygame.mixer.music.play()
    else:
        print(f"Queued file: {file_path}")


if __name__ == "__main__":
    # 如果不需要播放音频，可注释掉 pygame 播放模块初始化
    # pygame.mixer.init()

    # 初始化 Speech 对象
    speech = Speech()

    text = "我是孙笑川我是川吧之王，我最喜欢玩宝可梦。"

    # 长文本转语音示例（生成音频文件并保存，不播放）
    speech.long_text_to_synthetic_audio(text, play_sound)
