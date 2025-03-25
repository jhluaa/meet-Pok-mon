import requests
import os


def detect_language(audio_file_path: str, api_url: str = "http://localhost:9000/detect-language") -> dict:
    """
    调用 /detect-language 接口，识别音频文件的语言信息
    :param audio_file_path: 音频文件的本地路径
    :param api_url: 检测语言的 API 端点，默认为 http://localhost:9000/detect-language
    :return: 返回接口响应的 JSON（包括语言检测结果等）
    """
    if not os.path.isfile(audio_file_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")

    with open(audio_file_path, "rb") as f:
        files = {"audio_file": f}
        try:
            resp = requests.post(api_url, files=files, timeout=120)
            resp.raise_for_status()  # 若状态码非200 则抛出异常
            return resp.json()
        except requests.RequestException as e:
            print(f"❌ detect_language 出错: {e}")
            raise


def asr_transcribe(
        audio_file_path: str,
        api_url: str = "http://localhost:9000/asr",
        language: str = "zh",
        output_format: str = "json",
        task: str = "transcribe",
) -> dict:
    """
    调用 /asr 接口，进行语音识别（转写或翻译）

    :param audio_file_path: 音频文件的本地路径
    :param api_url: 识别接口地址，默认 http://localhost:9000/asr
    :param language: 语言标识，例如 "zh"（中文）或 "en"（英文）等等
    :param output_format: 返回格式，可选 "json", "text", "srt", "vtt", "tsv"
    :param task: 识别任务类型，可选 "transcribe"（转录原文） 或 "translate"（翻译为英文）
    :return: 返回接口响应的 JSON（如果 output_format=json，否则返回 {"text": "..."}）
    """
    if not os.path.isfile(audio_file_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")

    params = {
        "language": language,
        "output": output_format,
        "task": task
    }

    with open(audio_file_path, "rb") as f:
        files = {"audio_file": f}
        try:
            resp = requests.post(api_url, params=params, files=files, timeout=120)
            resp.raise_for_status()  # 若状态码非 200 则抛出异常

            # 如果 output_format 为 json，resp.json() 会是 { "text": "...", "segments": ... }
            if output_format == "json":
                return resp.json()
            else:
                # 非 json 时，返回一个 dict，text 字段装内容
                return {"text": resp.text}
        except requests.RequestException as e:
            print(f"❌ asr_transcribe 出错: {e}")
            raise


if __name__ == "__main__":
    test_audio = "test.wav"
    print("=== 测试：detect_language ===")
    try:
        lang_result = detect_language(test_audio)
        print("语言检测结果：", lang_result)
    except Exception as e:
        print("detect_language 调用失败:", e)

    print("\n=== 测试：asr_transcribe ===")
    try:
        asr_result = asr_transcribe(
            audio_file_path=test_audio,
            language="zh",
            output_format="json",
            task="transcribe"
        )
        print("ASR 识别结果：", asr_result)
    except Exception as e:
        print("asr_transcribe 调用失败:", e)
