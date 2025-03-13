#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sys

def contains_gibberish(text: str) -> bool:
    """
    简单检测是否包含常见的乱码字符或序列。
    这里列出了一些常见乱码字符(可根据需要扩展)。
    """
    suspicious_chars = ["æ", "ä", "å", "ç", "è", "é", "â", "ã", "¤", "�"]
    for c in suspicious_chars:
        if c in text:
            return True
    return False

def clean_comment(comment: str) -> str:
    """
    对 comment 进行简单清洗，包括：
    1. 去除换行符
    2. 删除 URL
    3. 去除多余空白
    """
    # 1. 替换换行符为空格
    comment = comment.replace('\n', ' ')
    # 2. 删除 URL（若不需要删除可以注释掉下面这行）
    comment = re.sub(r'http\S+', '', comment)
    # 3. 合并多余空白并去掉首尾空白
    comment = re.sub(r'\s+', ' ', comment).strip()
    return comment

def main(input_file: str, output_file: str):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 假设你的 JSON 文件有一个叫 "RECORDS" 的字段，里面是数组
    records = data.get("RECORDS", [])

    output_data = []

    for item in records:
        # 获取 title、comment
        title = item.get('title', '')
        comment = item.get('comment', '')

        # 如果原始 comment 有明显乱码，就跳过
        if contains_gibberish(comment):
            continue

        # 清洗 comment
        cleaned_comment = clean_comment(comment)

        # 如果清洗后为空，则跳过
        if not cleaned_comment:
            continue

        # 构造训练/微调需要的结构
        record = {
            "instruction": title,
            "input": "",
            "output": cleaned_comment,
            "history": []
        }

        output_data.append(record)

    # 最后将 output_data 输出到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # 命令行使用：python script.py input.json output.json
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_json_file> <output_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)
