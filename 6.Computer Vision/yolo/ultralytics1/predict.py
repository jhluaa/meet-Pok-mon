from ultralytics import YOLO

# 加载模型
model = YOLO('yolov8n.pt')

# 进行预测（会自动保存到 runs/predict/ 目录）
results = model.predict(
    source='E:\\git\\ultralytics\\data\\VOC2007\\images\\val\\00892.jpg',
    save=True,        # 保存预测图像
    show=True,        # 弹窗显示
    save_txt=True     # 保存预测框坐标
)