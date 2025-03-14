import os
from zhipuai import ZhipuAI
from tqdm import tqdm
import json
import time
from openai import OpenAI

os.chdir(os.path.dirname(__file__))

openai_api_key = "sk-WSMhvS2cWeGRB6hU94Ff976288E94502A4Ca15Fa45248305"
openai_api_base = "http://139.224.116.116:3000/v1"
client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)


def process_pokemon_data(input_file, output_file):
    # 读取原始数据
    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # 定义提示词模板
    PROMPT_TEMPLATE = """你是一个宝可梦对话转换专家，请将下面的数据改写成自然对话格式：

    原始指令：{instruction}
    原始回复：{output}

    转换要求：
    1. 指令转换规则：
       - 资源请求类 ➔ "请问哪里可以找到{{资源}}？"
       - 更新咨询类 ➔ "{{作品}}的最新资源有更新吗？"
       - 知识咨询类 ➔ "请教大佬，{{具体问题}}"
       - 添加宝可梦元素 ➔ 使用"训练家","召唤师"等称呼，添加表情符号(・∀・)

    2. 回复转换规则：
       - 资源类 ➔ 提供网盘链接 + "点击精灵球图标获取！✨"
       - 技术问题 ➔ 分步骤说明 + 宝可梦梗举例
       - 数值问题 ➔ 用现实事物类比（如：相当于X个足球场）
       - 结尾添加 ➔ "就决定是你了！⚡" 等经典台词

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
                print(prompt)
                # 调用大模型
                response = client.chat.completions.create(
                    model="glm-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,  # 适当提高创造性
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
        input_file="final_data.json",  # 原始数据文件
        output_file="pokemon_conversation_data.json",  # 输出文件
    )
