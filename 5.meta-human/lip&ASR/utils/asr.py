#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import os
import websocket
import json
import time
import ssl

from utils import server
from utils.Thread import MyThreadFunc

class FunASR:
    # 初始化
    os.environ["LOCAL_ASR_IP"] = "127.0.0.1"
    os.environ["LOCAL_ASR_PORT"] = "10096"

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

        #  识别模式: offline / online / 2pass
        self.default_mode = "2pass"

    def on_message(self, ws, message):
        """
        只在最终结果时打印识别的完整句子
        对 2pass 模式而言，一般会有一条 "2pass-offline" + is_final=true 的消息
        """
        try:
            data = json.loads(message)
            text = data.get("text", "")
            mode_val = data.get("mode", "")
            is_final = data.get("is_final", False)

            # 你也可以先行调试：print("Debug Received:", data)
            # 如果发现在实际环境中并没有 is_final=true，则需要根据具体返回再改写

            # 判断：只有在 "2pass-offline" + is_final=true 时才算最终结果
            if mode_val.endswith("-offline") and is_final:
                print("[FunASR] Final recognized text:", text)
                self.finalResults = text
                self.done = True

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
            init_msg = {
                "mode": self.default_mode,   # "2pass", "online", or "offline"
                "wav_name": wav_name,
                "wav_format": "pcm",
                "is_speaking": True,
                "chunk_size": [5, 10, 5],    # 若是 2pass，可用 [5,10,5]
                "audio_fs": 16000,
                "hotwords": "",
                "itn": True
            }
            self.__ws.send(json.dumps(init_msg))

            # (2) 发送音频数据（bytes）
            self.__ws.send(audio_byte_array, opcode=websocket.ABNF.OPCODE_BINARY)

            # (3) 发送结束标志
            stop_msg = {"is_speaking": False}
            self.__ws.send(json.dumps(stop_msg))

            # 等待服务器返回最终结果 (视实际情况可调整)
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
