# 使用官方Python镜像作为基础镜像
FROM python:3.8

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的/app内
COPY . /app

# 设置时区
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Asia/Shanghai
# 安装 OpenCV 依赖项
RUN apt-get install -y libgl1-mesa-glx
# 使用清华镜像源加速pip安装
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口，例如60006
EXPOSE 60006

# 设置环境变量
ENV FLASK_APP=face_api.py

# 运行flask服务
CMD ["flask", "run","--host=0.0.0.0","--port=60006"]


