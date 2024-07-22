# Titan Image Inpainter on ECS

このソリューションは、Amazon Bedrock の Titan Image Generator を利用して、元画像の背景のみ画像生成を行うことを可能にします。元画像の被写体にはプロンプトの影響が及ばないように、自動的にマスク生成を行っており、Titan Image Generator の Inpaint 機能で、マスク部分以外の生成を行っています。

## Architecture Overview
![Architecture Overview](./img/architecture.png)

## 機能

### マスク画像の自動生成
被写体がプロンプトの影響を受けないよう、Inpaint の際に利用するマスク画像を自動的に生成します。
Titan Image Generator の maskPrompt で指定することも可能ですが、輪郭を正確にマスクすることは難しいため、 [rembg](https://github.com/danielgatis/rembg)ライブラリを使用して画像から背景を削除し、マスク画像を生成します。

### 日本語プロンプトに対応
プロンプトを Amazon Bedrock に渡す際に Amazon Translate を利用して英訳しています。そのため、日本語プロンプトを入力しても問題なく動作します。

### 画像生成
Amazon Bedrock の Titan Image Generator モデルを使用して、ユーザーが入力したプロンプトに基づいて画像を編集します。Inpaint を利用することで、マスク部分以外の画像生成を行います。

## サンプル1

Titan Image Generator で生成したワインボトルの背景を変換

```
プロのカメラマンが撮影した商品画像、大理石のテーブルの上に、たくさんの果物が乗っている、背景は少しボケている
```

![Sample wine](./img/sample_wine.jpg)

## サンプル2

Yotsuba で撮影したコーヒーの背景を変換

```text
プロのカメラマンが撮影した商品画像、大自然、背景は少しボケている
```

![Sample Coffee](./img/sample_coffee.jpg)


## Usage / 使い方

### 前提条件

- Amazon Bedrock の Titan Image Generator G1 モデルの有効化

### 開発環境の作成

[Cloud9 Setup for Prototyping](https://github.com/aws-samples/cloud9-setup-for-prototyping) を利用して、開発環境用の Cloud9 を作成します。

1. CloudShell ターミナルを開く
 
2. 以下のコマンドを実行して、Cloud9 を立ち上げる
 
```
git clone https://github.com/aws-samples/cloud9-setup-for-prototyping
cd cloud9-setup-for-prototyping
./bin/bootstrap
```

2~3分待ち、`Done!` と表示されたら作成は完了です。

3. cloud9 リソースの作成が完了したら[Cloud9](https://console.aws.amazon.com/cloud9/home)のコンソールにアクセスし、`cloud9-for-prototyping` を開く

4. Cloud9 のターミナル上で以下のコマンドを実行し、本リポジトリを clone する

```
git clone https://github.com/kobayasd/titan-image-inpaint
```

5. クローンしたリポジトリを開く

```
cd titan-image-inpaint
```

以上で環境の準備は完了です。


### デプロイ

アプリケーションは AWS Cloud Development Kit（以降 CDK）を利用してデプロイします。

1. `docker_app/config_file.py`を開き、`STACK_NAME`と`CUSTOM_HEADER_VALUE`を任意の値に修正しましょう

2. 依存関係のインストール

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. CDK のデプロイ

CDK を利用したことがない場合、初回のみ Bootstrap 作業が必要です。すでに Bootstrap された環境では以下のコマンドは不要です。
※ 実行には 1~2 分ほどかかります

```
cdk bootstrap
```

続いて、以下のコマンドで AWS リソースをデプロイします。デプロイには 5 ~ 10 分程度かかります。

```
cdk deploy
```

デプロイ完了時に、アプリケーションの URL が出力されます。

```
Outputs:
TitanInpainter.CloudFrontDistributionURL = ddh1msm2zhwg3.cloudfront.net
```

4. リソースの削除
作成したリソースは以下のコマンドで削除が可能です。

```
cdk destroy
```