# 安装项目环境

本项目开发换为：
 - Anaconda 3
 - Windows 11
 - Python 3.11
 - Pytorch 2.1.0
 - CUDA 12.1

1. 安装Pytorch，执行下面命令，如果已经安装了其他版本，若能正常运行，请跳过。
```shell
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

2. 安装其他依赖包，执行下面命令，安装完成之后，如果还缺失其他库，请对应安装。
```shell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

# 指令唤醒

`infer_pytorch.py`可以使用GPU进行推理，如果要使用CPU推理，可以`infer_onnx.py`，这个使用的是ONNX，在CPU可以有加速。

1. 可以调整的参数有：`sec_time`为录制时间，单位秒；`last_len`为上一部分的数据长度，单位秒；。
2. 增加指令，需要在`instruct.txt`添加指令。

# 微调指令模型

微调指令模型的代码在`finetune`目录下，具体的训练过程可以参考[这里](finetune/README.md)。
