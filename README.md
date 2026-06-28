# 📝 Todo リスト Web アプリ

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-API-34A853?logo=googlesheets&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46e3b7?logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

<br>

## 概要

**Python（Flask）と Google スプレッドシートを組み合わせたTodo管理Webアプリです。**

タスクの「タイトル・内容・期日」を登録・編集・削除でき、入力したデータはリアルタイムで Google スプレッドシートに保存されます。

一般的なTodoアプリとの違いは **「データベースを使わない」** 点です。Google スプレッドシートをデータストアとして活用することで、サーバー側のDB設定なしにデプロイでき、スプレッドシートを開けばデータをそのまま確認・編集することもできます。

**公開URL（Render）:** https://todo-app-1p8e.onrender.com

<br>

---

## 何ができるか

| 機能 | 説明 |
|---|---|
| ✅ **Todo登録** | タイトル・内容・期日を入力して新しいタスクを追加できる |
| 📋 **Todo一覧表示** | 登録したすべてのTodoをカード形式で一覧表示できる |
| ✏️ **Todo編集** | 登録済みのTodoのタイトル・内容・期日をあとから変更できる |
| 🗑️ **Todo削除** | 不要になったTodoを削除できる（確認ダイアログ付き） |
| 💾 **スプレッドシート保存** | 操作のたびにGoogleスプレッドシートへ自動で読み書きされる |
| 💬 **フラッシュメッセージ** | 「登録しました」「更新しました」などの操作結果を画面上に表示する |

<br>

**スプレッドシート側では、このようにデータが保存されます：**

| id | title | content | due_date | created_at |
|---|---|---|---|---|
| a1b2c3d4 | レポートを提出する | 3章まで書く | 2026-07-01 | 2026-06-28 21:00:00 |
| e5f6g7h8 | 買い物をする | 牛乳・卵・パン | 2026-06-30 | 2026-06-28 21:05:00 |

<br>

---

## 使用技術

| カテゴリ | 技術・ツール | 用途 |
|---|---|---|
| 言語 | Python 3.12 | バックエンド全般 |
| フレームワーク | Flask 3.0 | Webアプリの構築・ルーティング |
| データ保存 | Google Sheets API / gspread | スプレッドシートの読み書き |
| 認証 | google-auth（サービスアカウント） | Google APIへの安全な接続 |
| 環境変数管理 | python-dotenv | APIキー等の秘密情報を管理 |
| 本番サーバー | gunicorn | Render上でのアプリ起動 |
| デプロイ | Render | 無料でWebアプリを公開 |
| フロントエンド | HTML5 / CSS3 | 画面の構築とデザイン |

<br>

---

## システム構成

```
ブラウザ（ユーザー）
      │
      │  HTTP リクエスト（GET / POST）
      ▼
Flask アプリ（Render 上で稼働）
      │
      │  gspread ライブラリ経由
      ▼
Google Sheets API
      │
      ▼
Google スプレッドシート（データ保存先）
```

- ユーザーがフォームを送信 → FlaskがリクエストをPOSTで受け取る
- Flaskが `gspread` を通じてスプレッドシートを操作（追加・更新・削除）
- 一覧表示時はスプレッドシートから全データを読み込んでHTMLに渡す

<br>

---

## ディレクトリ構成

```
todo-app/
├─ app.py                # Flaskアプリ本体（ルーティング・スプレッドシート操作）
├─ requirements.txt      # 依存ライブラリ一覧
├─ .env.example          # 環境変数のテンプレート（.envにコピーして使う）
├─ .gitignore            # Git管理から除外するファイルを指定
├─ templates/
│  ├─ index.html         # 一覧ページ＋登録フォーム
│  └─ edit.html          # 編集ページ
└─ static/
   └─ style.css          # スタイルシート（レスポンシブ対応）
```

<br>

---

## セットアップ方法

### 前提条件

- Python 3.10 以上がインストールされていること
- Google アカウントを持っていること

<br>

### Step 1: リポジトリをクローン

```bash
git clone https://github.com/moedaichi0629-ai/todo-app.git
cd todo-app
```

<br>

### Step 2: Google Cloud でサービスアカウントを作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスしてプロジェクトを作成
2. 「APIとサービス」→「ライブラリ」から **Google Sheets API** と **Google Drive API** を有効化
3. 「APIとサービス」→「認証情報」→「サービスアカウント」を作成
4. 作成したサービスアカウントの「キー」タブから JSON キーをダウンロード
5. ダウンロードしたファイルを **`credentials.json`** にリネームし、プロジェクトルートに配置

<br>

### Step 3: Google スプレッドシートを準備

1. [Google スプレッドシート](https://sheets.google.com) で新しいシートを作成
2. `credentials.json` 内の `client_email` の値をコピー
3. スプレッドシートの「共有」から、そのメールアドレスを **編集者** として追加
4. URLからスプレッドシートIDを取得  
   `https://docs.google.com/spreadsheets/d/`**`【この部分がID】`**`/edit`

<br>

### Step 4: 環境変数を設定

```bash
cp .env.example .env
```

`.env` を開いて以下を入力：

```env
SPREADSHEET_ID=取得したスプレッドシートIDを貼り付ける
SECRET_KEY=任意の文字列（例：mysecretkey123）
```

<br>

### Step 5: ライブラリをインストールして起動

```bash
pip install -r requirements.txt
python app.py
```

ブラウザで **http://localhost:5000** を開いて動作確認してください。

<br>

---

## Render へのデプロイ手順

1. このリポジトリをGitHubにプッシュ
2. [Render](https://render.com/) にGitHubアカウントでサインアップ
3. 「New +」→「Web Service」→ リポジトリを選択

以下の設定を入力：

| 項目 | 設定値 |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |

「Advanced」→「Add Environment Variable」で以下の3つを追加：

| キー | 値 |
|---|---|
| `SPREADSHEET_ID` | スプレッドシートID |
| `SECRET_KEY` | 任意の文字列 |
| `GOOGLE_CREDENTIALS_JSON` | `credentials.json` の中身をすべてコピーして貼り付け |

「Create Web Service」をクリックしてデプロイ開始。  
`==> Your service is live 🎉` が表示されたら公開完了です。

<br>

---

## 今後追加予定の機能

- [ ] **完了チェック機能** — チェックボックスでTodoを「完了 / 未完了」に切り替える
- [ ] **ステータス管理** — 「未着手 / 進行中 / 完了」の3段階で管理する
- [ ] **検索・フィルタ機能** — キーワードや期日でTodoを絞り込む
- [ ] **優先順位設定** — 高・中・低の3段階でタグ付けして並び替え
- [ ] **期日ソート** — 期日が近い順・登録が新しい順に並べ替える
- [ ] **ログイン機能** — ユーザーごとにTodoを管理できるようにする
- [ ] **モバイル対応強化** — スマートフォンでさらに使いやすいUIに改善

<br>

---

## 工夫した点

**ローカルと本番環境で認証方法を自動切り替え**  
ローカル開発では `credentials.json` ファイルを使い、Render 等の本番環境では `GOOGLE_CREDENTIALS_JSON` 環境変数（JSON文字列）を使う仕組みにしました。これにより秘密鍵を含む `credentials.json` を Git に含めずにデプロイできます。

**データベース不要の設計**  
Google スプレッドシートをデータストアとして活用することで、SQLite や PostgreSQL などを別途セットアップせずにデプロイできます。スプレッドシートを直接開いてデータを確認・修正できる点も利点です。

**シートのヘッダーを自動初期化**  
アプリ起動時にスプレッドシートの1行目にヘッダー（`id / title / content / due_date / created_at`）がなければ自動で追加する処理を実装しました。手動でシートを事前設定しなくてもそのまま使い始められます。

<br>

---

## ライセンス

MIT License
