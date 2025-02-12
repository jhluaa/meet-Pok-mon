#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import threading
from utils.detect_lip import DetectFaceAndLip
from utils.recorder import  Recorder
from base import myUtil


def main():

    # 创建事件对象，用于线程间通信
    funasr_event = threading.Event()
    recorder = Recorder(funasr_event)
    # 启动录音线程
    threading.Thread(target=recorder.record_audio).start()

    # 唇动检测，传入事件对象
    detectFaceAndLip = DetectFaceAndLip(funasr_event)
    # 打开摄像头，启动人脸检测
    detectFaceAndLip.detect_face_and_mouth()


if __name__ == "__main__":
    main()
