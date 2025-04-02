#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import threading
from utils.detect_lip import DetectFaceAndLip
from utils.recorder import Recorder

def main():
    # 事件对象，用于线程间通信：一旦唇动检测认为“在说话”，就 set；否则 clear
    funasr_event = threading.Event()

    # 麦克风录音 & ASR 线程
    recorder = Recorder(funasr_event)
    threading.Thread(target=recorder.record_audio, daemon=True).start()

    # 唇动检测
    detectFaceAndLip = DetectFaceAndLip(funasr_event)
    detectFaceAndLip.detect_face_and_mouth()

if __name__ == "__main__":
    main()
