import numpy as np
import soundcard
from funasr import AutoModel

# 加载指令
with open('instruct.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    instructs = [line.replace('\n', '') for line in lines]
    hotwords = ' '.join(instructs)
    print(f"支持指令：{instructs}")

# 加载模型
model_dir = "models/paraformer-zh"
model = AutoModel(model=model_dir)

# 录制时间，单位秒
sec_time = 1
# 上一部分的数据
last_data = None
# 上一部分的数据长度
last_len = 0.5


def real_time_predict():
    global last_data
    block_size = 16000 * sec_time
    input_device = soundcard.default_microphone()
    recorder = input_device.recorder(samplerate=16000, channels=1, blocksize=block_size)
    with recorder:
        print("请发出指令...")
        while True:
            # 开始录制并获取数据
            data = recorder.record(numframes=block_size)
            data = data.squeeze()
            if last_data is not None:
                input_data = np.concatenate((last_data, data))
            else:
                input_data = data
            last_data = data[-int(16000 * last_len):]
            result = model.generate(input=input_data, batch_size_s=300, hotword=hotwords, disable_pbar=True)[0]
            if len(result) > 0:
                result = result['text'].replace(' ', '')
                if result in instructs:
                    print(f"触发指令：【{result}】")


if __name__ == '__main__':
    real_time_predict()
