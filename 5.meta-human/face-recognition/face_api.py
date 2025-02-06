#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from flask import Flask, jsonify
from flask_cors import CORS
from common import Log, imgUtil
from gevent import pywsgi

import flask
import main
import cv2

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app, resources=r"/*")


log = Log()


@app.route("/api/face/cut", methods=["POST"])
def cut_face():
    """
    人脸识别
    接口参数：
    (必填，str)image：图片的base64或url

    :return:
    """
    try:
        json_data = flask.request.get_json(force=True)
        img_data = json_data["image"]
        if imgUtil.is_base64_code(img_data):
            origin_img = imgUtil.base64_to_ndarray(img_data)
        if imgUtil.is_http_url(img_data):
            origin_img = imgUtil.url_to_ndarray(img_data)
        img_bgr = cv2.cvtColor(origin_img, cv2.COLOR_RGB2BGR)
        base64_faces = main.crop_faces(img_bgr)
        return jsonify(code=0, data=base64_faces, msg="success")
    except Exception as e:
        log.error(f"【cut_face】{e}")
        msg = f"【cut_face】{e}"
        return jsonify(code=-1, data=None, msg=msg)


@app.route("/api/face/recognition", methods=["POST"])
def rec_face():
    """
    人脸识别
    接口参数：
    (必填，str)images：图片的base64或url

    :return:
    """
    try:
        json_data = flask.request.get_json(force=True)
        face_images = []
        images = json_data["images"]
        for img_data in images:
            if not img_data:
                continue
            if imgUtil.is_base64_code(img_data):
                origin_img = imgUtil.base64_to_ndarray(img_data)
                face_images.append(origin_img)
            elif imgUtil.is_http_url(img_data):
                origin_img = imgUtil.url_to_ndarray(img_data)
                face_images.append(origin_img)

        flag, img_base64 = main.verify(face_images)
        return jsonify(
            code=0, data={"verified": flag, "faceImg": img_base64}, msg="success"
        )
    except Exception as e:
        log.error("【rec_face】" + str(e))
        msg = "【rec_face】" + str(e)
        return jsonify(code=-1, data=None, msg=msg)


if __name__ == "__main__":
    server = pywsgi.WSGIServer(("0.0.0.0", 60006), app)
    server.serve_forever()
