import argparse
import functools
import os
import shutil

from utils.utils import add_arguments, print_arguments

parser = argparse.ArgumentParser(description=__doc__)
add_arg = functools.partial(add_arguments, argparser=parser)
add_arg("model_src",
        default="../models/paraformer-zh/",
        type=str, help="原始模型的路径")
add_arg("model_target",
        default="../models/paraformer-zh-finetune/",
        type=str, help="更新后模型的保存路径")
add_arg("output_dir",
        default="outputs/",
        type=str, help="微调模型保存路径")
args = parser.parse_args()
print_arguments(args)

# 删除旧模型
if os.path.exists(args.model_target):
    shutil.rmtree(args.model_target)
checkpoint_name = "model.pt"
shutil.copytree(args.model_src, args.model_target)
shutil.copy(os.path.join(args.output_dir, checkpoint_name), os.path.join(args.model_target, "model.pt"))
