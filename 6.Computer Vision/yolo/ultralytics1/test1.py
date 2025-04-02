from ultralytics import YOLO

def main():
    # 加载模型
    model = YOLO('yolov8n.pt')

    # 开始训练
    model.train(
        data='E:\\git\\ultralytics\\data\\VOC2007\\VOC.yaml',
        epochs=20,
        imgsz=640,
        batch=32,
        workers=8,
    )


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()  # 兼容 Windows 打包情况
    main()