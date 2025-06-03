import base64
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------------------------------------------------
# GPT 生成ヘルパ

SYSTEM_PROMPT = """あなたはシステムとユーザーをつなぐアシスタントです。
"""

# ------------------------------------------------------------------
# GitHub API ヘルパ


def get_github_repo_contents(owner: str, repo: str, path: str = "") -> Dict[str, Any]:
    """
    GitHubのリポジトリコンテンツを取得する関数

    Args:
        owner (str): リポジトリのオーナー名
        repo (str): リポジトリ名
        path (str, optional): 取得するパス。デフォルトは空文字（ルート）

    Returns:
        Dict[str, Any]: リポジトリのコンテンツ情報

    Raises:
        RuntimeError: 必要な環境変数が設定されていない場合
        requests.exceptions.RequestException: APIリクエストが失敗した場合
    """
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        raise RuntimeError("GITHUB_TOKEN is not set in .env")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def create_github_file(
    owner: str, repo: str, content: str, branch: str = "main"
) -> Dict[str, Any]:
    """
    GitHubのリポジトリにファイルを作成する関数

    Args:
        owner (str): リポジトリのオーナー名
        repo (str): リポジトリ名
        content (str): 作成するファイルの内容
        branch (str, optional): 対象のブランチ。デフォルトは"main"

    Returns:
        Dict[str, Any]: 作成されたファイルの情報

    Raises:
        RuntimeError: 必要な環境変数が設定されていない場合
        requests.exceptions.RequestException: APIリクエストが失敗した場合
    """
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        raise RuntimeError("GITHUB_TOKEN is not set in .env")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # 現在のタイムスタンプをファイル名として使用（YYYY_MM_DD_HH_MM_SS形式）
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = f"memo_{timestamp}.md"

    # コンテンツをBase64エンコード
    content_bytes = content.encode("utf-8")
    content_base64 = base64.b64encode(content_bytes).decode("utf-8")

    data = {
        "message": f"Add memo file: {path}",
        "content": content_base64,
        "branch": branch,
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()


def delete_github_file(
    owner: str, repo: str, path: str, sha: str, branch: str = "main"
) -> Dict[str, Any]:
    """
    GitHubのリポジトリからファイルを削除する関数

    Args:
        owner (str): リポジトリのオーナー名
        repo (str): リポジトリ名
        path (str): 削除するファイルのパス
        sha (str): ファイルのSHAハッシュ
        branch (str, optional): 対象のブランチ。デフォルトは"main"

    Returns:
        Dict[str, Any]: 削除結果の情報

    Raises:
        RuntimeError: 必要な環境変数が設定されていない場合
        requests.exceptions.RequestException: APIリクエストが失敗した場合
    """
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        raise RuntimeError("GITHUB_TOKEN is not set in .env")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    data = {
        "message": f"Delete file: {path}",
        "sha": sha,
        "branch": branch,
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.delete(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()


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
            - (任意) OPEN_AI_CHAT_MODEL

        2. 関数を呼び出すと、API キーとクライアントインスタンスがタプルで返されます。

    戻り値:
        (
            OPENAI_API_KEY,      # 0: OpenAI APIキー
            OPEN_AI_CHAT_MODEL,  # 1: OpenAI モデル名
            openai_client,       # 2: OpenAI インスタンス
            SYSTEM_PROMPT        # 3: システムプロンプト
        )

    例外:
        - 必要な環境変数が未設定の場合は RuntimeError を送出します。

    例:
        api_keys_and_clients = initialize_clients()
        OPENAI_API_KEY = api_keys_and_clients[0]
        OPEN_AI_CHAT_MODEL = api_keys_and_clients[1]
        openai_client = api_keys_and_clients[2]
        SYSTEM_PROMPT = api_keys_and_clients[3]
    """
    global OPENAI_API_KEY, OPEN_AI_CHAT_MODEL
    global openai_client

    # .env からキー類を読み込む
    load_dotenv()

    # OpenAI API キー
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    # config.json からモデル名を取得
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            OPEN_AI_CHAT_MODEL = config.get("OPEN_AI_CHAT_MODEL", "gpt-4.1")
    except Exception:
        OPEN_AI_CHAT_MODEL = "gpt-4.1"

    # ------------------------------------------------------------------
    # API クライアント
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    return (
        OPENAI_API_KEY,
        OPEN_AI_CHAT_MODEL,
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
        model=OPEN_AI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=32000,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def get_url_title(url: str) -> Optional[str]:
    """URLからタイトルを取得する"""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else None
        return title.strip() if title else None
    except Exception:
        return None


class ChatBot:
    """チャットボットクラス"""

    def __init__(self, temperature: float = 0.1):
        """メッセージ履歴を保持するリストを初期化"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.temperature = temperature

        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_CHAT_MODEL = os.getenv("OPEN_AI_CHAT_MODEL", "gpt-4.1")
        self.openai_client = OpenAI(api_key=self.OPENAI_API_KEY)

    def get_ai_messages(self, user_message):
        self.messages.append({"role": "user", "content": user_message})
        response = self.openai_client.chat.completions.create(
            model=self.OPENAI_CHAT_MODEL,
            messages=self.messages,
            max_tokens=32000,
            temperature=self.temperature,
        )
        ai_response = response.choices[0].message.content.strip()
        self.messages.append(
            {
                "role": "assistant",
                "content": ai_response,
            }
        )
        return ai_response

    async def get_ai_messages_stream(self, user_message):
        """ストリーミング形式でAIの応答を取得（非同期版）"""
        self.messages.append({"role": "user", "content": user_message})
        stream = self.openai_client.chat.completions.create(
            model=self.OPENAI_CHAT_MODEL,
            messages=self.messages,
            max_tokens=32000,
            temperature=self.temperature,
            stream=True,
        )

        collected_messages = []
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                collected_messages.append(content)
                yield content

        # 完全な応答をメッセージ履歴に追加
        full_response = "".join(collected_messages)

        print(full_response)
        self.messages.append(
            {
                "role": "assistant",
                "content": full_response,
            }
        )

    def clear_messages(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# ChatBotのテスト
if __name__ == "__main__":
    try:
        # テスト用のリポジトリ情報
        test_owner = "yxfhy"
        test_repo = "memo"

        # リポジトリのルートコンテンツを取得
        contents = get_github_repo_contents(test_owner, test_repo)
        print("リポジトリのルートコンテンツ:")
        for item in contents:
            print(f"- {item['name']} ({item['type']})")

        # READMEファイルの内容を取得
        readme = get_github_repo_contents(test_owner, test_repo, "README.md")
        print("\nREADMEの内容:")
        print(readme.get("content", "コンテンツが見つかりません"))

        # 新しいメモファイルを作成
        test_content = """# テストメモ

これはテスト用のメモファイルです。
- 項目1
- 項目2
- 項目3

作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        new_file = create_github_file(test_owner, test_repo, test_content)
        print("\n新しいファイルを作成しました:")
        print(f"ファイル名: {new_file['content']['name']}")
        print(f"パス: {new_file['content']['path']}")
        print(f"SHA: {new_file['content']['sha']}")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
