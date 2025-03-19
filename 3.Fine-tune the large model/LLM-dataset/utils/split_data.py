import json
import os
# 原始数据切割成10分
# 分割json文件的函数
def split_json(input_file, num_splits, output_dir):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_len = len(data)
    split_size = total_len // num_splits

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i in range(num_splits):
        start_index = i * split_size
        end_index = None if i == num_splits - 1 else (i + 1) * split_size
        split_data = data[start_index:end_index]

        output_file = os.path.join(output_dir, f'split_{i+1}.json')
        with open(output_file, 'w', encoding='utf-8') as f_out:
            json.dump(split_data, f_out, ensure_ascii=False, indent=4)

        print(f"生成文件: {output_file}, 数据条数: {len(split_data)}")

# 示例调用
if __name__ == "__main__":
    input_json_file = '../final_merged_data.json'  # 输入的json文件路径
    output_directory = 'splits'    # 输出目录
    num_splits = 10                # 需要分割成的文件数量

    split_json(input_json_file, num_splits, output_directory)
