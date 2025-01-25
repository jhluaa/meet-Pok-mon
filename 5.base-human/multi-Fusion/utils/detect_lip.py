#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import os
from collections import deque

import cv2
import time
import numpy as np
import mediapipe as mp
from utils.Thread import MyThreadFunc
from base import setting


class DetectFaceAndLip:
    # 唇动检测
    def __init__(self, funasr_event):
        self.funasr_event = funasr_event
        # 设定说话检测的频率    padding =10  desired_size 216 padding=10 desired_size=300
        self.fps = 25
        self.padding = 25
        # 判断嘴唇开合阈值
        self.lip_open_threshold = 10  # 1. 0 17  阈值20; 2.avg 10
        self.mouth_status_history = []  # 用于存储嘴唇状态的历史记录
        self.remark = "Not talking"
        self.face_count = 0  # 用于保存文件的计数
        self.desired_size = 300  # 计算lip输入框大小
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )  # 人脸检测
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=2, min_detection_confidence=0.6, min_tracking_confidence=0.6
        )  # 初始化面部网格检测器
        self.face_bbox_history = deque(maxlen=5)  # 帧平均
        # 目标人脸的边界框
        self.target_face_bbox = None
        MyThreadFunc(func=self.check_talking, args=[]).start()

    def detect_face_and_mouth(self):
        prev_mouth_status = None  # 记录上一帧的嘴唇状态
        # 调用封装好的函数来选择摄像头
        # cap, camera_index = self.select_working_camera()
        # if cap is None:
        #     print("未找到可用的摄像头。")
        #     return
        # print(f"使用摄像头索引 {camera_index} 进行检测。")
        cap = cv2.VideoCapture(0)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"实际分辨率: {int(width)}x{int(height)}", self.fps)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        # print(self.fps)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            # 进行人脸检测和跟踪
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
                # cv2.imshow("origin", face_roi)
                or_h, or_w = face_roi.shape[:2]
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
                # cv2.imshow("change", resized_face)
                # resized_face=self.enhance_image(resized_face)
                # 保存人脸到本地
                # self.save_face(face_roi)
                # self.save_face(resized_face)
                # 在 resized_face 上绘制关键点用于保存和可视化
                rgb_face = cv2.cvtColor(resized_face, cv2.COLOR_BGR2RGB)
                output = self.face_mesh.process(rgb_face)
                landmark_points = output.multi_face_landmarks
                if landmark_points:
                    # 处理检测到的人脸关键点
                    selected_landmarks = landmark_points[0].landmark
                    current_distance, distance_ = self.__calculate_lip_distance(
                        selected_landmarks, self.desired_size
                    )
                    # print("current_distance",current_distance)
                    self.face_count += 1
                    _centered = self.__is_face_centered(
                        selected_landmarks, self.desired_size
                    )
                    current_mouth_status = self.update_mouth_status(
                        _centered, current_distance, distance_
                    )
                    prev_mouth_status = current_mouth_status
                    # 绘制目标人脸边界框可视化
                # cv2.rectangle(frame, (x_min, y_min), (x_min + width, y_min + height), (0, 255, 0), 1)
                rgb_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                output = self.face_mesh.process(rgb_face)
                landmark_points1 = output.multi_face_landmarks

                if landmark_points1:
                    # 只处理目标人脸的关键点
                    selected_landmarks1 = landmark_points1[0].landmark
                    face_points = []
                    # 绘制特征点，需要映射回原始帧坐标
                    for landmark in selected_landmarks1:
                        x_on_face = int(landmark.x * or_w)
                        y_on_face = int(landmark.y * or_h)
                        x_on_frame = x_min + x_on_face
                        y_on_frame = y_min + y_on_face
                        face_points.append((x_on_frame, y_on_frame))
                        # cv2.circle(frame, (x_on_frame, y_on_frame), 1, (0, 255, 0), -1)
                    # 绘制浅蓝色
                    for connection in mp.solutions.face_mesh.FACEMESH_TESSELATION:
                        pt1 = face_points[connection[0]]
                        pt2 = face_points[connection[1]]
                        cv2.line(frame, pt1, pt2, (255, 255, 0), 1)
                    # 绘制嘴巴红色
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
                self.remark = "No Face Detected"
            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()

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
        self, frame, target_face_bbox, distance_threshold=100
    ):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width, _ = frame.shape
        # 使用 MediaPipe 进行人脸检测
        results = self.face_detection.process(rgb_frame)
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
                    self.face_bbox_history.append(closest_face)
                    # 计算移动平均
                    avg_bbox = (
                        int(np.mean([bbox[0] for bbox in self.face_bbox_history])),
                        int(np.mean([bbox[1] for bbox in self.face_bbox_history])),
                        int(np.mean([bbox[2] for bbox in self.face_bbox_history])),
                        int(np.mean([bbox[3] for bbox in self.face_bbox_history])),
                    )
                    target_face_bbox = avg_bbox
                    # print("closest_face:", target_face_bbox)
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
                self.face_bbox_history.append(target_face_bbox)
                # 计算移动平均
                avg_bbox = (
                    int(np.mean([bbox[0] for bbox in self.face_bbox_history])),
                    int(np.mean([bbox[1] for bbox in self.face_bbox_history])),
                    int(np.mean([bbox[2] for bbox in self.face_bbox_history])),
                    int(np.mean([bbox[3] for bbox in self.face_bbox_history])),
                )
                target_face_bbox = avg_bbox
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

    def __calculate_lip_distance(self, selected_landmarks, desired_size):
        # 计算调整后的嘴唇开合距离
        # 定义关键点内唇
        lip_landmark_pairs = [(13, 14), (81, 178), (82, 87), (312, 317), (311, 402)]
        vertical_distances = []
        for upper_idx, lower_idx in lip_landmark_pairs:
            upper_point = np.array(
                [
                    selected_landmarks[upper_idx].x * desired_size,
                    selected_landmarks[upper_idx].y * desired_size,
                ]
            )
            lower_point = np.array(
                [
                    selected_landmarks[lower_idx].x * desired_size,
                    selected_landmarks[lower_idx].y * desired_size,
                ]
            )
            # 计算垂直距离（y轴差值）
            vertical_distance = abs(lower_point[1] - upper_point[1])
            vertical_distances.append(vertical_distance)
        # 计算所有垂直距离的平均值
        avg_vertical_distance = np.mean(vertical_distances)
        # print("所有垂直距离的平均值",avg_vertical_distance*10)
        # 计算关键点0和17之间的距离
        distance_upper_lip = abs(
            selected_landmarks[0].y * desired_size
            - selected_landmarks[17].y * desired_size
        )
        # 打印17和0的距离
        # print("17 和 0 之间的嘴唇距离:", distance_upper_lip)
        # 计算13和14之间的距离
        distance_13_14 = abs(
            selected_landmarks[13].y * desired_size
            - selected_landmarks[14].y * desired_size
        )
        # print("distance_13_14",distance_13_14)
        # print("13 和 14 之间的嘴唇距离:", distance_upper_lip)
        try:
            D_normalized = avg_vertical_distance * 100 / distance_upper_lip
        except ZeroDivisionError:
            D_normalized = 0  # 处理除零错误
        # print("D_normalized",D_normalized)
        return D_normalized, distance_13_14

    @staticmethod
    def __is_face_centered(landmarks, width):
        # 定义用于判断正脸的关键点索引
        LEFT_EYE_INDEX = 33
        RIGHT_EYE_INDEX = 263
        NOSE_TIP_INDEX = 1
        MOUTH_CENTER_INDEX = 13

        # 获取关键点的坐标
        left_eye = landmarks[LEFT_EYE_INDEX]
        right_eye = landmarks[RIGHT_EYE_INDEX]
        nose_tip = landmarks[NOSE_TIP_INDEX]
        mouth_center = landmarks[MOUTH_CENTER_INDEX]
        # 转换为像素坐标
        left_eye_x = int(left_eye.x * width)
        right_eye_x = int(right_eye.x * width)
        nose_tip_x = int(nose_tip.x * width)
        mouth_center_x = int(mouth_center.x * width)

        # 计算左右眼的水平中心
        eye_center_x = (left_eye_x + right_eye_x) / 2

        # 判断鼻子和嘴巴是否在眼睛中心的垂直线上
        if (
            abs(nose_tip_x - eye_center_x) < 20
            and abs(mouth_center_x - eye_center_x) < 20
        ):
            return True
        return False

    def update_mouth_status(self, centered, current_distance, distance_):
        # 只有当脸居中时才更新嘴唇状态
        if centered:
            distance_change = current_distance
            if distance_ < 1:
                detected = False
            else:
                detected = distance_change > self.lip_open_threshold
            # 更新历史记录
            self.mouth_status_history.append(detected)
            return detected
        else:
            # 如果脸不居中，返回上一状态
            self.remark = "Please face the camera"  # 提示用户调整
            if len(self.mouth_status_history) > 0:
                return self.mouth_status_history[-1]
            else:
                return False

    # def check_talking(self):
    #     wait = 0.5
    #     while True:
    #         alternations = 0
    #         is_talking = False
    #         total_count = len(self.mouth_status_history)
    #         # 遍历列表，计算张嘴闭嘴的频率
    #         if total_count > wait * self.fps:
    #             history = self.mouth_status_history.copy()
    #             self.mouth_status_history.clear()
    #             # 离散计算 计算闭嘴和张嘴的次数
    #             for i in range(1, len(history)):
    #                 if history[i] != history[i - 1]:
    #                     alternations += 1
    #             if alternations > 2:
    #                 is_talking = True
    #             else:
    #                 # 通过概率计算 初始状态
    #                 open_count = sum(history)
    #                 open_ratio = open_count / len(history)
    #                 is_talking = 0.1< open_ratio < 0.8
    #             if is_talking:
    #                 self.remark = "Talking"
    #                 self.funasr_event.set()
    #             else:
    #                 self.remark = "Not talking"
    #                 self.funasr_event.clear()
    #
    #         time.sleep(0.01)
    # def check_talking(self):
    #     wait = 0.4
    #     while True:
    #         total_count = len(self.mouth_status_history)
    #         if total_count > wait * self.fps:
    #             history = self.mouth_status_history.copy()
    #             print("history:",history)
    #             self.mouth_status_history.clear()
    #             all_open = all(history)
    #             all_closed = not any(history)
    #             if all_open or all_closed:
    #                 is_talking = False
    #             else:
    #                 is_talking = True
    #             if is_talking:
    #                 self.remark = "Talking"
    #                 self.funasr_event.set()
    #             else:
    #                 self.remark = "Not talking"
    #                 self.funasr_event.clear()
    #         time.sleep(0.2)
    def check_talking(self):
        wait = 0.4  # 时间窗口
        talking_threshold = 0.2  # 持续talking的时间
        talking_frames_required = int(talking_threshold * self.fps)
        talking_frames_count = 0  # 连续talking的帧数计数

        while True:
            total_count = len(self.mouth_status_history)
            if total_count > wait * self.fps:
                history = self.mouth_status_history.copy()
                # print("history:", history)
                self.mouth_status_history.clear()
                all_open = all(history)
                all_closed = not any(history)
                if all_open or all_closed:
                    is_talking = False
                    self.remark = "Not talking"
                else:
                    is_talking = True
                    self.remark = "Talking"
                if is_talking:
                    talking_frames_count += 1
                    if talking_frames_count >= talking_frames_required:
                        self.funasr_event.set()
                else:
                    talking_frames_count = 0
                    self.funasr_event.clear()
            time.sleep(0.1)  # 及时检查窗口数值

    @staticmethod
    def __is_face_near_edge(bbox, frame_width, frame_height, edge_threshold=20):
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
        # # 计算俯仰角（鼻尖到嘴巴中心的垂直偏移）
        delta_y_pitch = mouth_center[1] - nose_tip[1]
        # print("delta_y_pitch", delta_y_pitch)  # 正脸 30-40 俯视 10- 20
        return delta_y_pitch

    def alignment_face(self):
        pass

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

    # 人脸增强
    @staticmethod
    def enhance_image(face_roi_padded):
        cv2.imshow("original", face_roi_padded)
        # 将图像从BGR转换到YCrCb颜色空间
        ycrcb = cv2.cvtColor(face_roi_padded, cv2.COLOR_BGR2YCrCb)
        # 分离Y(亮度)通道
        y, cr, cb = cv2.split(ycrcb)
        # 创建CLAHE对象，参数可以根据需要调整
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(1, 1))
        # 应用CLAHE到Y通道
        y_eq = clahe.apply(y)
        # 合并均衡化后的Y通道与原始的Cr和Cb通道
        ycrcb_eq = cv2.merge((y_eq, cr, cb))
        # 将图像从YCrCb转换回BGR颜色空间
        face_roi_enhanced = cv2.cvtColor(ycrcb_eq, cv2.COLOR_YCrCb2BGR)
        cv2.imshow("change", face_roi_enhanced)
        return face_roi_enhanced
