import os

from dotenv import load_dotenv
from openai import OpenAI

# ------------------------------------------------------------------
# GPT 生成ヘルパ

SYSTEM_PROMPT = """あなたはWEB APP TEMLATEのシステムとユーザーをつなぐアシスタントです。
"""


# ------------------------------------------------------------------
# 初期化関数
def initialize_clients():
    """
    初期化関数: initialize_clients

    この関数は、.env ファイルから OpenAI API の認証情報を読み込み、
    OpenAI API クライアントを初期化します。

    使い方:
        1. .env ファイルに以下の環境変数を設定してください:
            - OPENAI_API_KEY
            - (任意) OPENAI_MODEL

        2. 関数を呼び出すと、API キーとクライアントインスタンスがタプルで返されます。

    戻り値:
        (
            OPENAI_API_KEY,      # 0: OpenAI APIキー
            OPENAI_MODEL,        # 1: OpenAI モデル名
            openai_client,       # 2: OpenAI インスタンス
            SYSTEM_PROMPT        # 3: システムプロンプト
        )

    例外:
        - 必要な環境変数が未設定の場合は RuntimeError を送出します。

    例:
        api_keys_and_clients = initialize_clients()
        OPENAI_API_KEY = api_keys_and_clients[0]
        OPENAI_MODEL = api_keys_and_clients[1]
        openai_client = api_keys_and_clients[2]
        SYSTEM_PROMPT = api_keys_and_clients[3]
    """
    global OPENAI_API_KEY, OPENAI_MODEL
    global openai_client

    # .env からキー類を読み込む
    load_dotenv()

    # OpenAI API キー
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    # モデル名（未設定なら gpt-4.1）
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")

    # ------------------------------------------------------------------
    # API クライアント
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    return (
        OPENAI_API_KEY,
        OPENAI_MODEL,
        openai_client,
        SYSTEM_PROMPT,
    )


def generate_ai_reply(user_prompt: str, temperature: float) -> str:
    """
    OpenAI APIを使用してメッセージを生成します。

    Args:
        user_prompt (str): ユーザーからのプロンプト
        temperature (float): 生成のランダム性を制御するパラメータ（0.0-1.0）

    Returns:
        str: 生成されたメッセージ
    """
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=120 * 10,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


# if __name__ == "__main__":
#     # クライアント初期化
#     initialize_clients()
#     # 例: ツイートIDを指定して本文取得
#     tweet_id = input("ツイートIDを入力してください: ")
#     try:
#         reply_to_tweet(tweet_id, "system::test_reply")

#     except Exception as e:
#         print("エラー:", e)
