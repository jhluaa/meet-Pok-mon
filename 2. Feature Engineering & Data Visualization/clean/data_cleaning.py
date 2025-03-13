import json
import re


def clean_comment(comment):
    """ 清理 comment 字符串，去掉无效内容 """
    if not comment or comment.lower() in ["无", "暂无"]:
        return ""

    # 去除网页链接、提取码等
    comment = re.sub(r'链接[:：]?\s*网页链接', '', comment)
    comment = re.sub(r'提取码[:：]?\s*[a-zA-Z0-9]+', '', comment)
    comment = re.sub(r'网盘链接', '', comment)

    # 去除连续重复的字符或无意义的占位符
    comment = re.sub(r'(d\s*){5,}', '', comment)  # 过滤掉 "d d d d d d ..."
    comment = re.sub(r'[\n\s]+', ' ', comment).strip()  # 统一换行和空格

    return comment


def process_data(input_path, output_path):
    """ 读取 JSON 数据并转换为微调格式 """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    output_data = []

    for item in data:
        title = item.get('title', '').strip()
        comment = clean_comment(item.get('comment', '').strip())

        # 过滤无效数据
        if not title or not comment:
            continue

        output_data.append({
            "instruction": title,
            "input": "",
            "output": comment,
            "history": []
        })

    # 写入处理后的 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)


# 运行转换
input_file = "../2_clean_filtered.json"  # 替换为实际文件路径
output_file = "../2_clean_filtered.json"
process_data(input_file, output_file)

