import json


def clean_text(text):
    """去除空白和无效字符"""
    return text.strip() if text and text != "无" else ""


def process_record(record):
    """处理单条记录，转换为微调格式"""
    instruction = clean_text(record.get("title", ""))
    if not instruction:
        return None  # 跳过没有标题的数据

    book_info = clean_text(record.get("book_info", ""))
    rating = clean_text(record.get("rating", ""))
    content = clean_text(record.get("content", ""))

    # 处理评论（reviews 是字符串形式的列表）
    try:
        reviews = json.loads(record.get("reviews", "[]"))
        reviews_text = "\n".join([clean_text(r) for r in reviews if clean_text(r)])
    except json.JSONDecodeError:
        reviews_text = ""

    # 组装 output
    output_parts = []
    if book_info:
        output_parts.append(f"{book_info}")
    if rating and rating != "无评分":
        output_parts.append(f"该歌曲的评分为 {rating} 分。")
    if content:
        output_parts.append(f"内容简介：{content}")
    if reviews_text:
        output_parts.append(f"用户评价：\n{reviews_text}")

    output = "\n\n".join(output_parts).strip()
    if not output:
        return None  # 没有内容的跳过

    return {
        "instruction": instruction,
        "input": "",
        "output": output,
        "history": []
    }


def process_json(input_path, output_path):
    """读取 JSON 并处理数据"""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("RECORDS", [])
    processed_data = [process_record(record) for record in records]
    processed_data = [d for d in processed_data if d]  # 过滤 None 记录

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)


# 运行转换
input_file = "douban_pokemon_book.json"
output_file = "../raw_data/douban_pokemon_book_processed.json"
process_json(input_file, output_file)


