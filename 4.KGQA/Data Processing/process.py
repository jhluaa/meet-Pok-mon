import csv
import json
import re

# # 输入的CSV文件路径
# input_csv_file = '/disease-kb/DATAsets/Affair.csv'
#
# # 输出的TXT文件路径
# output_txt_file = 'Affair.txt'
#
# # 打开并读取CSV文件（使用 utf-8-sig 以处理 BOM）
# with open(input_csv_file, mode='r', encoding='utf-8-sig') as csv_file:
#     csv_reader = csv.reader(csv_file)
#
#     # 打开输出文件进行写入
#     with open(output_txt_file, mode='w', encoding='utf-8') as txt_file:
#         for row in csv_reader:
#             # 读取每一行，可能没有适当的双引号
#             json_str = row[0].replace('""', '"')  # 去除多余的双引号
#
#             # 使用正则表达式修正没有引号的 JSON 格式字符串
#             json_str = re.sub(r'\"name\":([^\"]+)', r'\"name\":\"\1\"', json_str)  # 给 name 字段值添加双引号
#             json_str = re.sub(r'“|”', '"', json_str)  # 将中文引号转换为英文引号
#
#             try:
#                 # 解析为字典
#                 data = json.loads(json_str)
#                 name = data.get('name', '')  # 提取 'name' 字段
#                 if name:  # 如果有有效的 'name' 字段
#                     txt_file.write(name + "\n")  # 每个实体名称占一行
#             except json.JSONDecodeError as e:
#                 print(f"解析失败: {row[0]}")  # 输出无法解析的行
#                 continue
#
# print(f"数据已成功保存到 {output_txt_file}")
#
#
# mai
if __name__ == '__main__':
    import re

    # 输入 CSV 文件路径和输出 TXT 文件路径
    # input_csv = "/data/KGqa/disease-kb/DATAsets/Dept.csv"
    # output_txt = '/data/KGqa/disease-kb/DATAsets/Dept.txt'
    #
    # # 打开 CSV 文件进行读取
    # with open(input_csv, mode='r', encoding='utf-8') as csv_file:
    #     # 打开 TXT 文件进行写入
    #     with open(output_txt, mode='w', encoding='utf-8') as txt_file:
    #         # 遍历每一行数据
    #         for line in csv_file:
    #             # 使用正则表达式提取 : 后面的内容
    #             match = re.search(r'":([^}]+)', line)
    #             if match:
    #                 # 提取匹配到的内容并写入 TXT 文件
    #                 extracted_text = match.group(1)
    #                 txt_file.write(extracted_text + '\n')
    #
    # print(f"处理完成，结果已保存到 {output_txt}")
    import re
    import json
    import csv

    input_csv = "/data/KGqa/disease-kb/DATAsets/File.csv"
    output_txt = '/data/KGqa/disease-kb/DATAsets/File.json'
    error_csv = '/data/KGqa/disease-kb/DATAsets/a.csv'  # 错误数据保存路径

    # 读取CSV文件
    with open(input_csv, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)

        # 用于保存所有JSON数据
        json_list = []

        # 用于保存错误数据
        error_data = []

        for row in csv_reader:
            # 假设每一行是类似"{""name"":关联的证据,""source"":申请人自备,""id"":887115,...}"的格式
            raw_data = row[0]  # 假设数据在第一列

            # 1. 替换多余的双引号
            data_fixed = re.sub(r'""', '"', raw_data)

            # 2. 给所有的字符串值加双引号
            data_fixed = re.sub(r'(:)([^\s,{}]+)(?=\s|,|})', r'\1"\2"', data_fixed)

            # 3. 给 URL 加双引号
            data_fixed = re.sub(r'(:)(http[^\s,}]+)', r'\1"\2"', data_fixed)

            # 4. 如果字段值为空，填充为空字符串
            data_fixed = re.sub(r':\s*,', r':""', data_fixed)  # 替换空字段为 ""

            # 5. 处理字段空值，检查没有值的字段并替换
            data_fixed = re.sub(r':\s*$', r':""', data_fixed)  # 处理字段后没有值的情况

            # 6. 尝试将修复后的字符串解析为 JSON 对象
            try:
                json_data = json.loads(data_fixed)
                json_list.append(json_data)  # 将解析后的 JSON 数据添加到列表
            except json.JSONDecodeError as e:
                print(f"JSON 解析错误: {e}，原数据: {raw_data}")
                error_data.append([raw_data])  # 保存原始错误数据到列表

    # 将结果保存为 JSON 文件
    with open(output_txt, 'w', encoding='utf-8') as json_file:
        json.dump(json_list, json_file, ensure_ascii=False, indent=4)

    # 保存错误数据到 CSV 文件
    if error_data:
        with open(error_csv, mode='w', encoding='utf-8', newline='') as error_file:
            error_writer = csv.writer(error_file)
            error_writer.writerow(["raw_data"])  # 写入表头
            error_writer.writerows(error_data)  # 写入错误数据

    print(f"处理完成，结果已保存到 {output_txt}")
    if error_data:
        print(f"解析错误的数据已保存到 {error_csv}")


