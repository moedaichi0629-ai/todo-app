import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# .envファイルの読み込み
load_dotenv()

app = Flask(__name__)
# フラッシュメッセージに必要なシークレットキー
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Google Sheets API に必要な権限（スコープ）
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 環境変数からスプレッドシートIDを取得
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# スプレッドシートの列見出し（ヘッダー）
HEADERS = ['id', 'title', 'content', 'due_date', 'created_at']


def get_sheet():
    """Google Sheets に接続してシートオブジェクトを返す関数"""

    # Renderなど本番環境では GOOGLE_CREDENTIALS_JSON に JSON文字列を設定する
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        # 環境変数のJSON文字列からCredentialsを生成
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # ローカル開発時は credentials.json ファイルを使用
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    # 1枚目のシートを使用
    sheet = spreadsheet.sheet1
    return sheet


def init_sheet(sheet):
    """シートにヘッダー行がなければ追加する関数"""
    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        # ヘッダーが違う場合はシートをクリアしてヘッダーを挿入
        sheet.clear()
        sheet.insert_row(HEADERS, 1)


def get_all_todos():
    """スプレッドシートから全Todoを辞書のリストとして取得する関数"""
    sheet = get_sheet()
    init_sheet(sheet)
    # get_all_records() は1行目をキーとして辞書のリストを返す
    records = sheet.get_all_records()
    return records, sheet


# ========== ルーティング ==========

@app.route('/')
def index():
    """一覧ページ：Todoの一覧と新規登録フォームを表示する"""
    todos, _ = get_all_todos()
    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
def add_todo():
    """フォームから送信されたデータで新しいTodoを追加する"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    due_date = request.form.get('due_date', '').strip()

    # タイトルは必須入力
    if not title:
        flash('タイトルを入力してください', 'error')
        return redirect(url_for('index'))

    # 8文字のユニークIDを生成（重複しない識別子）
    todo_id = uuid.uuid4().hex[:8]
    # 登録日時を記録
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # シートに新しい行を追加
    _, sheet = get_all_todos()
    sheet.append_row([todo_id, title, content, due_date, created_at])

    flash('Todoを登録しました', 'success')
    return redirect(url_for('index'))


@app.route('/edit/<todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    """Todoの編集ページを表示・更新する"""

    if request.method == 'POST':
        # POST: フォームの内容でTodoを更新する
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()

        if not title:
            flash('タイトルを入力してください', 'error')
            return redirect(url_for('edit_todo', todo_id=todo_id))

        sheet = get_sheet()
        # A列（id列）を取得して対象のTodoが何行目にあるか探す
        id_column = sheet.col_values(1)
        for i, cell_id in enumerate(id_column):
            if cell_id == todo_id:
                row_num = i + 1  # gspreadは1始まりのインデックス
                # 対象行のtitle・content・due_dateを更新
                sheet.update_cell(row_num, 2, title)
                sheet.update_cell(row_num, 3, content)
                sheet.update_cell(row_num, 4, due_date)
                break

        flash('Todoを更新しました', 'success')
        return redirect(url_for('index'))

    else:
        # GET: 編集フォームを表示する
        todos, _ = get_all_todos()
        # idが一致するTodoを探す
        todo = next((t for t in todos if str(t['id']) == todo_id), None)
        if not todo:
            flash('Todoが見つかりませんでした', 'error')
            return redirect(url_for('index'))
        return render_template('edit.html', todo=todo)


@app.route('/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """指定したidのTodoを削除する"""
    sheet = get_sheet()
    # A列（id列）から対象行を検索して削除
    id_column = sheet.col_values(1)
    for i, cell_id in enumerate(id_column):
        if cell_id == todo_id:
            sheet.delete_rows(i + 1)  # 1-indexed
            break

    flash('Todoを削除しました', 'success')
    return redirect(url_for('index'))


# ========== アプリ起動 ==========

if __name__ == '__main__':
    # Renderなどのサーバーは PORT 環境変数でポートを指定する
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
