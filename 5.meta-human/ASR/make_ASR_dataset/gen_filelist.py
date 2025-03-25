import os
import chardet

# 📌 1️⃣ 检测文件编码
def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result["encoding"]

# 📌 2️⃣ 将 `.lab` 文件转换为 UTF-8
def convert_to_utf8(file_path):
    encoding = detect_encoding(file_path)
    if encoding and encoding.lower() != 'utf-8':  # 如果不是 UTF-8，则转换
        print(f"正在转换 {file_path} 从 {encoding} 到 UTF-8")
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

# 📌 3️⃣ 处理 `.lab` 文件并生成 `full.txt`
def process():
    persons = ['swk']
    ch_language = 'ZH'
    out_file = "filelists/full.txt"

    # 确保文件夹存在
    os.makedirs("filelists", exist_ok=True)

    with open(out_file, 'w', encoding="utf-8") as wf:
        for person in persons:
            path = f"./data/short/{person}"
            if not os.path.exists(path):
                print(f"❌ 目录不存在: {path}")
                continue

            files = os.listdir(path)
            for f in files:
                if f.endswith(".lab"):
                    file_path = os.path.join(path, f)

                    # 🚀 确保所有 `.lab` 文件都是 UTF-8
                    convert_to_utf8(file_path)

                    # 🚀 读取 `.lab` 内容
                    with open(file_path, 'r', encoding="utf-8", errors="ignore") as perFile:
                        line = perFile.readline().strip()
                        result = f"./data/short/{person}/{f.split('.')[0]}.wav|{person}|{ch_language}|{line}"
                        wf.write(f"{result}\n")

                    print(f"✅ 处理完成: {file_path}")

if __name__ == "__main__":
    process()
