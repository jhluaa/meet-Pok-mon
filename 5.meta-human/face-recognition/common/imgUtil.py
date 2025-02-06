#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import io
import requests
import numpy as np
import cv2
import re, base64
from PIL import Image


def is_http_url(s):
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if regex.match(s):
        return True
    else:
        return False


def is_base64_code(s):
    """Check s is Base64.b64encode"""
    if not isinstance(s, str) or not s:
        return "params s not string or None"

    if s.find(";base64,") > -1:
        return True

    _base64_code = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "+",
        "/",
        "=",
    ]
    _base64_code_set = set(_base64_code)  # 转为set增加in判断时候的效率
    # Check base64 OR codeCheck % 4
    code_fail = [i for i in s if i not in _base64_code_set]
    if code_fail or len(s) % 4 != 0:
        return False
    return True


def base64_to_ndarray(base64_data):
    """
    base64转imgArray
    :param base64_data:
    :return:
    """
    if base64_data:
        pos = base64_data.find(";base64,")
        pos = 0 if pos == -1 else pos + 8
        base64_data = base64_data[pos:]
    img_data = base64.b64decode(base64_data)
    image_stream = io.BytesIO(img_data)
    img = Image.open(image_stream)
    img_array = np.array(img)

    return img_array


def img_to_base64(img_array):
    # 传入图片为RGB格式numpy矩阵，传出的base64也是通过RGB的编码
    # img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)  # RGB2BGR，用于cv2编码
    encode_image = cv2.imencode(".jpg", img_array)[1]  # 用cv2压缩/编码，转为一维数组
    byte_data = encode_image.tobytes()  # 转换为二进制
    base64_str = base64.b64encode(byte_data).decode("ascii")  # 转换为base64
    return base64_str


def url_to_ndarray(url_data):
    res = requests.get(url_data, verify=False)
    content = res.content
    img = np.asarray(bytearray(content), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    return img
