#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import os
from collections import deque
from base import setting
import configparser
import cv2
import time
import numpy as np
import mediapipe as mp
from utils.Thread import MyThreadFunc
import random
import math
import onnxruntime as ort


class DetectFaceAndLip:
    # 唇动检测
    def __init__(self, funasr_event, camera_index=1):
        self.funasr_event = funasr_event
        # 设定说话检测的频率
        self.fps = 25
        self.padding = int(self.get_config_value("padding_size", "padding"))
        # 判断嘴唇开合阈值
        self.lip_open_threshold = float(
            self.get_config_value("lip_open", "lip_open_threshold")
        )
        self.mouth_status_history = []  # 用于存储嘴唇状态的历史记录
        self.remark = "Not talking"

        # self._open = bool(self.get_config_value("update_open", "open"))
        self.face_count = 0  # 用于保存文件的计数

        self.desired_size = int(self.get_config_value("resized_images", "desired_size"))
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.7
        )  # 人脸检测
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            refine_landmarks=True,
            max_num_faces=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.65,
        )  # 初始化面部网格检测器
        # 手部检测模型用来判断是否遮挡
        # self.hands = mp.solutions.hands.Hands(
        #     static_image_mode=False,
        #     max_num_hands=2,
        #     min_detection_confidence=0.7,
        #     min_tracking_confidence=0.7,
        # )
        # 目标人脸的边界框
        self.target_face_bbox = None
        self.gamma = float(self.get_config_value("image_enhance", "gamma"))
        inv_gamma = 1.0 / self.gamma
        self.gamma_table = np.array(
            [(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]
        ).astype("uint8")
        # 摄像头
        self.camera_index = camera_index  # 新增摄像头索引配置
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头（索引：{self.camera_index}）。")
        # 获取实际的FPS
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0:
            self.fps = 25
        self.session = ort.InferenceSession(str(setting.model_path))
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.d_normalized_history = deque(maxlen=25)
        MyThreadFunc(func=self.check_talking, args=[]).start()

    def detect_face_and_mouth(self):
        prev_mouth_status = None  # 记录上一帧的嘴唇状态
        cap = self.cap
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"实际分辨率: {int(width)}x{int(height)}, FPS: {self.fps}")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape

            # 进行人脸检测
            frame, self.target_face_bbox = self.__handle_face_tracking_with_mediapipe(
                frame, self.target_face_bbox
            )

            if self.target_face_bbox:
                x_min, y_min, width, height = self.target_face_bbox
                x_min = max(0, x_min)
                y_min = max(0, y_min)
                x_max = min(frame_width, x_min + width)
                y_max = min(frame_height, y_min + height)

                # 提取目标人脸区域
                face_roi = frame[y_min:y_max, x_min:x_max]
                # 添加Padding，扩大人脸区域
                x_min_padded = max(0, x_min - self.padding)
                y_min_padded = max(0, y_min - self.padding)
                x_max_padded = min(frame_width, x_max + self.padding)
                y_max_padded = min(frame_height, y_max + self.padding)
                # 裁剪并添加Padding的face_roi_padded
                face_roi_padded = frame[
                                  y_min_padded:y_max_padded, x_min_padded:x_max_padded
                                  ]
                h, w = face_roi_padded.shape[:2]
                # 检测人脸是否模糊
                if not self.is_face_clear(face_roi_padded):
                    if prev_mouth_status is not None:
                        self.mouth_status_history.append(prev_mouth_status)
                    continue
                # 等比例缩放人脸区域到固定尺寸
                scale_w = self.desired_size / w
                scale_h = self.desired_size / h
                new_w = int(w * scale_w)
                new_h = int(h * scale_h)

                resized_face = cv2.resize(face_roi_padded, (new_w, new_h))
                # resized_face = self.enhance_image(resized_face)
                # cv2.imshow("change", resized_face)
                # 在 resized_face 上绘制关键点用于保存和可视化
                rgb_face = cv2.cvtColor(resized_face, cv2.COLOR_BGR2RGB)
                output = self.face_mesh.process(rgb_face)
                landmark_points = output.multi_face_landmarks

                if landmark_points:
                    # 处理检测到的人脸关键点
                    selected_landmarks = landmark_points[0].landmark
                    # 判断手是否遮挡人脸
                    # face_occluded = self.is_hand_covering_face_simple(resized_face)

                    self.face_count += 1
                    current_mouth_status = self.update_mouth_status(
                         selected_landmarks
                    )
                    prev_mouth_status = current_mouth_status
                    face_points = []
                    for landmark in selected_landmarks:
                        # landmark.x, landmark.y 范围在 [0,1]
                        # 转换为resized_face坐标
                        x_resized = landmark.x * new_w
                        y_resized = landmark.y * new_h

                        # 映射回 face_roi_padded 原始坐标
                        x_padded = x_resized / scale_w
                        y_padded = y_resized / scale_h

                        # 映射回 frame 全局坐标
                        x_frame_coord = int(x_min_padded + x_padded)
                        y_frame_coord = int(y_min_padded + y_padded)

                        face_points.append((x_frame_coord, y_frame_coord))

                    # 绘制浅蓝色mesh结构
                    for connection in mp.solutions.face_mesh.FACEMESH_TESSELATION:
                        pt1 = face_points[connection[0]]
                        pt2 = face_points[connection[1]]
                        cv2.line(frame, pt1, pt2, (255, 255, 0), 1)

                    # 绘制嘴唇红色
                    for connection in mp.solutions.face_mesh.FACEMESH_LIPS:
                        pt1 = face_points[connection[0]]
                        pt2 = face_points[connection[1]]
                        cv2.line(frame, pt1, pt2, (0, 0, 255), 1)

                    cv2.putText(
                        frame,
                        self.remark,
                        (30, 30),
                        cv2.FONT_HERSHEY_DUPLEX,
                        1,
                        (
                            (0, 0, 255) if "Please" in self.remark else (125, 246, 55)
                        ),  # 提示信息为红色，正常信息为绿色
                        1,
                    )
                else:
                    self.d_normalized_history.clear()
                    self.mouth_status_history.clear()
                    self.remark = "No Face Detected"
                    cv2.putText(
                        frame,
                        self.remark,
                        (30, 30),
                        cv2.FONT_HERSHEY_DUPLEX,
                        1,
                        (0, 0, 255),  # 红色
                        1,
                    )
            else:
                # 没有检测到人脸时的处理
                self.remark = "No Face Detected"
                self.d_normalized_history.clear()
                self.mouth_status_history.clear()
                cv2.putText(
                    frame,
                    self.remark,
                    (30, 30),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1,
                    (0, 0, 255),  # 红色
                    1,
                )
            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()

    def min_max_scale(self, data):
        # MinMaxScaler
        data = np.array(data)
        min_val = np.min(data)
        max_val = np.max(data)
        # 避免除以零
        if max_val - min_val == 0:
            return data
        scaled_data = (data - min_val) / (max_val - min_val)
        return scaled_data

    @staticmethod
    def get_config_value(group, key):
        con = configparser.ConfigParser()
        con.read(setting.CONFIG_DIR, encoding="utf-8")
        return con.get(group, key)

    # 可用摄像头列表
    def get_available_cameras(self, max_index=3):
        available_cameras = []
        for index in range(max_index):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                available_cameras.append(index)
                cap.release()
        return available_cameras

    # 选择工作摄像头
    def select_working_camera(self):
        # 获取可用摄像头列表
        available_cameras = self.get_available_cameras()
        if not available_cameras:
            print("未找到可用的摄像头。")
            return None, None

        for camera_index in available_cameras:
            print(f"尝试使用摄像头索引：{camera_index}")
            cap = cv2.VideoCapture(camera_index)
            self.fps = cap.get(cv2.CAP_PROP_FPS)

            if not cap.isOpened():
                print(f"无法打开摄像头（索引：{camera_index}）。")
                continue

            # 尝试读取一帧，检查摄像头是否工作正常
            ret, frame = cap.read()
            if not ret:
                print(f"无法从摄像头（索引：{camera_index}）读取帧。")
                cap.release()
                continue

            # 检测人脸
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)

            if results.detections:
                print(f"摄像头（索引：{camera_index}）可以检测到人脸。")
                return cap, camera_index  # 返回摄像头对象和索引
            else:
                print(f"摄像头（索引：{camera_index}）无法检测到人脸。")
                cap.release()
        print("所有摄像头均无法检测到人脸。")
        return None, None

    def __handle_face_tracking_with_mediapipe(
            self, frame, target_face_bbox, distance_threshold=70
    ):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width, _ = frame.shape
        # 使用 MediaPipe 进行人脸检测
        results = self.face_detection.process(rgb_frame)
        # 如果检测到人脸，输出每个检测到的脸部边界框和置信度
        # if results.detections:
        #     for detection in results.detections:
        #         # 获取边界框信息
        #         bboxC = detection.location_data.relative_bounding_box
        #         print(
        #             f"Bounding Box - x: {bboxC.xmin}, y: {bboxC.ymin}, width: {bboxC.width}, height: {bboxC.height}"
        #         )
        #         # 获取检测置信度
        #         print(f"Detection confidence: {detection.score[0]}")
        if results.detections:
            candidate_faces = []
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                # 转换为像素坐标
                x_min = int(bboxC.xmin * frame_width)
                y_min = int(bboxC.ymin * frame_height)
                width = int(bboxC.width * frame_width)
                height = int(bboxC.height * frame_height)
                candidate_faces.append((x_min, y_min, width, height))
            # 如果已锁定目标人脸，根据距离选择最接近的
            if target_face_bbox:
                target_x, target_y, target_width, target_height = target_face_bbox
                target_center = (
                    target_x + target_width // 2,
                    target_y + target_height // 2,
                )
                min_distance = float("inf")
                closest_face = None
                for face in candidate_faces:
                    face_x, face_y, face_width, face_height = face
                    face_center = (face_x + face_width // 2, face_y + face_height // 2)
                    # 计算目标人脸和候选人脸的中心距离
                    distance = (
                                       (face_center[0] - target_center[0]) ** 2
                                       + (face_center[1] - target_center[1]) ** 2
                               ) ** 0.5
                    if distance < min_distance and distance < distance_threshold:
                        min_distance = distance
                        closest_face = face
                # 更新目标人脸边界框
                if closest_face:
                    target_face_bbox = closest_face
                    # 检查人脸是否接近图像边缘
                    if self.__is_face_near_edge(
                            target_face_bbox, frame_width, frame_height
                    ):
                        # 如果人脸接近边缘，重置目标人脸边界框
                        target_face_bbox = None
                else:
                    pass
            else:
                # 如果未锁定目标人脸，选择面积最大的人脸
                target_face_bbox = max(candidate_faces, key=lambda x: x[2] * x[3])
                # 检查新目标人脸是否接近边缘
                if self.__is_face_near_edge(
                        target_face_bbox, frame_width, frame_height
                ):
                    # 如果人脸接近边缘，重置目标人脸边界框
                    target_face_bbox = None
        else:
            # 如果未检测到人脸，目标人脸置空
            target_face_bbox = None

        return frame, target_face_bbox

    def __calculate_lip_distance(self, selected_landmarks):
        # 计算调整后的嘴唇开合距离
        # 定义关键点内唇
        lip_landmark_pairs = [(13, 14), (81, 178), (82, 87), (312, 317), (311, 402)]
        vertical_distances = []
        for upper_idx, lower_idx in lip_landmark_pairs:
            upper_point = np.array(
                [
                    selected_landmarks[upper_idx].x * self.desired_size,
                    selected_landmarks[upper_idx].y * self.desired_size,
                ]
            )
            lower_point = np.array(
                [
                    selected_landmarks[lower_idx].x * self.desired_size,
                    selected_landmarks[lower_idx].y * self.desired_size,
                ]
            )

            vertical_distance = np.linalg.norm(upper_point - lower_point)
            vertical_distances.append(vertical_distance)

        avg_vertical_distance = np.mean(vertical_distances)
        # print("avg_vertical_distance", avg_vertical_distance * 10)
        # # 计算关键点0和17之间的距离
        distance_upper_lip = abs(
            selected_landmarks[0].y * self.desired_size
            - selected_landmarks[17].y * self.desired_size
        )
        # # print("self.baseline_lip_threshold", self.baseline_lip_threshold)
        # 计算13和14之间的距离
        # point_13 = selected_landmarks[13]
        # point_14 = selected_landmarks[14]
        #
        # distance_13_14 = abs(
        #     point_13.y * self.desired_size - point_14.y * self.desired_size
        # )
        # # print("distance_13_14", distance_13_14)
        try:
            D_normalized = avg_vertical_distance * 100 / distance_upper_lip
        except ZeroDivisionError:
            D_normalized = 0
        # print("D_normalized", D_normalized)
        return D_normalized

    @staticmethod
    def __is_face_centered(landmarks, width=350, yaw_threshold=10, pitch_threshold=31):

        # 定义关键点索引
        LEFT_EYE_INDEX = 33
        RIGHT_EYE_INDEX = 263
        NOSE_TIP_INDEX = 1

        # 获取关键点归一化坐标
        left_eye = landmarks[LEFT_EYE_INDEX]
        right_eye = landmarks[RIGHT_EYE_INDEX]
        nose_tip = landmarks[NOSE_TIP_INDEX]

        # 转换为像素坐标
        left_eye_x = left_eye.x * width
        left_eye_y = left_eye.y * width
        right_eye_x = right_eye.x * width
        right_eye_y = right_eye.y * width
        nose_tip_x = nose_tip.x * width
        nose_tip_y = nose_tip.y * width

        # 计算左右眼中心坐标 (眼间中心) 及眼间距离
        eye_center_x = (left_eye_x + right_eye_x) / 2.0
        eye_center_y = (left_eye_y + right_eye_y) / 2.0
        interocular_distance = abs(right_eye_x - left_eye_x)  # 两眼水平距离

        # =============  第一部分：检测左右摆头（Yaw）  =============
        # 计算鼻尖在水平方向相对眼睛中心偏移的角度
        # 通过 atan2(横向差值, 眼间距离) 获得“偏航角”
        eye_nose_delta_x = nose_tip_x - eye_center_x
        yaw_angle = math.degrees(
            math.atan2(abs(eye_nose_delta_x), interocular_distance)
        )
        # print("yaw_angle", yaw_angle)
        if yaw_angle > yaw_threshold:
            return False  # 左右转头过大

        # =============  第二部分：检测上下点头（Pitch）  =============
        #  计算鼻尖在垂直方向相对眼睛中心偏移的角度
        # 通过 atan2(纵向差值, 眼间距离) 获得“俯仰角”
        eye_nose_delta_y = nose_tip_y - eye_center_y
        pitch_angle = math.degrees(
            math.atan2(abs(eye_nose_delta_y), interocular_distance)
        )
        # print("pitch_angle", pitch_angle)
        if pitch_angle > pitch_threshold:
            return False  # 上下点头过大

        return True

    def update_mouth_status(self, landmarks):
        # 将当前距离加入历史记录
        detected=False

        if self.__is_face_centered(landmarks):
            current_distance = self.__calculate_lip_distance(
                landmarks
            )
            self.d_normalized_history.append(current_distance)
            if len(self.d_normalized_history) == 25:
                # 将 deque 转为 NumPy 数组以进行归一化

                normalized_history = self.min_max_scale(list(self.d_normalized_history))
                input_array = np.array(normalized_history, dtype=np.float32).reshape(
                    1, 25, 1
                )

                # 使用模型预测嘴巴状态
                y_pred = self.session.run(
                    [self.output_name], {self.input_name: input_array}
                )
                predict = np.argmax(y_pred[0], axis=-1)

                if int(predict) == 1:  # "speaking"
                    detected = True
                else:  # "silent"
                    detected = False
            else:
                # 如果历史记录不足，使用当前距离判断
                # detected = distance_13 > self.lip_open_threshold
                detected = False

        # print(detected)
        # 更新嘴巴状态历史记录
        self.mouth_status_history.append(detected)
        return detected

    def check_talking(self):
        wait = 0.4  # 时间窗口（秒）
        talking_threshold = 0
        talking_frames_required = int(talking_threshold * self.fps)
        talking_frames_count = 0  # 连续 talking 的帧数计数
        while True:
            total_count = len(self.mouth_status_history)

            if total_count > wait * self.fps:
                # 复制历史记录并清空
                history = self.mouth_status_history.copy()
                self.mouth_status_history.clear()

                # print("history", len(history))

                # 统计 history 中 True 的数量
                talking_count = sum(history)
                talking_ratio = talking_count / len(history)  # 计算 True 的比例

                if talking_ratio > 0.5:
                    is_talking = True
                    self.remark = "Talking"
                else:  # 否则表示未说话
                    is_talking = False
                    self.remark = "Not Talking"

                # 根据 is_talking 状态更新事件和计数器
                if is_talking:
                    talking_frames_count += 1
                    if talking_frames_count >= talking_frames_required:
                        self.funasr_event.set()  # 触发事件
                else:
                    talking_frames_count = 0
                    self.funasr_event.clear()  # 清除事件

            time.sleep(0.15)  # 窗口刷新频率

    @staticmethod
    def __is_face_near_edge(bbox, frame_width, frame_height, edge_threshold=0):
        x_min, y_min, width, height = bbox
        # 人脸是否接近图像边缘
        if (
                x_min < edge_threshold
                or x_min + width > frame_width - edge_threshold
                or y_min < edge_threshold
                or y_min + height > frame_height - edge_threshold
        ):
            return True
        return False

    def estimate_face_angle(self, landmarks):
        # 估算人脸的旋转角度
        nose_tip = np.array(
            [landmarks[1].x * self.desired_size, landmarks[1].y * self.desired_size]
        )
        mouth_left = np.array(
            [landmarks[61].x * self.desired_size, landmarks[61].y * self.desired_size]
        )
        mouth_right = np.array(
            [landmarks[291].x * self.desired_size, landmarks[291].y * self.desired_size]
        )
        # 计算眼睛中心和嘴巴中心
        mouth_center = (mouth_left + mouth_right) / 2
        # 计算俯仰角（鼻尖到嘴巴中心的垂直偏移）
        delta_y_pitch = mouth_center[1] - nose_tip[1]
        return delta_y_pitch

    # 保存识别人脸
    def save_face(self, face_roi):
        if not os.path.exists(setting.TEMP_DIR):
            os.makedirs(setting.TEMP_DIR)
        file_name = f"{setting.TEMP_DIR}/face_{self.face_count:04d}.jpg"
        cv2.imwrite(file_name, face_roi)
        # print(f"保存人脸 {file_name}")

    @staticmethod
    def is_face_clear(face_roi, threshold=100):
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var > threshold

    # def is_hand_covering_face(self, frame, selected_landmarks):
    #     image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     hand_results = self.hands.process(image_rgb)
    #
    #     if not hand_results.multi_hand_landmarks:
    #         return False
    #
    #     frame_height, frame_width, _ = frame.shape
    #
    #     # 获取手部 bounding box 列表
    #     hand_bboxes = []
    #     for hand_landmarks in hand_results.multi_hand_landmarks:
    #         x_coords = [lm.x for lm in hand_landmarks.landmark]
    #         y_coords = [lm.y for lm in hand_landmarks.landmark]
    #         x_min = int(min(x_coords) * frame_width)
    #         x_max = int(max(x_coords) * frame_width)
    #         y_min = int(min(y_coords) * frame_height)
    #         y_max = int(max(y_coords) * frame_height)
    #         hand_bboxes.append((x_min, y_min, x_max, y_max))
    #
    #     # 获取嘴部关键点的全局坐标
    #     mouth_indices = [13, 14]
    #     mouth_points = [
    #         (
    #             int(selected_landmarks[idx].x * frame_width),
    #             int(selected_landmarks[idx].y * frame_height),
    #         )
    #         for idx in mouth_indices
    #     ]
    #
    #     # 检查嘴部关键点是否在任何一个手的bbox内
    #     for fx, fy in mouth_points:
    #         for x_min, y_min, x_max, y_max in hand_bboxes:
    #             if x_min <= fx <= x_max and y_min <= fy <= y_max:
    #                 return True
    #     return False

    # def is_hand_covering_face_simple(self, frame):
    #     image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     hand_results = self.hands.process(image_rgb)
    #
    #     if hand_results.multi_hand_landmarks:
    #         return True  # 检测到手，认为脸部遮挡
    #     else:
    #         return False  # 未检测到手，认为脸部未遮挡

    # 人脸增强
    def enhance_image(self, face_roi_padded):
        # YCrCb 增强对比度
        ycrcb = cv2.cvtColor(face_roi_padded, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # 调整 tileGridSize
        y_eq = clahe.apply(y)
        ycrcb_eq = cv2.merge((y_eq, cr, cb))
        face_roi_enhanced = cv2.cvtColor(ycrcb_eq, cv2.COLOR_YCrCb2BGR)

        # Gamma 校正，使用预计算的表
        face_roi_enhanced = cv2.LUT(face_roi_enhanced, self.gamma_table)
        return face_roi_enhanced
