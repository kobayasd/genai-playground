class Config:
    # スタック名
    # この値を変更すると、スタックの新しいインスタンスを作成できます
    STACK_NAME = "TitanInpainter"
    
    # ALBがCloudFront以外のクライアントからのリクエストを受け付けないように、
    # ここに独自のカスタム値を設定してください。任意のランダムな文字列を選択できます。
    CUSTOM_HEADER_VALUE = "My_random_value_58dsv15e4s31"    