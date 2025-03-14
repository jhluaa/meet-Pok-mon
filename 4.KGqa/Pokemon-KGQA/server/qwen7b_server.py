from flask import Flask, request, jsonify
from openai import OpenAI

# 初始化 OpenAI 配置
openai_api_key = "sk-WSMhvS2cWeGRB6hU94Ff976288E94502A4Ca15Fa45248305"
openai_api_base = "http://139.224.116.116:3000/v1"
client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)


def predict_model(data):
    try:
        # 合并历史消息和当前消息
        messages = data.get("history", []) + data["message"]
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            temperature=data.get("temperature", 0.8),
            max_tokens=data.get("max_tokens", 100),
            top_p=data.get("top_p", 0.9),
        )
        # 提取回复内容，并更新历史记录
        reply = response.choices[0].message.content
        updated_history = messages + [{"role": "assistant", "content": reply}]
        return reply, updated_history
    except Exception as e:
        return str(e), []


app = Flask(__name__)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    print("收到请求:", data)

    try:
        reply, updated_history = predict_model(data)
        return jsonify(
            {
                "output": [reply],
                "history": updated_history,  # 返回更新后的历史记录
                "status": "success",
            }
        )
    except Exception as e:
        return jsonify({"output": [str(e)], "history": [], "status": "error"})


if __name__ == "__main__":
    app.run(port=3001, debug=False, host="0.0.0.0")
