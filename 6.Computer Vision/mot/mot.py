import os
import json
# 使用X-anylabeling 生成json格式文件 然后使用该脚本生成MOT groundTrue.txt文件
#JSON文件夹路径 (anns)
ANN_DIR = "/data/ultralytics/anns"
#输出的MOTgt.txt文件
OUTPUT_TXT = "gt.txt"

def main():
    # 1) 获取所有 .json 文件列表，并排序
    ann_files = [f for f in os.listdir(ANN_DIR) if f.lower().endswith(".json")]
    ann_files.sort()  # 按文件名排序，例如 00019.json -> 00020.json -> ...

    # 创建一个字典，用于映射帧号(原始帧->新帧)
    frame_map = {}
    new_frame_id = 1

    # 2) 填充frame_map构建帧号映射
    for ann_name in ann_files:
        base_name = os.path.splitext(ann_name)[0]  # "00121"
        try:
            old_frame_id = int(base_name)  # 121
        except ValueError:
            continue

        if old_frame_id not in frame_map:
            frame_map[old_frame_id] = new_frame_id
            new_frame_id += 1

    all_lines = []  # 用来存储所有帧的标注行

    # 3) 读取每个JSON文件并处理
    for ann_name in ann_files:
        ann_path = os.path.join(ANN_DIR, ann_name)

        # 4)从文件名解析帧号: "00019.json" -> 19
        base_name = os.path.splitext(ann_name)[0]  # "00019"
        try:
            old_frame_id = int(base_name)  # 19
        except ValueError:
            continue

        # 使用frame_map将原帧号映射成新帧号
        frame_index = frame_map.get(old_frame_id, None)
        if frame_index is None:
            continue  #如果没有找到映射，跳过

        # 5) 读取JSON数据
        with open(ann_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 6) 解析shapes部分
        shapes = data.get("shapes", [])
        for shape in shapes:
            label = shape.get("label", "")
            # 如果只关心 "person"，可以在此过滤:
            # if label != "person":
            #     continue

            # track_id: 用 group_id 或其他可标识同一目标的字段
            track_id = shape.get("group_id", 0)
            if track_id is None:
                track_id = 0

            # 7) 取出标注点
            points = shape.get("points", [])
            if len(points) < 2:
                # 不足以构成矩形，跳过
                continue

            # 8) 计算外接矩形 (x, y, w, h)
            xs = [pt[0] for pt in points]
            ys = [pt[1] for pt in points]
            left, right = min(xs), max(xs)
            top, bottom = min(ys), max(ys)
            w = right - left
            h = bottom - top

            # 如果你需要过滤小框，可在此判断w,h是否过小

            # MOT的gt.txt中，这几个字段：frame, track_id, x, y, w, h, valid, class_id, visibility
            valid = 1  # 不忽略此框
            class_id = 1  # 如果只有人，可以统一填 1
            visibility = 1  # 如果没额外信息，就填 1

            # 9) 构造一行字符串 9 个值 当然MOT17是 10个 unused -1
            line = f"{frame_index},{track_id},{left:.2f},{top:.2f},{w:.2f},{h:.2f},{valid},{class_id},{visibility}"
            all_lines.append(line)
    # 10) 按帧号排序
    def get_frame_num(line):
        return int(line.split(",")[0])

    all_lines.sort(key=get_frame_num)

    # 11) 写出到 gt.txt
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for line in all_lines:
            f.write(line + "\n")

    print(f"转换完成，共处理 {len(ann_files)} 个 JSON 文件，输出保存到: {OUTPUT_TXT}")


if __name__ == "__main__":
    main()
