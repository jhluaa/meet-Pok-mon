#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import os
import websocket
import json
import time
import ssl

from utils import  server
from  utils.Thread import MyThreadFunc





class FunASR:
    # 初始化
    os.environ["LOCAL_ASR_IP"] = "127.0.0.1"
    os.environ["LOCAL_ASR_PORT"] = "10095"

    def __init__(self):
        # 构建 ws:// 或 wss:// 连接地址
        # 如果服务器是加密模式，需要使用 wss:// 并加 ssl 选项
        self.__URL = "ws://{}:{}".format(
            os.environ.get("LOCAL_ASR_IP"), os.environ.get("LOCAL_ASR_PORT")
        )
        self.__ws = None
        self.__connected = False
        self.__closing = False
        self.done = False
        self.finalResults = ""

        # 重连相关
        self.__reconnect_delay = 1
        self.__reconnecting = False

        # 多线程控制
        self.on_start_thread = None

        # 你可以在这里修改默认识别模式
        # 例如 offline/online/2pass
        self.default_mode = "2pass"

    # def on_message(self, ws, message):
    #     """
    #     收到服务器返回的识别结果。
    #     官方协议中，服务器返回的 JSON 形如:
    #       {"mode":"2pass-online","wav_name":"mic","text":"你好","is_final":false,...}
    #       或  {"mode":"2pass-offline","text":"你好啊","is_final":true,...}
    #     你可以在这里解析并做自定义处理
    #     """
    #     print("on_message:", message)
    #     self.finalResults = message
    #     self.done = True
    #
    #     if self.__closing:
    #         try:
    #             self.__ws.close()
    #         except Exception as e:
    #             print(e)
    import json

    def on_message(self, ws, message):
        try:
            # 先解析 JSON
            data = json.loads(message)
            # 获取 text 字段
            text = data.get("text", "")
            # 只打印 text
            print("on_message text:", text)
        except Exception as e:
            print("on_message error:", e)

    def on_close(self, ws, code, msg):
        self.__connected = False
        print("[FunASR] on_close:", msg)
        self.__ws = None
        self.__attempt_reconnect()

    def on_error(self, ws, error):
        if not isinstance(error, SystemExit):
            self.__connected = False
            print("### on_error:", error)
            self.__ws = None
            self.__attempt_reconnect()

    def __attempt_reconnect(self):
        if not self.__reconnecting:
            self.__reconnecting = True
            print("[FunASR] try reconnecting ...")
            while not self.__connected:
                time.sleep(self.__reconnect_delay)
                self.start()
                self.__reconnect_delay *= 2
            self.__reconnect_delay = 1
            self.__reconnecting = False

    def on_open(self, ws):
        self.__connected = True
        print("[FunASR] WebSocket connected.")

    def __connect(self):
        self.done = False
        self.__connected = False
        self.__closing = False
        websocket.enableTrace(False)

        self.__ws = websocket.WebSocketApp(
            self.__URL,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error,
        )
        self.__ws.on_open = self.on_open
        self.__ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def start(self):
        """
        外部调用，启动 WebSocket 连接。非阻塞，会在后台线程中执行。
        """
        try:
            if self.on_start_thread:
                self.on_start_thread.stop()
            self.on_start_thread = MyThreadFunc(func=self.__connect, args=[])
            self.on_start_thread.start()
        except Exception as e:
            print("### start:", e)

    def send_byte_array(self, audio_byte_array, wav_name="microphone"):
        """
        一次性发送：
          1) 初始 JSON (mode, is_speaking=true,...)
          2) 音频数据
          3) 结束 JSON (is_speaking=false)
        遵循官方文档的通信协议:
          https://github.com/alibaba-damo-academy/FunASR/blob/main/runtime/websocket/websocket_protocol.md
        """
        try:
            if not (self.__ws and self.__ws.sock and self.__ws.sock.connected):
                print("### send_byte_array: connection not ready!")
                return

            # (1) 发送首次通信 JSON
            # 官方示例: {"mode":"2pass","wav_name":"xxx","is_speaking":True,"wav_format":"pcm","chunk_size":[5,10,5],...}
            init_msg = {
                "mode": self.default_mode,   # "2pass", "online", or "offline"
                "wav_name": wav_name,
                "wav_format": "pcm",         # 你录音时就是PCM
                "is_speaking": True,
                "chunk_size": [5,10,5],      # 如果是2pass, chunk_size = [5,10,5]
                "audio_fs": 16000,           # 你的录音采样率
                "hotwords": "",              # 如果有热词,例如 '{"阿里巴巴":20}'
                "itn": True                  # 是否使用ITN
            }
            self.__ws.send(json.dumps(init_msg))

            # (2) 发送音频数据（bytes）
            self.__ws.send(audio_byte_array, opcode=websocket.ABNF.OPCODE_BINARY)

            # (3) 发送结束标志
            # 官方示例: {"is_speaking": false}
            stop_msg = {"is_speaking": False}
            self.__ws.send(json.dumps(stop_msg))

            # 等待服务器返回最终结果
            time.sleep(1.0)

        except Exception as e:
            print("### send_byte_array:", e)

    def end(self):
        """
        如果你需要手动关闭连接，可调用此方法
        """
        print("[FunASR] end() called, closing connection...")
        self.__closing = True
        self.__connected = False
        if self.__ws:
            try:
                self.__ws.close()
            except:
                pass
