import json


def remove_first_n_entries(json_file, n):
    """
    删除 JSON 文件中的前 n 条数据，并覆盖原文件。

    :param json_file: JSON 文件路径
    :param n: 需要删除的条目数
    """
    try:
        # 读取 JSON 文件
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 确保数据是一个列表
        if not isinstance(data, list):
            print("❌ JSON 文件格式错误，数据应为数组列表。")
            return

        # 计算剩余数据
        if n >= len(data):
            print(f"⚠️ 要删除的数据条数（{n}）大于或等于总数（{len(data)}），将清空文件！")
            remaining_data = []
        else:
            remaining_data = data[n:]

        # 将剩余数据写回文件
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(remaining_data, f, ensure_ascii=False, indent=4)

        print(f"✅ 已删除前 {n} 条数据，剩余 {len(remaining_data)} 条数据。")

    except json.JSONDecodeError:
        print("❌ 解析 JSON 失败，请检查文件格式是否正确！")
    except FileNotFoundError:
        print(f"❌ 文件 {json_file} 未找到，请检查路径！")
    except Exception as e:
        print(f"❌ 发生错误：{e}")


# 示例用法：删除 JSON 文件 "data.json" 中的前 5 条数据
remove_first_n_entries("../split_3.json", 321)
