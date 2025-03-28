from langchain_text_splitters import RecursiveCharacterTextSplitter

# 初始化分割器
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""],  # 分隔符列表
    chunk_size=10,  # 每块文本的最大长度
    chunk_overlap=2  # 块之间的重叠长度
)

# 示例文本
text = "这是一个示例文本\n\n它包含多个句子\n\n用于演示如何使用\n\nRecursiveCharacterTextSplitter\n\n进行文本分割。"

# 分割文本
print(text_splitter.split_text(text))
