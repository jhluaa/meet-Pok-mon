import cv2
import os
import datetime
import time


def record_video(output_filename="output.avi", duration=None):
    cap = cv2.VideoCapture(0)
    save_interval = 1
    last_save_time = time.time()
    if not cap.isOpened():
        return
        # 创建保存图片的文件夹
    save_dir = "../resources/captured_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_filename, fourcc, fps, (frame_width, frame_height))

    print("開始錄製視頻。按 'q' 鍵停止錄製。")

    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

        cv2.imshow("Recording", frame)
        # 当前时间
        current_time = time.time()
        # 判断是否到达保存时间
        if current_time - last_save_time >= save_interval:
            # 获取当前时间作为文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(save_dir, f"image_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"图片已保存到: {filename}")
            last_save_time = current_time
        # 檢查是否達到指定的錄製時間
        if duration is not None:
            elapsed_time = time.time() - start_time
            if elapsed_time > duration:
                print(f"已達到指定錄製時間：{duration} 秒")
                break
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("停止錄製視頻。")
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # 調用函數錄製視頻，保存為 'output.avi'
    # 可以指定錄製持續時間，例如 10 秒：record_video(duration=10)
    record_video(output_filename="../resources/output.avi", duration=None)
