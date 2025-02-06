#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# sys.path.append(BASE_DIR)

# 配置文件
CONFIG_DIR = os.path.join(BASE_DIR, "resources", "config")
# 日志目录
LOG_DIR = os.path.join(BASE_DIR, "resources", "log")
# 下载文件临时目录
TEMP_DIR = os.path.join(BASE_DIR, "resources", "temp")
# yaml文件夹路径
YAML_DIR = os.path.join(BASE_DIR, "resources", "yaml")
# model文件夹路径
MODEL_DIR = os.path.join(BASE_DIR, "resources", "model")
# data文件夹路径
DATA_DIR = os.path.join(BASE_DIR, "resources", "data")
