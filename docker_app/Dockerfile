FROM python:3.11
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*
RUN  pip3 install --upgrade pip && pip3 install -r requirements.txt

# GitHub からu2netをダウンロード
RUN mkdir -p /root/.u2net && \
    wget -O /root/.u2net/u2net.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

COPY . .

# Command overriden by docker-compose
CMD streamlit run app.py
