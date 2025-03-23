import os


def combine_text_files(input_folder, output_file):
    # 获取指定文件夹中所有的 .txt 文件
    text_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]

    # 打开输出文件，以写模式写入合并后的内容
    with open(output_file, 'w', encoding='utf-8') as output:
        for file_name in text_files:
            file_path = os.path.join(input_folder, file_name)

            # 读取每个文本文件并写入输出文件
            with open(file_path, 'r', encoding='utf-8') as file:
                output.write(file.read())
    print(f"所有文本文件已经成功合并到 {output_file}")


# 使用脚本
input_folder = './'  # 替换为文本文件所在文件夹的路径
output_file = 'combined_text.txt'  # 输出合并后文件的路径
combine_text_files(input_folder, output_file)
