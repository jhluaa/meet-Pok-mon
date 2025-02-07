#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
https://help.aliyun.com/zh/isi/developer-reference/sdk-for-python-1?spm=a2c4g.11186623.help-menu-30413.d_3_1_0_5.3e0b18faTIOOgg 开发文档
完整 TTS_ali 模块
此文件集成了：
  1. 依赖模块的重新实现（ALiNls、ali_tts_voice、EnumVoice、configUtil、setting、Log）
  2. 文本处理、长文本拆分、TTS 调用（调用阿里云接口）及缓存管理
  3. 基于 pygame 的音频播放管理

注意：部分参数（如 AppKey、Token）采用环境变量方式配置，实际使用时请确保正确设置。
"""

import os
import time
import math
import re
import threading
import requests
import pygame
from pypinyin import lazy_pinyin


# ---------------------- 重新实现依赖模块 ----------------------

# apikey Aliyun NLS, 阿里云智能语音服务
class ALiNls:
    def __init__(self):
        # 从环境变量获取AppKey和Token，若未设置则使用dummy值
        self.app_key = os.environ.get("ALI_NLS_APP_KEY", "yVgwkSuzSt7hi59l")
        self._dummy_token = os.environ.get("ALI_NLS_TOKEN", "a4ff17b1e7984004a37c242a6ef2868e")
        # 阿里云TTS服务地址
        self.TTS_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"

    def get_ali_token(self):
        return self._dummy_token


# 模拟 core.ali_tts_voice 模块及 EnumVoice
class DummyVoice:
    def __init__(self, voiceName):
        self.value = {"voiceName": voiceName}


def get_voice_of(soundType):
    # 简单实现：忽略 soundType，统一返回 "zhitian_emo"
    return DummyVoice("zhitian_emo")


# 此处将 get_voice_of 和 EnumVoice 集中定义
class ali_tts_voice:
    get_voice_of = staticmethod(get_voice_of)


class EnumVoice:
    ZHI_MI_EMO = DummyVoice("zhitian_emo")


# 模拟 public.common.configUtil
class configUtil:
    # 配置示例：soundType 及唤醒词列表
    voice_config = {
        "soundType": "default",
        "wakenWords": ["你好", "小助手"]
    }

    @staticmethod
    def load_config():
        print("加载配置（模拟）...")


# 模拟 public.common.setting
class setting:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 生成音频文件保存目录：BASE_DIR/resources/temp
    TEMP_DIR = os.path.join(BASE_DIR, "resources", "temp")
    # 确保目录存在
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


# 模拟 public.module.Log
class Log:
    def error(self, message):
        print("ERROR:", message)

    def info(self, message):
        print("INFO:", message)


# ---------------------- TTS 核心功能实现 ----------------------

class AliTTS:
    """
    AliTTS 实现了文本转语音的核心流程：
      1. 文本预处理与句子拆分
      2. 调用阿里云 TTS 接口合成语音文件
      3. 结果缓存（避免重复合成相同文本）
    """

    def __init__(self):
        self._tts_service = ALiNls()  # 用于获取 TTS 服务 URL、AppKey 及 Token
        self._cache = {}  # 缓存格式： { (voice, text): audio_file_path }
        self._stop_long_synthesis = False  # 控制长文本逐句合成时的中断标志
        self._logger = Log()

    def _get_voice_name(self):
        """根据配置返回实际使用的语音型号"""
        voice_conf = configUtil.voice_config.get("soundType")
        voice_type = ali_tts_voice.get_voice_of(voice_conf)
        if voice_type is not None:
            return voice_type.value["voiceName"]
        return EnumVoice.ZHI_MI_EMO.value["voiceName"]

    def _find_cache(self, voice, text):
        """尝试从缓存中获取已合成音频的文件路径"""
        return self._cache.get((voice, text))

    def _save_cache(self, voice, text, file_path):
        """将合成结果缓存起来"""
        self._cache[(voice, text)] = file_path

    def get_audio_file(self, text):
        """
        根据输入文本合成语音并返回音频文件路径（先从缓存中查找）
        """
        voice = self._get_voice_name()
        cached = self._find_cache(voice, text)
        if cached:
            return cached
        file_path = self._create_audio_file(text, voice)
        if file_path:
            self._save_cache(voice, text, file_path)
        return file_path

    def synthesize_text(self, text, callback):
        """
        文字转语音：合成文本后通过回调返回音频文件路径

        Args:
            text (str): 待合成的文本
            callback (function): 回调函数，格式为 callback(index, file_path)
                                   index==1 表示立即播放
        """
        voice = self._get_voice_name()
        cached = self._find_cache(voice, text)
        if cached:
            audio_path = cached
        else:
            audio_path = self._create_audio_file(text, voice)
            self._save_cache(voice, text, audio_path)
        callback(1, audio_path)

    def synthesize_long_text(self, long_text, callback, sentence_index=1):
        """
        长文本合成：将长文本拆分为多个句子依次合成后，通过回调返回每句音频文件

        Args:
            long_text (str): 长文本字符串
            callback (function): 回调函数，格式为 callback(sentence_index, file_path)
            sentence_index (int): 起始句子编号
        """
        formatted_text = self.format_text(long_text)
        self._stop_long_synthesis = False
        voice = self._get_voice_name()
        sentences = self._split_sentences(formatted_text)
        for sentence in sentences:
            if self._stop_long_synthesis:
                break
            cached = self._find_cache(voice, sentence)
            if cached:
                audio_path = cached
            else:
                audio_path = self._create_audio_file(sentence, voice)
                self._save_cache(voice, sentence, audio_path)
            callback(sentence_index, audio_path)
            sentence_index += 1

    def synthesize_sentence(self, text, callback, sentence_index):
        """
        单句合成：仅合成文本中的第一句，剩余文本留待后续处理

        Args:
            text (str): 可能包含多个句子的文本
            callback (function): 回调函数，格式为 callback(sentence_index, file_path)
            sentence_index (int): 当前句子编号

        Returns:
            tuple: (本次合成的句子, 更新后的句子编号)
        """
        voice = self._get_voice_name()
        sentences = self._split_sentences(text)
        if sentences:
            first_sentence = sentences[0]
            sentence_index += 1
            cached = self._find_cache(voice, first_sentence)
            if cached:
                audio_path = cached
            else:
                audio_path = self._create_audio_file(first_sentence, voice)
                self._save_cache(voice, first_sentence, audio_path)
            callback(sentence_index, audio_path)
            return first_sentence, sentence_index
        return "", sentence_index

    def _create_audio_file(self, text, voice):
        """
        调用阿里云 TTS 接口合成语音，并将生成的音频保存到文件中

        Args:
            text (str): 待合成的文本（经过清洗）
            voice (str): 语音型号

        Returns:
            str: 音频文件的完整路径
        """
        clear_text = self._sanitize_text(text)
        if not clear_text:
            return None

        url = self._tts_service.TTS_URL
        fmt = "wav"
        timestamp = int(time.time() * 1000)
        # 如果文本中包含唤醒词，则使用特殊前缀
        prefix = "echo" if self._contains_wake_word(clear_text) else "sample"
        file_name = f"{prefix}_{timestamp}.{fmt}"
        audio_file_path = os.path.join(setting.TEMP_DIR, file_name)
        params = {
            "appkey": self._tts_service.app_key,
            "token": self._tts_service.get_ali_token(),
            "text": clear_text,
            "format": fmt,
            "sample_rate": "16000",
            "voice": voice,
        }
        headers = {"Content-Type": "application/json"}

        try:
            start_time = time.time()
            response = requests.post(url=url, params=params, headers=headers)
            if response.status_code == 200:
                elapsed = math.floor((time.time() - start_time) * 1000)
                print(f"[{clear_text}] 合成成功，耗时: {elapsed} ms")
                with open(audio_file_path, "wb") as fd:
                    fd.write(response.content)
            else:
                self._logger.error(f"[{clear_text}] TTS 响应状态异常: {response.status_code}, 字数: {len(clear_text)}")
        except requests.RequestException as e:
            self._logger.error(f"TTS 请求异常: {e}")
        except IOError as e:
            self._logger.error(f"文件操作异常: {e}")
        except Exception as e:
            self._logger.error(f"其他异常: {e}")
        return audio_file_path

    def _contains_wake_word(self, text):
        """
        判断文本中是否包含预设的唤醒词（仅检测前两个）

        Args:
            text (str): 待检测文本

        Returns:
            bool: 包含返回 True，否则 False
        """
        wake_words = configUtil.voice_config.get("wakenWords", [])
        if wake_words:
            # 只检测前两个
            target_words = wake_words[:2]
            target_pinyin = lazy_pinyin(target_words)
            target_len = len(target_words)
            for i in range(len(text) - target_len + 1):
                segment = text[i: i + target_len]
                if lazy_pinyin(segment) == target_pinyin:
                    return True
        return False

    def get_text_by_audio(self, file_path):
        """
        根据音频文件路径查找缓存中对应的文本

        Args:
            file_path (str): 音频文件路径

        Returns:
            str: 合成时使用的原始文本，若未缓存则返回空字符串
        """
        for (voice, txt), path in self._cache.items():
            if path == file_path:
                return txt
        return ""

    def _split_sentences(self, org_text, min_length=10, pattern=r"[,，！!：。？\\?]"):
        """
        利用标点拆分文本为句子，只有累计长度超过 min_length 时才分割

        Args:
            org_text (str): 原始文本
            min_length (int): 句子最小长度
            pattern (str): 拆分所用正则表达式

        Returns:
            list: 句子列表
        """
        regex = re.compile(pattern)
        start = 0
        sentences = []
        current_sentence = ""
        try:
            for match in regex.finditer(org_text):
                end = match.end()
                current_sentence += org_text[start:end]
                if len(current_sentence) > min_length:
                    sentences.append(current_sentence)
                    current_sentence = ""
                start = end
            # 处理剩余部分
            remainder = org_text[start:]
            if remainder:
                current_sentence += remainder
            if current_sentence:
                sentences.append(current_sentence)
        except Exception as e:
            print("句子拆分异常:", e)
        return sentences

    def _sanitize_text(self, txt):
        """
        清理文本：去除所有空格、换行符及 <br/> 标签

        Args:
            txt (str): 原始文本

        Returns:
            str: 清理后的文本
        """
        txt = re.sub(r"\s+", "", txt)
        txt = re.sub(r"<br\s*/?>", "", txt)
        return txt.strip()

    def format_text(self, org_text):
        """
        格式化长文本，将空白字符替换为中文逗号，同时保留标点后间隔

        Args:
            org_text (str): 原始长文本

        Returns:
            str: 格式化后的文本
        """
        punct_pattern = r"[.,，！!：。？\\?]"
        tmp = re.sub(r"\s+", "|", org_text).strip("|")
        tmp = re.sub(r"(?<=[" + re.escape(punct_pattern) + r"])\|", "", tmp)
        return tmp.replace("|", "，")


# ---------------------- 音频播放管理 ----------------------

# 全局播放队列，用于排队播放多个音频
_play_queue = []


def clear_play_queue():
    global _play_queue
    _play_queue = []


def add_to_queue(file_path):
    global _play_queue
    _play_queue.append(file_path)


def get_next_from_queue():
    global _play_queue
    if _play_queue:
        return _play_queue.pop(0)
    return None


def is_queue_empty():
    return len(_play_queue) == 0


def play_audio(index, file_path):
    """
    播放音频的回调函数

    Args:
        index (int): 播放序号，1 表示立即播放；其他视为加入播放队列
        file_path (str): 合成后的音频文件路径
    """
    if index == 1:
        print("播放音频...")
        clear_play_queue()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
    else:
        add_to_queue(file_path)
    # 若 index==2，则启动后台线程监控音频播放结束
    if index == 2:
        threading.Thread(target=monitor_playback, daemon=True).start()


def monitor_playback():
    """
    监控当前音频播放状态，待播放完毕后自动播放队列中的下一个音频
    """
    while True:
        time.sleep(0.5)
        if not pygame.mixer.music.get_busy():
            if is_queue_empty():
                break
            next_file = get_next_from_queue()
            print("继续播放:", next_file)
            pygame.mixer.music.load(next_file)
            pygame.mixer.music.play()
    print("全部音频播放结束！")


# ---------------------- 主流程示例 ----------------------

if __name__ == "__main__":
    # 模拟加载配置（在 configUtil.load_config 中已实现打印提示）
    configUtil.load_config()

    # 初始化 pygame 播放器
    pygame.mixer.init()

    # 创建 AliTTS 实例
    tts_manager = AliTTS()

    # 播报文本
    sample_text = """我们谈研发效能的时候，我们在谈些什么？这个议题被抛出来，有人讨论，是因为存在问题，问题就在于实际的研发效率，已经远低于预期了。
    企业初创的时候，一个想法从形成到上线，一个人花两个小时就完成了，而当企业发展到数千人的时候，类似事情的执行，往往需要多个团队，花费好几周才能完成。
    这便造成了鲜明的对比，而这一对比产生的印象，对于没有深入理解软件工程的人来说，显得难以理解，可又往往无计可施。
    细心的读者会留意到，前文我既用了“效能”一词，也用了“效率”一词。这是为了做严谨的区分，效能往往是用来衡量产品的经济绩效，而效率仅仅是指提升业务响应能力，提高吞吐，降低成本。
    这里的定义引用了乔梁的《如何构建高效能研发团队》课程材料，本文并不讨论产品开发方法，因此后面的关注都在“效率”上。本世纪 10 年代，早期的互联网从业者开发简易网站的时候，只需要学会使用 Linux、Apache、MySql、PHP（Perl）即可，这套技术有一个好记的名字：LAMP。
    可今天，在一个大型互联网公司工作的开发者，需要理解的技术栈上升了一个数量级，例如分布式系统、微服务、Web 开发框架、DevOps 流水线、容器等云原生技术等等。
    如果仅仅是这些复杂度还好说，毕竟都是行业标准的技术，以开发者的学习能力，很快就能掌握。
    令人生畏的复杂度在于，大型互联网公司都有一套或者多套软件系统，这些软件系统的规模往往都在百万行以上，质量有好有坏（坏者居多），而开发者必须基于这些系统开展工作。这个时候必须承担非常高的认知负荷，而修改软件的时候也会面临破坏原有功能的巨大风险，而风险的增高就必然导致速度的降低。
    因此研发效率的大幅降低，其中一个核心因素就是软件复杂度的指数上升。"""

    sentence_index = 0

    # 循环逐句合成播放，每次合成文本中的第一句，直至文本全部处理完毕
    while True:
        sentence, sentence_index = tts_manager.synthesize_sentence(sample_text, play_audio, sentence_index)
        # 只替换第一次出现的该句，防止误删重复文本
        sample_text = sample_text.replace(sentence, "", 1).strip()
        if not sample_text:
            break
        time.sleep(0.5)
