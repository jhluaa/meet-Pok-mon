import json


def extract_事项名称(json_file, output_file):
    try:
        # 打开并加载 JSON 数据
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取所有的 事项名称
        事项名称_list = [item.get("事项名称") for item in data]

        # 将结果写入 a.txt
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in 事项名称_list:
                f.write(item + '\n')

        print(f"成功将事项名称写入 {output_file}")

    except Exception as e:
        print(f"发生错误: {e}")


# 调用函数，传入 JSON 文件路径和输出 TXT 文件路径
extract_事项名称('data.json', 'ban_zhuti.txt')
