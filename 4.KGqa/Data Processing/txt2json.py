import json
import re

def txt_to_json(txt_file, json_file):
    with open(txt_file, 'r', encoding='utf-8') as file:
        data = file.read()

    # 用 ==##########== 作为分隔符分割文本数据
    items = data.split('==##########==')

    # 定义一个列表来存储每个事项的数据
    result = []

    # 定义去除括号及其内容的正则表达式
    def remove_brackets(text):
        return re.sub(r"（.*?）", "", text).strip()

    for item in items:
        if not item.strip():
            continue  # 跳过空项

        # 每个事项的字典
        item_data = {}

        # 按行分割每个事项
        lines = item.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 解析每一行数据
            if line.startswith("事项名称"):
                item_data['事项名称'] = line.split("：")[-1].strip()
            elif line.startswith("事项类型"):
                item_data['事项类型'] = line.split("：")[-1].strip()
            elif line.startswith("基本编码"):
                item_data['基本编码'] = line.split("：")[-1].strip()
            elif line.startswith("业务办理项编码"):
                item_data['业务办理项编码'] = line.split("：")[-1].strip()
            elif line.startswith("行使层级"):
                item_data['行使层级'] = line.split("：")[-1].strip()
            elif line.startswith("办理形式"):
                item_data['办理形式'] = [x.strip() for x in line.split("：")[-1].strip().split(',')]
            elif line.startswith("实施主体"):
                match = re.match(r"实施主体：(.+)", line)
                if match:
                    item_data['实施主体'] = match.group(1).strip()
                match = re.match(r"实施主体编码：(.+)", line)
                if match:
                    item_data['实施主体编码'] = match.group(1).strip()
                match = re.match(r"实施主体性质：(.+)", line)
                if match:
                    item_data['实施主体性质'] = match.group(1).strip()
            elif line.startswith("权力来源"):
                item_data['权力来源'] = line.split("：")[-1].strip()
            elif line.startswith("是否进驻政务大厅"):
                item_data['是否进驻政务大厅'] = line.split("：")[-1].strip()
            elif line.startswith("办理地点"):
                item_data['办理地点'] = line.split("：")[-1].strip()
            elif line.startswith("办理时间"):
                item_data['办理时间'] = line.split("：")[-1].strip()
            elif line.startswith("服务对象"):
                item_data['服务对象'] = line.split("：")[-1].strip()
            elif line.startswith("受理条件"):
                item_data['受理条件'] = line.split("：")[-1].strip()
            elif line.startswith("办件类型"):
                item_data['办件类型'] = line.split("：")[-1].strip()
            elif line.startswith("法定办结时限"):
                item_data['法定办结时限'] = line.split("：")[-1].strip()
            elif line.startswith("承诺办结时限"):
                item_data['承诺办结时限'] = line.split("：")[-1].strip()
            elif line.startswith("收费情况"):
                item_data['收费情况'] = line.split("：")[-1].strip()
            elif line.startswith("咨询方式"):
                item_data['咨询方式'] = line.split("：")[-1].strip()
            elif line.startswith("监督投诉方式"):
                item_data['监督投诉方式'] = line.split("：")[-1].strip()
            elif line.startswith("行政相对人权利和义务"):
                item_data['行政相对人权利和义务'] = line.split("：")[-1].strip()
            elif line.startswith("办理材料"):
                item_data['办理材料'] = [x.strip() for x in re.split(r'\s{2,}', line.split("：")[-1].strip())]
            elif line.startswith("办理流程"):
                item_data['办理流程'] = [x.strip() for x in re.split(r'\s{2,}', line.split("：")[-1].strip())]

        # 将每个事项添加到结果列表中
        result.append(item_data)

    # 将结果写入 json 文件
    try:
        with open(json_file, 'w', encoding='utf-8') as json_out:
            json.dump(result, json_out, ensure_ascii=False, indent=4)
        print(f"成功写入 {json_file}")
    except Exception as e:
        print(f"写入文件时出错: {e}")


# 调用函数，输入txt文件路径和输出json文件路径
txt_to_json('../DATAsets/data.txt', 'data.json')
