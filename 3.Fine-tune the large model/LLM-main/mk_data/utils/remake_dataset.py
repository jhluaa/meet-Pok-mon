import os
from tqdm import tqdm
import json
import time
from openai import OpenAI

os.chdir(os.path.dirname(__file__))

openai_api_key = "sk-7egdiZg0g9LaGJnX4973895138C148FbAcF5E96e1cAdEd00"
openai_api_base = "http://139.224.116.116:3000/v1"
client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)


def process_pokemon_data(input_file, output_file):
    # 读取原始数据
    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # 定义提示词模板
    PROMPT_TEMPLATE = """你是一名富有创意、幽默感十足的宝可梦世界对话问答专家。你的任务是将以下原始数据，重新创作为真实人类之间的对话。

    原始指令：{instruction}
    原始回复：{output}

    请遵循以下转换规则：

    - 指令转换规则：
      严肃地模拟真实人类向大模型直接提出问题的口吻提出问题。

    回复转换规则：
    - 将原始回复转写成自然、顺畅且带有幽默感的回答，仿佛是一位知识渊博的宝可梦导游在亲切地与游客交谈。

    请输出JSON格式（只包含instruction和output字段）：
    """

    # 处理数据
    for i, item in enumerate(tqdm(dataset)):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 构造提示词
                prompt = PROMPT_TEMPLATE.format(
                    instruction=item["instruction"], output=item["output"]
                )
                # print(prompt)
                # 调用大模型
                response = client.chat.completions.create(
                    model="glm-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # 适当提高创造性
                )

                response_content = response.choices[0].message.content

                # 解析结果
                # 获取返回的内容
                # 去掉 ```json 和 ``` 代码块
                response_content = (
                    response_content.strip("```json").strip("```").strip()
                )
                # print(response_content)
                # exit()
                # 解析JSON
                try:
                    result = json.loads(response_content)
                    instruction = result.get("instruction", "")
                    output = result.get("output", "")

                    print("Instruction:", instruction)
                    print("Output:", output)

                except json.JSONDecodeError as e:
                    print("JSON 解析失败:", e)
                    print("返回的内容:", response_content)

                # 保存结果
                with open(output_file, "a", encoding="utf-8") as f:
                    json.dump(
                        {
                            "instruction": instruction,
                            "input": "",
                            "output": output,
                            "history": [],
                        },
                        f,
                        ensure_ascii=False,
                    )
                    f.write(",\n")

                break  # 成功则跳出重试循环

            except Exception as e:
                print(f"第{i}条数据处理失败，重试{attempt + 1}/{max_retries}")
                time.sleep(2**attempt)  # 指数退避
                if attempt == max_retries - 1:
                    with open("error_log.json", "a") as log:
                        json.dump(
                            {"index": i, "error": str(e), "original_data": item},
                            log,
                            ensure_ascii=False,
                        )
                        log.write("\n")


if __name__ == "__main__":
    # 示例用法
    process_pokemon_data(
        input_file=r"D:\meet-Pok-mon\3.Fine-tune the large model\LLM-main\mk_data\splits\split_1.json",  # 原始数据文件
        output_file="splits/pokemon_data_1.json",  # 输出文件
    )
