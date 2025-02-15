from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8081/v1", api_key="not-needed"
)

with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="af_sky+af_bella",  # 单个或多个语音包组合
    input="Hello world!"
) as response:
    response.stream_to_file("output.mp3")
