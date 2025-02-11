import os

MOT17_ROOT = "/data/PaddlePaddle/PaddleDetection/dataset/mot/mot_zhengwu"

# 输出的列表文件放在哪里
IMAGE_LIST_DIR = "/data/PaddlePaddle/PaddleDetection/dataset/mot/image_lists"
OUTPUT_FILE = os.path.join(IMAGE_LIST_DIR, "mot_zhengwu.train")

def main():
    train_dir = os.path.join(MOT17_ROOT, "images", "train")
    # 获取训练集下所有序列文件夹，如 ["MOT17-02", "MOT17-04", ...]
    seqs = sorted(os.listdir(train_dir))

    lines = []
    for seq in seqs:
        seq_path = os.path.join(train_dir, seq, "img1")
        if not os.path.isdir(seq_path):
            continue
        # 获取img1里所有.jpg 文件
        img_names = sorted(os.listdir(seq_path))
        for img_name in img_names:
            if img_name.lower().endswith(".jpg"):
                # 拼接成绝对路径
                abs_path = os.path.join(seq_path, img_name)
                abs_path = os.path.abspath(abs_path)
                lines.append(abs_path)

    # 确保输出目录存在
    os.makedirs(IMAGE_LIST_DIR, exist_ok=True)
    # 写到 mot17.train
    with open(OUTPUT_FILE, "w") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"生成 {OUTPUT_FILE} 完成，共 {len(lines)} 行")

if __name__ == "__main__":
    main()
