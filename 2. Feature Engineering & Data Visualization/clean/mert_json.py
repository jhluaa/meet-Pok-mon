import json
import glob

def merge_json_files(input_files, output_file):
    merged_data = []

    for file_path in input_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):  # 确保数据是列表
                    merged_data.extend(data)
        except Exception as e:
            print(f"⚠️ 读取 {file_path} 时发生错误: {e}")

    # 写入合并后的 JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

# 指定要合并的文件
json_files = [
    "1_clean_filtered.json",
    "2_clean_filtered.json",
    "3_clean_filtered.json",
    "4_clean_filtered.json",
    "5_clean_filtered.json",
    "6_clean_filtered.json",
    "douban_pokemon_book_processed.json",
    "douban_pokemon_movie_processed.json",
    "douban_pokemon_music_processed.json",
    "merged_answers.json"
]

# 目标输出文件
output_file = "../final_merged_data.json"

# 执行合并
# merge_json_files(json_files, output_file)


# 读取合并后的 JSON 文件并统计数据条数
with open(output_file, "r", encoding="utf-8") as f:
    merged_data = json.load(f)

# 统计总数据量
total_entries = len(merged_data)
print(total_entries)
