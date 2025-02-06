#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import time

import cv2
import os, io
import base64
import numpy as np
from tensorboard.plugins.image.summary import image

from common import setting, Log, imgUtil
from deepface import DeepFace
from PIL import Image

log = Log()

DeepFace.build_model("Facenet512")  # 只加载一次模型


def crop_faces(img_ndarray):
    # 使用 DeepFace 检测并裁剪人脸
    base64_faces = []
    try:
        try:
            detected_faces = DeepFace.extract_faces(
                img_ndarray,
                detector_backend="mtcnn",
                expand_percentage=30,
                align=True,
            )
        except:
            raise Exception("无法检测到人脸")
        for i, face in enumerate(detected_faces):
            # Normalize the face image to 0-255 range and convert to uint8
            face_img_array = face["face"]
            face_img_array = (
                (face_img_array - face_img_array.min())
                * (255 / (face_img_array.max() - face_img_array.min()))
            ).astype(np.uint8)
            face_img = Image.fromarray(face_img_array, "RGB")
            buffered = io.BytesIO()
            face_img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_faces.append(img_base64)
    except Exception as e:
        log.error(f"【crop_faces】{e}")
    return base64_faces


def verify(images):
    # img1_path = save_temp_image(images[0], prefix="face_1")
    # img2_path = save_temp_image(images[1], prefix="face_2")
    try:
        result = DeepFace.verify(
            images[0],
            images[1],
            model_name="Facenet512",
            threshold=0.39,
            detector_backend="mtcnn",
            normalization="Facenet2018",
            expand_percentage=10,
        )
        log.info(result)
        # 计算裁剪区域的边界
        left = result["facial_areas"]["img2"]["x"]
        upper = result["facial_areas"]["img2"]["y"]
        right = left + result["facial_areas"]["img2"]["w"]
        lower = upper + result["facial_areas"]["img2"]["h"]
        # 裁剪图片
        cropped_img = Image.fromarray(images[1]).crop((left, upper, right, lower))
        # 将裁剪后的图像保存到内存缓冲区
        buffered = io.BytesIO()
        cropped_img.save(buffered, format="JPEG")
        # 将图像转换为 Base64 编码
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return result["verified"], img_base64
    except Exception as e:
        log.error(f"【verify】{e}")
        return False


def save_temp_image(image_array, prefix="temp_image"):
    """
    将ndarray格式的图像保存到临时文件，并返回文件路径
    """
    if not os.path.exists(setting.TEMP_DIR):
        os.mkdir(setting.TEMP_DIR)
    tempfile = os.path.join(setting.TEMP_DIR, prefix + ".jpg")
    cv2.imwrite(tempfile, image_array)
    return tempfile


if __name__ == "__main__":

    # img1_path = cv2.imread()
    img2_path = cv2.imread(
        "/data/gitlab/base-digital-human/face-recognition/faces/1.jpg"
    )
    # image = []
    # image.append(img1_path)
    # image.append(img2_path)
    # a, b = verify(image)
    # print(a)
    # print(b)
    # img2_path = "resources/temp/face_test_4.jpg"
    # result = DeepFace.verify(
    #     img1_path,
    #     img2_path,
    #     model_name="Facenet512",
    #     threshold=0.39,
    #     detector_backend="mtcnn",
    #     normalization="Facenet2018",
    #     expand_percentage=10 #像素
    # )
    # print(result)

    # #存储图像
    #     # # 读取 JPG 图片
    #     # # image_path = "/data/gitlab/base-digital-human/face-recognition/resources/news/3.jpg"
    # image_ndarray = cv2.imread(img1_path)

    cropped_faces = crop_faces(img2_path)
    print(cropped_faces[0])
    # 遍历并保存每张提取的人脸图片
    for i, face_base64 in enumerate(cropped_faces):
        # 将 Base64 解码为图像字节数据
        img_data = base64.b64decode(face_base64)
        # 将图像字节数据转为 NumPy 数组
        np_img = np.frombuffer(img_data, np.uint8)
        face_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)  # 转换为OpenCV图像
        # 保存提取的人脸图片
        saved_path = save_temp_image(face_img, prefix=f"face_{i + 1}")
        print(f"Saved face {i + 1} at: {saved_path}")
