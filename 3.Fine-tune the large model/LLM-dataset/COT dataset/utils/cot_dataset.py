import os
import json
import re
from tqdm import tqdm
import time
from openai import OpenAI

os.chdir(os.path.dirname(__file__))

openai_api_key = "sk_jbnY4jsUamy1p0mKQRSBWdKcdsL3fJstL5ZNjGqXprY"
openai_api_base = "https://api.ppinfra.com/v3/openai"
client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)

def save_txt_entry(output_file, text):
    """将文本以追加方式保存到输出文件中"""
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

def update_input_file(input_file, dataset):
    """实时更新原始数据文件，将已处理的数据移除"""
    remaining = [d for d in dataset if d is not None]
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=4)

def clean_response(response_content):
    """清理返回内容中的代码块标记和未转义的换行符"""
    if response_content.startswith("```json"):
        response_content = response_content[len("```json"):].strip()
    if response_content.endswith("```"):
        response_content = response_content[:-len("```")].strip()
    response_content = re.sub(r'(?<!\\)\n', r'\\n', response_content)
    return response_content

def process_pokemon_data(input_file, output_file):
    # 读取原始数据
    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    PROMPT_TEMPLATE = """你的任务是将给定的指令（instruction）和原始回答（output）改写为包含清晰思考过程的 **Chain-of-Thought (CoT)** 风格答案。

请遵循以下要求完成改写：

1. **输出格式**：必须输出 JSON 格式的数据对象，包含 "instruction" 和 "output" 两个字段。
2. **思考过程**：在 "output" 字段中，先给出详细的推理思考过程，并使用 <think>...</think> 标签将这一过程包裹起来；然后在 </think> 标签之后给出最终的答案。
3. **内容优化**：可以在合理范围内对原始回答进行改写或优化，使其更清晰、规范和合理。不必拘泥于原回答的措辞或格式，尤其当原回答不清晰或不规范时，可以进行调整，但需确保最终答案与指令要求相符，内容准确无误。
4. **指令保持**：JSON 输出中的 "instruction" 字段内容应与提供的指令完全一致，不进行任何改动。
5. **仅输出 JSON**：请直接给出满足上述要求的 JSON 对象，不要包含解释、注释或额外的文本。

现在，我将提供一个指令和对应的原始回答，请根据上述要求生成包含思考过程的新版回答，并以 JSON 格式输出。

**Instruction**：{instruction}
**原始回答**：{output}

请根据以上输入，输出转换后的 JSON 格式数据，例如：

{{
    "instruction": "{instruction}",
    "output": "<think>这里写下详细的思考推理过程……</think> 最终的回答内容"
}}
"""

    for i, item in enumerate(tqdm(dataset)):
        if item is None:
            continue
        max_retries = 1
        for attempt in range(max_retries):
            try:
                prompt = PROMPT_TEMPLATE.format(
                    instruction=item["instruction"],
                    output=item["output"]
                )

                response = client.chat.completions.create(
                    model="deepseek/deepseek-r1/community",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )

                response_content = response.choices[0].message.content
                response_content = clean_response(response_content)

                # 直接保存整个返回内容
                print("返回内容:", response_content)
                save_txt_entry(output_file, response_content)

                dataset[i] = None
                # update_input_file(input_file, dataset)
                # break

            except Exception as e:
                print(f"第 {i} 条数据处理失败，重试 {attempt+1}/{max_retries}")
                time.sleep(2**attempt)
                if attempt == max_retries - 1:
                    with open("error_log.txt", "a", encoding="utf-8") as log:
                        log.write(f"Index: {i}\nError: {str(e)}\nOriginal data: {json.dumps(item, ensure_ascii=False)}\n\n")
                    dataset[i] = None
                    # update_input_file(input_file, dataset)

if __name__ == "__main__":
    process_pokemon_data(
        input_file=r"pokemon_data_1.json",  # 原始数据文件
        output_file="pokemon_data_1_cot.txt"  # 输出文本文件
    )
