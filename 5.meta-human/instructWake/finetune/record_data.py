import os
import time

from utils.record import RecordAudio

recorder = RecordAudio()

save_dir = 'dataset/audio/'
os.makedirs(save_dir, exist_ok=True)
save_list_train = 'dataset/train/'
os.makedirs(save_list_train, exist_ok=True)
save_list_validation = 'dataset/validation/'
os.makedirs(save_list_validation, exist_ok=True)
f_train_scp = open(f'{save_list_train}/wav.scp', 'a+', encoding='utf-8')
f_train_text = open(f'{save_list_train}/text', 'a+', encoding='utf-8')
f_validation_scp = open(f'{save_list_validation}/wav.scp', 'a+', encoding='utf-8')
f_validation_text = open(f'{save_list_validation}/text', 'a+', encoding='utf-8')

text = input("请输入指令内容：")
num = input("请输入录入次数：")
for i in range(int(num)):
    _ = input(f'第{i + 1}次录音，按回车开始说话：')
    name = int(time.time() * 1000)
    save_path = os.path.join(save_dir, f'{name}.wav')
    recorder.record(record_seconds=2, save_path=save_path)
    f_train_text.write(f'{name} {" ".join(text)}\n')
    f_train_scp.write(f'{name} {save_path}\n')
    f_validation_text.write(f'{name} {" ".join(text)}\n')
    f_validation_scp.write(f'{name} {save_path}\n')
f_train_scp.close()
f_train_text.close()
f_validation_scp.close()
f_validation_text.close()
