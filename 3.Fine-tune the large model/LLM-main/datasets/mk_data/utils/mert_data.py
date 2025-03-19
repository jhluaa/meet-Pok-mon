import os
import json

def merge_json_files(directory, output_file="merged.json"):
    merged_data = []  # 用于存储所有 JSON 记录

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_data = f.read().strip()

                    # 尝试解析 JSON，如果是多个 JSON 对象，则拆分
                    try:
                        # 直接尝试加载 JSON
                        data = json.loads(raw_data)
                        if isinstance(data, list):
                            merged_data.extend(data)
                        else:
                            merged_data.append(data)
                    except json.JSONDecodeError:
                        # 尝试按行解析 JSON
                        json_objects = raw_data.split("\n")
                        for obj in json_objects:
                            try:
                                parsed_obj = json.loads(obj.strip())
                                merged_data.append(parsed_obj)
                            except json.JSONDecodeError:
                                print(f"警告: 文件 {filename} 中某行无法解析，已跳过")
            except Exception as e:
                print(f"无法解析 {filename}: {e}")

    # 将合并后的数据写入新的 JSON 文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

    print(f"合并完成，已保存到 {output_file}")

# 调用函数，指定要合并的文件夹路径
if __name__ == "__main__":
    folder_path = ""  # 修改为你的 JSON 文件所在的文件夹路径
    merge_json_files(folder_path)
