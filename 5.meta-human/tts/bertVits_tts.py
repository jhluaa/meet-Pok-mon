#!/usr/bin/env python
# coding: utf-8

import os
import re
import time
import requests
from datetime import datetime

import cn2an
import phonenumbers


def replace_digits_with_chinese(raw_text: str) -> str:

    # 简单把纯数字整体转成中文数字，例如 "123" -> "一二三"
    def digit_to_chinese(match):
        return ''.join(cn2an.transform(d, "an2cn") for d in match.group())

    processed = re.sub(r"\d+", digit_to_chinese, raw_text)
    return processed


class BertVITS2tts:
    """ 
    通过 HTTP 请求将文本发送给服务器，并保存音频文件到本地。
    """

    def __init__(self, service_url: str = None):
        self.service_url = service_url or os.environ.get("local_bert_vits2_url")
        if not self.service_url:
            self.service_url = "http://localhost:23456/voice/bert-vits2?"  # 默认值

        # 记录合成过的文本音频文件路径，避免多次相同请求
        self._synthesis_cache = {}
        # 标记是否在合成时需要中
        self.interrupt_long_text_synthesis = False

        print("[INFO]Bert-VITS2服务地址:", self.service_url)

    @staticmethod
    def split_text_with_punctuations(
            text: str, max_length: int = 15, pattern: str = r"[,，！!：。？\?]"
    ) -> list:
        """
        根据标点符号（或传入的正则 pattern）分割文本；
        如果单句超过 max_length，也会自动拆分。
        """
        reg = re.compile(pattern)
        start = 0
        result = []
        buffer_sentence = ""

        for match_obj in reg.finditer(text):
            end = match_obj.end()
            fragment = text[start:end]
            buffer_sentence += fragment
            if len(buffer_sentence) > max_length:
                result.append(buffer_sentence)
                buffer_sentence = ""
            start = end

        # 处理最后剩余内容（可能没有标点）
        last_part = text[start:]
        if last_part:
            buffer_sentence += last_part

        if buffer_sentence.strip():
            result.append(buffer_sentence)

        return result

    def generate_audio_single_text(self, text: str) -> str:
        """
        对单段文本进行语音合成，返回生成的本地音频文件路径。
        会先检查是否在缓存中（避免重复合成）。
        """
        text = text.strip()
        if not text:
            return ""

        # 如果已经合成过同样的文本，直接返回缓存结果
        if text in self._synthesis_cache:
            return self._synthesis_cache[text]

        # 生成文件名
        file_name = f"bertvits_{int(time.time() * 1000)}.wav"
        file_path = os.path.join(".", file_name)

        # 发起请求并保存音频文件
        self._request_and_save_audio(text, file_path)

        # 缓存结果
        self._synthesis_cache[text] = file_path

        return file_path

    def generate_audio_for_long_text(
            self, text: str, callback, start_index: int = 1
    ) -> None:
        """
        把长文本切分成多个小句，每合成一段后通过 callback(index, file_path) 返回。
        可用于“边合成边播放”或“分段处理”。
        """
        self.interrupt_long_text_synthesis = False
        fragments = self.split_text_with_punctuations(text)

        idx = start_index
        for fragment in fragments:
            if self.interrupt_long_text_synthesis:
                print("[INFO] 合成已被中断。")
                break

            fragment = fragment.strip()
            if not fragment:
                continue

            audio_path = self.generate_audio_single_text(fragment)
            callback(idx, audio_path)
            idx += 1

    def generate_audio_for_first_sentence(
            self, text: str, callback, current_index: int
    ) -> tuple:
        """
        只取文本拆分后的第一小句进行合成，其余由调用方自行决定如何处理。
        返回值： (合成的第一句, 更新后的索引)
        """
        fragments = self.split_text_with_punctuations(text)
        if not fragments:
            return "", current_index

        first_fragment = fragments[0].strip()
        if not first_fragment:
            return "", current_index

        audio_path = self.generate_audio_single_text(first_fragment)
        current_index += 1

        callback(current_index, audio_path)
        return first_fragment, current_index

    def _request_and_save_audio(self, text: str, output_path: str):
        """
        发送 HTTP请求给Bert-VITS2 服务，把合成的音频数据保存到 output_path。
        """
        # 可以在这里处理数字转中文、去掉特殊符号等自定义逻辑
        processed_text = replace_digits_with_chinese(text)
        processed_text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9,。，.:+]", " ", processed_text)

        print(f"[TTS] 即将请求合成文本: {processed_text}")
        start_time = datetime.now()

        request_url = f"{self.service_url}text={processed_text}"

        try:
            response = requests.get(request_url, timeout=30)
            if response.status_code == 200:
                with open(output_path, "wb") as fd:
                    fd.write(response.content)
                print("[TTS] 合成成功 ->", output_path)
            else:
                print("[TTS] 服务响应错误, HTTP状态码:", response.status_code)
        except Exception as exc:
            print("[TTS] 请求合成出现异常:", str(exc))

        end_time = datetime.now()
        print("[TTS] 开始合成时间:", start_time.strftime("%Y-%m-%d %H:%M:%S"))
        print("[TTS] 结束合成时间:", end_time.strftime("%Y-%m-%d %H:%M:%S"))


def demo_audio_play_callback(index: int, audio_file: str):
    """
    用于演示的回调函数示例：打印信息 + 使用 pygame 播放音频。
    如果不需要播放，可自行修改此函数逻辑。
    """
    if not audio_file:
        print(f"[CALLBACK] 第{index}段合成音频为空。")
        return

    print(f"[CALLBACK] 第{index}段合成完毕, 音频路径: {audio_file}")

    #pygame播放
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except ImportError:
        print("[WARN] 未安装 pygame，无法播放音频。只做文件输出。")


if __name__ == "__main__":
    tts_url = os.environ.get("local_bert_vits2_url") or "http://localhost:23456/voice/bert-vits2?"
    tts = BertVITS2tts(tts_url)
    sample_text_long = """\
今天天气非常好，适合外出游玩，
可以试试看多句连续合成，这里多写几句话测试一下。
BertVITS2 效果不错吧？
"""
    print("========== [DEMO] 测试长文本多句合成 ==========")
    tts.generate_audio_for_long_text(sample_text_long, demo_audio_play_callback, start_index=1)
    # 测试：只合成第一句
    sample_text_single = "你好，这是另外一段文本，用来演示只合成并播放第一句。"
    print("\n========== [DEMO] 测试只合成第一句 ==========")
    first_sentence, idx = tts.generate_audio_for_first_sentence(sample_text_single, demo_audio_play_callback, 0)
    print("[INFO] 被抽取出来的第一句:", first_sentence)
    print("[INFO] 当前句子序号:", idx)
