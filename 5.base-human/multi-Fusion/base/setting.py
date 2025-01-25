#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# sys.path.append(BASE_DIR)


# 图片文件目录
MODEL_FILE = os.path.join(BASE_DIR, "resources", "weight", "v8l_0.pt")

# 配置文件
CONFIG_DIR = os.path.join(BASE_DIR, "resources", "config", "app.ini")
# 日志目录
LOG_DIR = os.path.join(BASE_DIR, "resources", "logs")
# 图片文件目录
IMAGE_DIR = os.path.join(BASE_DIR, "resources", "file", "image")
# 视频文件目录
VIDEO_DIR = os.path.join(BASE_DIR, "resources", "file", "video")
# yaml文件夹路径
YAML_DIR = os.path.join(BASE_DIR, "resources", "yaml")
# temp文件夹路径
TEMP_DIR = os.path.join(BASE_DIR, "resources", "temp")
# camera选取
camera_index = 0
# 模型路径
model_path = os.path.join(BASE_DIR, "resources", "model", "model.onnx")  # 构建相对路径
