# 📝 Todo リスト Web アプリ

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-API-green?logo=googlesheets)
![Render](https://img.shields.io/badge/Deploy-Render-46e3b7?logo=render)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 概要

Python（Flask）と Google スプレッドシートを使ったシンプルな Todo 管理 Web アプリです。

タスクの「タイトル・内容・期日」を登録・編集でき、データは Google スプレッドシートにリアルタイムで保存されます。データベース不要で、スプレッドシートをそのままデータストアとして活用しています。

---

## デモ

**https://todo-app-1p8e.onrender.com**

<!-- ![スクリーンショット](docs/screenshot.png) -->

---

## 使用技術

| カテゴリ | 技術 |
|---|---|
| バックエンド | Python 3.11 / Flask 3.0 |
| データ保存 | Google Sheets API / gspread |
| フロントエンド | HTML5 / CSS3（バニラ） |
| デプロイ | Render |
| 認証 | Google サービスアカウント（OAuth2） |

---

## 機能

- **Todo 登録** — タイトル・内容・期日を入力して保存
- **Todo 一覧表示** — 登録したすべての Todo を一覧で確認
- **Todo 編集** — 既存 Todo の内容を更新
- **Todo 削除** — 不要な Todo を削除
- **Google スプレッドシート保存** — データベース不要でスプレッドシートに永続化
- **フラッシュメッセージ** — 操作後に成功・エラーをフィードバック表示

---

## システム構成

```
ブラウザ
   │
   │ HTTP リクエスト
   ▼
Flask アプリ（Render）
   │
   │ gspread / Google Sheets API
   ▼
Google スプレッドシート（データストア）
```

- ユーザーはブラウザから Flask アプリにアクセス
- Flask が Google Sheets API 経由でスプレッドシートを読み書き
- データはスプレッドシートの1行1Todoとして保存される

---

## ディレクトリ構成

```
todo-app/
├─ app.py                # Flask アプリ本体（ルーティング・API連携）
├─ requirements.txt      # 依存ライブラリ一覧
├─ .env.example          # 環境変数のテンプレート
├─ .gitignore
├─ templates/
│  ├─ index.html         # 一覧ページ・登録フォーム
│  └─ edit.html          # 編集ページ
└─ static/
   └─ style.css          # スタイルシート
```

---

## セットアップ方法

### 前提条件

- Python 3.10 以上
- Google アカウント

### 1. リポジトリをクローン

```bash
git clone https://github.com/moedaichi0629-ai/todo-app.git
cd todo-app
```

### 2. Google Cloud の設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. **Google Sheets API** と **Google Drive API** を有効化
3. サービスアカウントを作成し、JSONキー（`credentials.json`）をダウンロード
4. `credentials.json` をプロジェクトルートに配置

### 3. Google スプレッドシートの準備

1. スプレッドシートを新規作成
2. `credentials.json` 内の `client_email` をスプレッドシートに「編集者」として共有
3. URL から **スプレッドシートID** を取得  
   `https://docs.google.com/spreadsheets/d/`**`<ここがID>`**`/edit`

### 4. 環境変数を設定

```bash
cp .env.example .env
```

`.env` を編集：

```env
SPREADSHEET_ID=スプレッドシートIDを貼り付ける
SECRET_KEY=任意の文字列
```

### 5. ライブラリをインストール・起動

```bash
pip install -r requirements.txt
python app.py
```

ブラウザで `http://localhost:5000` を開いて確認してください。

---

## Render へのデプロイ

1. 本リポジトリを Fork または自分のリポジトリにプッシュ
2. [Render](https://render.com/) で「New Web Service」を作成
3. 以下を設定：

| 項目 | 値 |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |

4. Environment Variables に以下を追加：

| キー | 値 |
|---|---|
| `SPREADSHEET_ID` | スプレッドシートID |
| `SECRET_KEY` | 任意の文字列 |
| `GOOGLE_CREDENTIALS_JSON` | `credentials.json` の中身をそのまま貼り付け |

---

## 今後追加予定の機能

- [ ] 完了チェック機能（チェックボックスで完了/未完了を切り替え）
- [ ] 検索・フィルタ機能（キーワードや期日で絞り込み）
- [ ] 優先順位設定（高/中/低でタグ付け）
- [ ] 並び替え機能（期日順・登録日順）
- [ ] スマートフォン向けのさらなるレスポンシブ対応

---

## 工夫した点

**ローカルと本番環境の認証切り替え**  
ローカル開発では `credentials.json` ファイルを使い、Render 等の本番環境では `GOOGLE_CREDENTIALS_JSON` 環境変数（JSON文字列）を使う仕組みにしました。これにより `credentials.json` を Git に含めずセキュアに運用できます。

**データベース不要の設計**  
Google スプレッドシートをデータストアとして使うことで、SQLite/PostgreSQL などを別途用意せずにデプロイできます。非エンジニアでもスプレッドシートを直接確認・編集できる点も利点です。

**シート自動初期化**  
アプリ起動時にスプレッドシートのヘッダー行が存在するか確認し、なければ自動で作成するようにしました。手動でシートを設定しなくてもすぐ使える UX を意識しています。

---

## 学んだこと

- **Flask の基本的なルーティング**（GET/POST の使い分け、リダイレクト）
- **gspread を使った Google Sheets API の操作**（行の追加・更新・削除）
- **サービスアカウントによる OAuth2 認証**の仕組みと設定手順
- **環境変数による機密情報の管理**（`.env` / Render の環境変数）
- **gunicorn を使った本番環境向けの起動設定**

---

## ライセンス

MIT License
