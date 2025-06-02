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
- メモ機能
  - メモの作成、表示、削除
  - クリップボードからのテキスト貼り付け
  - メモ内のURLをワンクリックでコピー
  - メモの検索機能
  - 並び順の変更（新しい順/古い順）
  - 表示件数の調整（10件/50件）
  - ページネーション機能
  - GitHubリポジトリへの保存機能
    - メモをGitHubリポジトリに自動保存
    - 保存されたメモはGitHubで直接閲覧可能
    - メモのタイムスタンプ付きファイル名で管理
  - 管理機能（管理者ユーザーのみ）
    - GitHubリポジトリのメモファイル一括削除
    - 削除前の確認ダイアログ
    - 操作ログの表示
- チャット機能
  - AIとの対話型チャット
  - チャット内容をそのままGitHubリポジトリにMarkdown形式でプッシュ可能
    - プッシュ後はGitHub上で内容を直接閲覧可能

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