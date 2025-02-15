# Kokoro FastAPI 使用说明

## 1. 用于 ONNX 调用
这部分内容可以根据实际需要进行详细描述，比如如何通过 ONNX 模型进行推理调用，或者如何配置 FastAPI 与 ONNX 配合使用。

## 2. 使用 Docker 启动 Kokoro FastAPI
使用 Docker 启动 Kokoro FastAPI，支持 CPU 和 GPU 版本。以下是两种常见的命令：

### 2.1 CPU 版本
```bash
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.2


### 2.2 GPU 版本
```bash

docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:v0.2.2

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8880/v1", api_key="not-needed"
)

with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="af_sky+af_bella",  # 单个或多个语音包组合
    input="Hello world!"
) as response:
    response.stream_to_file("output.mp3")

# 终端映射端口  如 docker run -p 8081:8880 ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.2