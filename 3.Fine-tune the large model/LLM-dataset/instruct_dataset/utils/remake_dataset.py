import os
import json
from tqdm import tqdm
import time
from openai import OpenAI

os.chdir(os.path.dirname(__file__))

openai_api_key = "sk-KKlEkGNKAxhX1ZvCzGkGfwVBcYyCV3SUpoYtYoSjTQEvrvxB"
openai_api_base = "https://api.hunyuan.cloud.tencent.com/v1"
client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)


def save_json_entry(output_file, entry):
    """保存一条新的数据到JSON文件中"""
    with open(output_file, "a", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=4)
        f.write(",\n")


def process_pokemon_data(input_file, output_file):
    # 读取原始数据
    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # 定义提示词模板
    PROMPT_TEMPLATE = """你是一名具有丰富经验的宝可梦世界对话问答专家。你的任务是将以下原始数据，重写对话内容。

    原始指令：{instruction}
    原始回复：{output}

    请遵循以下转换规则：

    - 指令转换规则：
      严肃地模拟真实人类向大模型直接提出问题的口吻提出问题。不要加问候语直接问问题，不要加 你 我 他 这种主语

    回复转换规则：
    - 将原始回复转写成大模型式回答。不要加人物，你只是一个大模型解答助手，而不是某一个人，如果回复很奇怪，那么请你参考回复自己生成答案 不要加问候语直接问问题

    示例说明：
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

                # 调用大模型
                response = client.chat.completions.create(
                    model="hunyuan-turbo",
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

                # 解析JSON
                try:
                    result = json.loads(response_content)
                    instruction = result.get("instruction", "")
                    output = result.get("output", "")

                    print("Instruction:", instruction)
                    print("Output:", output)

                    # 保存结果到目标文件
                    save_json_entry(output_file, {
                        "instruction": instruction,
                        "input": "",
                        "output": output,
                        "history": [],
                    })

                    # 删除源文件中已处理的数据
                    del dataset[i]

                    # 退出重试循环
                    break  # 成功则跳出重试循环

                except json.JSONDecodeError as e:
                    print("JSON 解析失败:", e)
                    print("返回的内容:", response_content)

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

    # 更新源文件，删除已处理的数据
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":

    process_pokemon_data(
        input_file=r"../split_10.json",  # 原始数据文件 2
        output_file="pokemon_data_10.json",  # 输出文件1  2
    )
