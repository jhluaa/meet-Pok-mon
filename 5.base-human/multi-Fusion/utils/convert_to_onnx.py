# import tensorflow as tf
# import tf2onnx
#
# # 加载模型
# model = tf.keras.models.load_model("1_32_False_True_0.25_lip_motion_net_model.h5")
#
# # 定义输入形状 (batch_size, seq_length, feature_dim)
# input_signature = (tf.TensorSpec((1, 25, 1), tf.float32, name="input"),)
#
# # 导出为 ONNX
# onnx_model, _ = tf2onnx.convert.from_keras(
#     model, input_signature=input_signature, opset=13
# )
#
# # 保存 ONNX 模型
# onnx_model_path = "model.onnx"
# with open(onnx_model_path, "wb") as f:
#     f.write(onnx_model.SerializeToString())
#
# print(f"Model successfully exported to {onnx_model_path}")

if __name__ == "__main__":
    import onnxruntime as ort
    import numpy as np

    # 加载 ONNX 模型
    session = ort.InferenceSession("model.onnx")

    # 获取输入输出名称
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    # 准备测试数据
    X_data = np.random.rand(1, 25, 1).astype(np.float32)
    print("X_data", X_data)
    # 推理
    y_pred = session.run([output_name], {input_name: X_data})
    print("Model output:", y_pred)
    predicted_class = np.argmax(y_pred[0], axis=-1)
    print("Predicted class:", predicted_class)
