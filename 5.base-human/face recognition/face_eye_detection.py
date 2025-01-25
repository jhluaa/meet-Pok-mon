import os
import cv2
import dlib
import numpy as np
from mtcnn import MTCNN
from imutils import face_utils
import setting


class LivenessDetector:
    def __init__(self, predictor_path, ear_thresh=0.20):
        """
        初始化人脸检测器和特征点预测器。

        :param predictor_path: shape_predictor_68_face_landmarks.dat 文件的路径
        :param ear_thresh: EAR 阈值，用于判断眼睛是否睁开
        """
        self.EAR_THRESH = ear_thresh

        if not os.path.isfile(predictor_path):
            raise FileNotFoundError(f"特征点检测器文件未找到: {predictor_path}")

        print("[INFO] 加载面部特征点预测器...")
        self.mtcnn = MTCNN()  # 初始化 MTCNN
        self.predictor = dlib.shape_predictor(predictor_path)

        # 获取左眼和右眼的特征点索引
        self.lStart, self.lEnd = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        self.rStart, self.rEnd = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    @staticmethod
    def eye_aspect_ratio(eye):
        """
        计算眼睛的纵横比 (EAR)。

        :param eye: 左眼或右眼的关键点数组
        :return: EAR 值
        """
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def process_image(self, image_path):
        """
        处理单张图片，判断人脸的眼睛是否睁开。

        :param image_path: 图片的路径
        :return: 处理后的图像和检测结果
        """
        if not os.path.isfile(image_path):
            print(f"输入图像文件不存在: {image_path}")
            return None, None

        # 加载图像
        image = cv2.imread(image_path)
        if image is None:
            print(f"无法加载图像: {image_path}")
            return None, None

        # 使用 MTCNN 检测人脸
        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces = self.mtcnn.detect_faces(rgb_img)

        if not faces:
            print("未检测到人脸！")
            return image, None

        # 获取最大的人脸区域
        largest_face = max(faces, key=lambda face: face["box"][2] * face["box"][3])
        x, y, width, height = largest_face["box"]

        # 确保裁剪区域在图像范围内
        x = max(0, x)
        y = max(0, y)
        cropped_face = image[y : y + height, x : x + width]

        if cropped_face.size == 0:
            print("裁剪后的脸部区域为空！")
            return image, None

        # 将裁剪区域转换为灰度图
        gray = cv2.cvtColor(cropped_face, cv2.COLOR_BGR2GRAY)

        # 使用 dlib 的特征点预测器
        rect = dlib.rectangle(0, 0, cropped_face.shape[1], cropped_face.shape[0])
        shape = self.predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        # 提取左右眼的关键点
        left_eye = shape[self.lStart : self.lEnd]
        right_eye = shape[self.rStart : self.rEnd]
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0

        # 将眼睛关键点坐标偏移到原图上
        left_eye += np.array([x, y])
        right_eye += np.array([x, y])

        # 绘制眼睛轮廓
        left_eye_hull = cv2.convexHull(left_eye)
        right_eye_hull = cv2.convexHull(right_eye)
        cv2.drawContours(image, [left_eye_hull], -1, (0, 255, 0), 1)
        cv2.drawContours(image, [right_eye_hull], -1, (0, 255, 0), 1)

        # 判断眼睛是否睁开
        if ear < self.EAR_THRESH:
            status = "Eyes Closed"
            rs = False
            color = (0, 0, 255)  # 红色表示闭眼
        else:
            status = "Eyes Open"
            rs = True
            color = (0, 255, 0)  # 绿色表示睁眼

        # 在图像上显示结果
        cv2.putText(
            image,
            f"EAR: {ear:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
        cv2.putText(
            image,
            status,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        # 返回处理后的图像和 EAR 值
        return image, rs
        # return image, ear


if __name__ == "__main__":
    # 初始化 Liveness 检测器
    try:
        liveness_detector = LivenessDetector(
            predictor_path=setting.SHAPE_PREDICTOR_PATH
        )
    except FileNotFoundError as e:
        print(e)
        exit(1)
    except Exception as e:
        print(f"初始化 LivenessDetector 时发生错误: {e}")
        exit(1)

    # 处理图片
    img_path = "/data/gitlab/base-digital-human/face-recognition/resources/142beece651444b187544d38a7bfbdf4.jpg"
    image, rs = liveness_detector.process_image(img_path)  # 处理后图片，判断结果

    if image is not None:
        # 显示处理后的图像
        cv2.namedWindow("Liveness Detection", cv2.WINDOW_NORMAL)
        cv2.imshow("Liveness Detection", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("处理失败或未检测到人脸。")
