# 制作数据

运行`record_data.py`代码，启动录音程序，默认录制2秒钟，建议录制完成之后，再录制1秒钟的音频，注意录制1秒钟时间非常短，按下回车之后要立马开始说话。其实自定义数据可以参考生成的`dataset`目录。

# 生成训练数据列表

运行`generate_data_list.py`代码，生成训练数据列表。

# 训练模型

执行下面命令训练模型，如果是Windows，需要把参数并接为一行，并删除`\`。
```shell
funasr-train \
++model=../models/paraformer-zh \
++train_data_set_list=dataset/train.jsonl \
++valid_data_set_list=dataset/validation.jsonl \
++dataset_conf.batch_type="token" \
++dataset_conf.batch_size=10000 \
++train_conf.max_epoch=5 \
++train_conf.log_interval=1 
++train_conf.keep_nbest_models=5 \
++train_conf.avg_nbest_model=3 \
++output_dir="./outputs"
```

# 合并模型

运行`merge_model.py`代码，将训练好的模型合并成一个模型`../models/paraformer-zh-finetune`。