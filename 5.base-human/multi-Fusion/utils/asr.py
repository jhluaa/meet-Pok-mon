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
    os.environ["LOCAL_ASR_IP"] = "localhost"
    os.environ["LOCAL_ASR_PORT"] = "8080"

    def __init__(self):
        self.__URL = "ws://{}:{}".format(
            os.environ.get("LOCAL_ASR_IP"), os.environ.get("LOCAL_ASR_PORT")
        )
        self.__ws = None
        self.__connected = False
        self.__frames = []
        self.__state = 0
        self.__closing = False
        self.__task_id = ""
        self.done = False
        self.finalResults = ""
        self.__reconnect_delay = 1
        self.__reconnecting = False
        self.on_start_thread = None
        self.on_open_thread = None

    def __on_msg(self):
        pass

    # 收到websocket消息的处理
    def on_message(self, ws, message):
        try:
            print("on_message:", message)
            self.finalResults = message
            self.done = True
            # wsa_server.get_web_instance().add_cmd({"panelMsg": self.finalResults})
            # if not configUtil.human_config["interact"]["playSound"]:  # 非展板播放
            #     content = {
            #         "Topic": "Unreal",
            #         "Data": {"Key": "log", "Value": self.finalResults},
            #     }
            #     wsa_server.get_instance().add_cmd(content)
            self.__on_msg()

        except Exception as e:
            print("### on_message:", e)

        if self.__closing:
            try:
                self.__ws.close()
            except Exception as e:
                print(e)

    # 收到websocket关闭的处理
    def on_close(self, ws, code, msg):
        self.__connected = False
        print("on_close", msg)
        self.__ws = None
        self.__attempt_reconnect()

    # 收到websocket错误的处理
    def on_error(self, ws, error):
        if not isinstance(error, SystemExit):
            self.__connected = False
            print("### on_error:", error)
            self.__ws = None
            self.__attempt_reconnect()

    # 重连
    def __attempt_reconnect(self):
        if not self.__reconnecting:
            self.__reconnecting = True
            print("尝试重连funasr...")
            while not self.__connected:
                time.sleep(self.__reconnect_delay)
                self.start()
                self.__reconnect_delay *= 2
            self.__reconnect_delay = 1
            self.__reconnecting = False

    # 收到websocket连接建立的处理
    def on_open(self, ws):
        self.__connected = True
        # print("连接上了！！！")
        # if self.on_open_thread:
        #     self.on_open_thread.stop()
        # self.on_open_thread = MyThreadFunc(func=self.__run, args=[ws])
        # self.on_open_thread.start()

    def __run(self, ws):
        while self.__connected:
            try:
                if len(self.__frames) > 0:
                    frame = self.__frames[0]
                    self.__frames.pop(0)
                    if type(frame) == dict:
                        ws.send(json.dumps(frame))
                    elif type(frame) == bytes:
                        ws.send(frame, websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print("### __run:", e)
                break
            time.sleep(0.04)

    def __connect(self):
        self.finalResults = ""
        self.done = False
        self.__connected = False
        self.__frames.clear()
        self.__closing = False
        websocket.enableTrace(False)
        self.__ws = websocket.WebSocketApp(
            self.__URL,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error,
            subprotocols=["binary"],
        )
        self.__ws.on_open = self.on_open
        self.__ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def add_frame(self, frame):
        self.__frames.append(frame)

    def clear_frame(self):
        self.__frames.clear()

    def send(self, buf):
        self.__frames.append(buf)

    def send_url(self, url):
        frame = {"url": url}
        self.__ws.send(json.dumps(frame))

    def send_byte_array(self, byte_array):
        try:
            if self.__ws and self.__ws.sock.connected:
                self.__ws.send(byte_array, opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            print("### send_byte_array:", e)

    def start(self):
        try:
            if self.on_start_thread:
                self.on_start_thread.stop()
            self.on_start_thread = MyThreadFunc(func=self.__connect, args=[])
            self.on_start_thread.start()
            # data = {"vad_need": False, "state": "StartTranscription"}
            # self.add_frame(data)
        except Exception as e:
            print("### start:", e)

    def end(self):
        if self.__connected:
            try:
                for frame in self.__frames:
                    self.__frames.pop(0)
                    if type(frame) == dict:
                        self.__ws.send(json.dumps(frame))
                    elif type(frame) == bytes:
                        self.__ws.send(frame, websocket.ABNF.OPCODE_BINARY)
                    time.sleep(0.4)
                self.__frames.clear()
                # frame = {"vad_need": False, "state": "StopTranscription"}
                # self.__ws.send(json.dumps(frame))
            except Exception as e:
                print("### end:", e)
        self.__closing = True
        self.__connected = False
