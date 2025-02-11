import os

# 输入的图像目录路径（假设是 imgs）
IMG_DIR = "/data/ultralytics/201_20241104_172122"
# 输出的图像目录路径（可以和输入路径相同）
OUTPUT_DIR = "/data/ultralytics/renamed_imgs"

# 获取文件夹内所有图像文件并排序
img_files = sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(".jpg")])

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 重命名并复制文件
for idx, img_name in enumerate(img_files):
    # 根据排序后的文件列表生成新的文件名
    new_name = f"{idx + 1:05d}.jpg"  # 格式化为 00001.jpg, 00002.jpg, ...

    # 原始文件路径
    old_path = os.path.join(IMG_DIR, img_name)

    # 新文件路径
    new_path = os.path.join(OUTPUT_DIR, new_name)

    # 复制并重命名
    os.rename(old_path, new_path)
    print(f"Renamed: {img_name} -> {new_name}")

print(f"Renaming complete. Files are saved to {OUTPUT_DIR}")
