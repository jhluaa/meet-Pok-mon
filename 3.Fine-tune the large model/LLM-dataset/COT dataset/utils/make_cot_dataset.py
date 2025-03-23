import json
import re

def process_input_file(input_file):
    # 打开并读取txt文件内容
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # 初始化输出列表
    output_list = []

    # 使用正则表达式匹配多个数据条目
    data_entries = re.findall(r'\{(.*?)\}', content, re.DOTALL)

    for entry in data_entries:
        output_ = {
            "instruction": "",
            "input": "",
            "output": "",
            "history":[]
        }

        # 提取 instruction 部分
        instruction_match = re.search(r'"instruction":\s?"(.*?)"', entry)
        if instruction_match:
            output_["instruction"] = instruction_match.group(1).strip()

        # 提取 output 部分
        output_match = re.search(r'"output":\s?"(.*?)"', entry, re.DOTALL)
        if output_match:
            output_["output"] = output_match.group(1).strip()  # 直接提取 output 内容

        output_list.append(output_)

    # 返回结果为 JSON 格式
    return json.dumps(output_list, ensure_ascii=False, indent=4)

# 调用函数
input_file = "combined_text.txt"  # 输入文件路径
processed_json = process_input_file(input_file)
print(processed_json)

# 如果需要保存到文件
with open("output.json", "w", encoding="utf-8") as json_file:
    json_file.write(processed_json)
