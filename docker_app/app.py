import base64
import boto3
import cv2
import io
import json
import numpy as np
import os
from PIL import Image
import logging
from rembg import remove
from dotenv import load_dotenv
import streamlit as st

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# dotenv で環境変数を読み込む
def load_env_if_exists():
    """カレントディレクトリに .env ファイルが存在する場合に限り、環境変数を読み込む。"""
    env_path = '.env'
    if os.path.isfile(env_path):
        load_dotenv(env_path)
        print(".env から環境変数を読み込みました。")
    else:
        print(".env ファイルが見つかりません。IAMロールまたは他の認証方法を使用します。")

load_env_if_exists()

class ImageProcessor:
    THRESHOLD = 128 # 2 値化の閾値

    @staticmethod
    def create_binary_mask(masked_image):
        """マスク画像を2値化する"""
        mask = masked_image.point(lambda x: 0 if x < ImageProcessor.THRESHOLD else 255)
        return mask
    
    @staticmethod
    def remove_background(input_image):
        """背景を削除する"""
        # rembgを使用して背景を削除
        # only_mask=True でマスク画像のみを出力
        output_image = remove(input_image,only_mask=True, alpha_matting=True)

        return output_image

    @staticmethod
    def convert_image_to_base64(image_input):
        """画像をBase64エンコードされた文字列に変換"""
        if isinstance(image_input, str):
            if not os.path.isfile(image_input):
                raise FileNotFoundError(f"指定されたファイルが見つかりません: {image_input}")
            with open(image_input, "rb") as file:
                return base64.b64encode(file.read()).decode("utf-8")
        elif isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        else:
            raise ValueError("サポートされていない型です。str (ファイルパス) または PIL.Image.Image が必要です。")

class Translator:
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client(service_name="translate", region_name=region_name)

    def translate_text(self, text, source_language_code='ja', target_language_code='en'):
        """テキストを翻訳する"""
        try:
            result = self.client.translate_text(Text=text, SourceLanguageCode=source_language_code, TargetLanguageCode=target_language_code)
            return result.get('TranslatedText')
        except Exception as e:
            logging.error(f"翻訳中にエラーが発生しました: {e}")
            return None

class BedrockAPI:
    def __init__(self):
        self.client = boto3.client(service_name="bedrock-runtime", region_name='us-east-1')

    def invoke_model(self, body, modelId):
        """Bedrockのモデルを呼び出す"""
        response = self.client.invoke_model(body=json.dumps(body), modelId=modelId, accept="application/json", contentType="application/json")
        response_body = json.loads(response.get("body").read())
        images = [Image.open(io.BytesIO(base64.b64decode(base64_image))) for base64_image in response_body.get("images")]
        return images[0]

    def edit_image(self, task_type, prompt, negative_prompt, image, maskImage=None, seed=0):
        """画像編集タスクを実行する"""
        translator = Translator()
        translated_prompt = translator.translate_text(prompt)
        logging.info("Amazon Bedrock で画像生成を実行します。")
        logging.info(f"プロンプト（英訳前）: {prompt}")
        logging.info(f"プロンプト（英訳後）: {translated_prompt}")
        logging.info(f"ネガティブプロンプト: {negative_prompt}")
        logging.info(f"シード値: {seed}")

        body = {
            "taskType": task_type.upper(),
            "inPaintingParams": {
                "text": translated_prompt,
                "negativeText": negative_prompt,
                "image": ImageProcessor.convert_image_to_base64(image),
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "standard",
                "cfgScale": 8.0,
                "seed": seed,
            }
        }
        if maskImage:
            body["inPaintingParams"]["maskImage"] = ImageProcessor.convert_image_to_base64(maskImage)
        return self.invoke_model(body, modelId="amazon.titan-image-generator-v1")

import random  # ランダムモジュールをインポート

def main():
    st.title("Titan Image Inpainter")

    # セッションステートでシード値を管理
    if 'seed_value' not in st.session_state:
        st.session_state.seed_value = 0  # 初期値を設定

    # ユーザーに画像のアップロードを促す
    uploaded_file = st.file_uploader("画像をアップロードしてください", type=["png", "jpg", "jpeg"])

    # プロンプトとネガティブプロンプトの入力
    prompt = st.text_input("生成したい画像のイメージが伝わるよう、プロンプトを入力してください", "プロのカメラマンが撮影した商品画像、大理石のテーブルの上に、たくさんの果物が置かれている、背景は少しボケている")
    negative_prompt = st.text_input("ネガティブプロンプトを入力してください", "lowres, error, cropped, worst quality, low quality, jpeg artifacts, ugly, out of frame")


    # ランダムにシード値を生成する場合
    if st.button("ランダムにシード値を生成する"):
        seed_value = random.randint(0, 2147483646)
        st.session_state.seed_value = seed_value

    # シード値の入力
    seed_value = st.number_input("シード値を入力してください (0 から 2147483646)", min_value=0, max_value=4294967295, value=st.session_state.seed_value, step=1)

    # アップロードされた画像と修正後の画像を横に並べて表示するためのカラムを作成
    col1, col2 = st.columns(2)

    # アップロードされた画像を表示
    if uploaded_file is not None:
        # アップロードされた画像を読み込む
        bytes_data = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(bytes_data))

        # アップロードされた画像を 1024x1024 以下にする
        if image.width > 1024 or image.height > 1024:
            # 画像の縦横比を維持したまま、長辺を 1024 にする
            if image.width > image.height:
                image = image.resize((1024, int(image.height * 1024 / image.width)))
            else:
                image = image.resize((int(image.width * 1024 / image.height), 1024))

        with col1:
            st.image(image, caption="アップロードされた画像")

    # 処理を開始するボタン
    if st.button("画像を生成する"):
        
        if uploaded_file is None:
            st.error("画像がアップロードされていません。")
            return
        
        # 画像処理中はローディング状態を表示
        with col2:
            with st.spinner('画像を生成中です...'):
                # 背景除去
                bg_removed_image = ImageProcessor.remove_background(image)
                if bg_removed_image:
                    # マスク画像を2値化する
                    mask = ImageProcessor.create_binary_mask(bg_removed_image)

                    # Amazon Bedrock で画像生成を実行する
                    bedrock_api = BedrockAPI()
                    imageOutpaint = bedrock_api.edit_image("INPAINTING", prompt, negative_prompt, image, maskImage=mask, seed=st.session_state.seed_value)

                    # 処理が完了したら、修正後の画像を表示
                    st.image(imageOutpaint, caption="生成した画像")

                    logging.info("画像の処理が完了しました。")
                else:
                    st.error("画像の処理に失敗しました。")

if __name__ == "__main__":
    main()

