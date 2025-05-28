# Web App Template

このプロジェクトは、Python 3.11を使用したWebアプリケーションのテンプレートです。FastAPIを使用したバックエンドと、モダンなフロントエンドの構成を提供します。

## 開発環境のセットアップ

### 必要条件
- Docker
- Visual Studio Code
- VS Code Remote - Containers 拡張機能

### 環境変数の設定

デプロイメントに必要な環境変数は、GitHubリポジトリのSecretsに事前に設定する必要があります。
詳細な設定方法については、[GitHub Actionsの設定](./docs/github-actions.md)を参照してください。

### 開発環境の起動方法

1. このリポジトリをクローンします：
```bash
git clone [リポジトリのURL]
cd web-app-template
```

2. VS Codeでプロジェクトを開きます：
```bash
code .
```

3. VS Codeがコンテナのビルドを提案したら、「Reopen in Container」をクリックします。

## プロジェクト構造

```
.
├── .devcontainer/     # 開発コンテナの設定
├── models/           # データモデル
├── routers/          # APIルーター
├── static/           # 静的ファイル
├── templates/        # テンプレート
├── utils/            # ユーティリティ関数
├── app.py           # メインアプリケーション
└── database.py      # データベース設定
```

## 主な機能

- FastAPIを使用したRESTful API
- SQLiteデータベース
- モダンなUI/UX
- 開発環境のコンテナ化

## 開発環境の特徴

- Python 3.11
- 自動フォーマッティング（Black）
- インポートの自動整理（isort）
- コード品質チェック（Flake8）
- GitHub Copilot統合
- Jupyter Notebookサポート

## ポート設定

- 5678: デバッグ用ポート
- 8000: アプリケーション用ポート

## ライセンス

[ライセンス情報を追加]

## 貢献

[貢献方法のガイドラインを追加] 