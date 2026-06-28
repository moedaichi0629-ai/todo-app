import os
import uuid
import json
import requests
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# .env ファイルを読み込む
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Google Sheets API に必要な権限（スコープ）
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# スプレッドシートの列定義
HEADERS = ['id', 'title', 'content', 'due_date', 'created_at', 'status', 'priority']


# ========== Google Sheets 接続 ==========

def get_sheet():
    """Google Sheets に接続してシートオブジェクトを返す"""
    try:
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            # 本番環境（Render）: 環境変数の JSON 文字列から認証
            creds = Credentials.from_service_account_info(
                json.loads(creds_json), scopes=SCOPES
            )
        else:
            # ローカル開発: credentials.json ファイルから認証
            creds = Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES
            )
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).sheet1

    except FileNotFoundError:
        raise Exception(
            'credentials.json が見つかりません。'
            'ファイルを配置するか GOOGLE_CREDENTIALS_JSON 環境変数を設定してください。'
        )
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(
            f'スプレッドシートが見つかりません（ID: {SPREADSHEET_ID}）。'
            'SPREADSHEET_ID を確認し、サービスアカウントと共有されているか確認してください。'
        )
    except Exception as e:
        raise Exception(f'Google Sheets への接続に失敗しました: {e}')


def init_sheet(sheet):
    """
    シートのヘッダーを確認し、必要に応じて初期化・列を追加する。
    既存データは消えないよう、不足列のみ追記する。
    """
    try:
        first_row = sheet.row_values(1)

        if not first_row or first_row[0] != 'id':
            # シートが空またはヘッダーが全くない → 初期化
            sheet.clear()
            sheet.insert_row(HEADERS, 1)

        else:
            # 不足している列だけ右端に追加する（既存データを守る）
            for col_name in HEADERS:
                if col_name not in first_row:
                    next_col = len(first_row) + 1
                    sheet.update_cell(1, next_col, col_name)
                    first_row.append(col_name)  # ローカルの状態も更新

                    # status 列を追加した場合は既存行に 'incomplete' を設定
                    if col_name == 'status':
                        all_values = sheet.get_all_values()
                        # 2行目以降のデータ行だけ対象にする
                        for row_idx in range(2, len(all_values) + 1):
                            row = all_values[row_idx - 1]
                            if any(c.strip() for c in row):
                                sheet.update_cell(row_idx, next_col, 'incomplete')

    except Exception as e:
        raise Exception(f'シートの初期化に失敗しました: {e}')


def get_initialized_sheet():
    """接続と初期化を済ませたシートを返すユーティリティ"""
    sheet = get_sheet()
    init_sheet(sheet)
    return sheet


def get_all_todos():
    """
    全 Todo を取得し、期日ステータス（due_status）を付加して返す。
    due_status: 'overdue' / 'today' / 'tomorrow' / 'upcoming' / ''
    """
    sheet = get_initialized_sheet()

    try:
        records = sheet.get_all_records()
    except Exception as e:
        raise Exception(f'Todo の取得に失敗しました: {e}')

    today = date.today()
    tomorrow = today + timedelta(days=1)

    for todo in records:
        # status が空（旧データ）は incomplete として扱う
        if not todo.get('status'):
            todo['status'] = 'incomplete'

        # 期日を解析して due_status を付与
        due_str = str(todo.get('due_date', '')).strip()
        if due_str:
            try:
                due = date.fromisoformat(due_str)
                if due < today:
                    todo['due_status'] = 'overdue'
                elif due == today:
                    todo['due_status'] = 'today'
                elif due == tomorrow:
                    todo['due_status'] = 'tomorrow'
                else:
                    todo['due_status'] = 'upcoming'
            except ValueError:
                todo['due_status'] = ''
        else:
            todo['due_status'] = ''

    return records, sheet


# ========== LINE 通知 ==========

def send_line_message(target_todos):
    """
    LINE Messaging API でプッシュ通知を送る。
    戻り値: (成功: bool, メッセージ: str)
    """
    token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    user_id = os.getenv('LINE_USER_ID')

    if not token or not user_id:
        return False, 'LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が設定されていません'

    # due_status ごとのラベル
    label_map = {
        'overdue':  '⚠️ 期限切れ',
        'today':    '🔴 今日が期限',
        'tomorrow': '🟡 明日が期限',
    }

    # メッセージ本文を組み立てる
    lines = ['📋 Todoリスト 期日通知\n']
    for todo in target_todos:
        label = label_map.get(todo.get('due_status', ''), '')
        lines.append(f"{label}\n・{todo['title']}（期日: {todo['due_date']}）")

    message_text = '\n\n'.join(lines)

    try:
        res = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={
                'to': user_id,
                'messages': [{'type': 'text', 'text': message_text}],
            },
            timeout=10,
        )
        if res.status_code == 200:
            return True, 'success'
        else:
            return False, f'LINE API エラー（{res.status_code}）: {res.text}'

    except requests.exceptions.Timeout:
        return False, 'LINE API へのリクエストがタイムアウトしました'
    except Exception as e:
        return False, f'LINE 通知の送信に失敗しました: {e}'


# ========== ルーティング ==========

@app.route('/')
def index():
    """一覧ページ：検索・フィルター・Todo リスト表示"""
    try:
        todos, _ = get_all_todos()
    except Exception as e:
        flash(f'エラー: {e}', 'error')
        todos = []

    # クエリパラメータから検索・フィルター条件を取得
    query            = request.args.get('q', '').strip()
    status_filter    = request.args.get('status', 'all')    # all / incomplete / completed
    due_filter       = request.args.get('due', 'all')        # all / overdue / today / tomorrow
    priority_filter  = request.args.get('priority', 'all')   # all / high / medium / low

    filtered = todos

    # キーワード検索（タイトル・内容を対象）
    if query:
        filtered = [
            t for t in filtered
            if query.lower() in str(t.get('title', '')).lower()
            or query.lower() in str(t.get('content', '')).lower()
        ]

    # 完了ステータスでフィルター
    if status_filter != 'all':
        filtered = [t for t in filtered if t.get('status') == status_filter]

    # 期日ステータスでフィルター
    if due_filter != 'all':
        filtered = [t for t in filtered if t.get('due_status') == due_filter]

    # 優先順位でフィルター
    if priority_filter != 'all':
        filtered = [t for t in filtered if t.get('priority') == priority_filter]

    # 優先順位で並び替え（高→中→低→未設定）
    priority_order = {'high': 0, 'medium': 1, 'low': 2, '': 3}
    filtered.sort(key=lambda t: priority_order.get(t.get('priority', ''), 3))

    return render_template(
        'index.html',
        todos=filtered,
        total_count=len(todos),
        query=query,
        status_filter=status_filter,
        due_filter=due_filter,
        priority_filter=priority_filter,
    )


@app.route('/add', methods=['POST'])
def add_todo():
    """フォームから送信されたデータで新しい Todo を追加する"""
    title    = request.form.get('title', '').strip()
    content  = request.form.get('content', '').strip()
    due_date = request.form.get('due_date', '').strip()
    priority = request.form.get('priority', '').strip()   # high / medium / low / ''

    if not title:
        flash('タイトルを入力してください', 'error')
        return redirect(url_for('index'))

    todo_id    = uuid.uuid4().hex[:8]
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        sheet = get_initialized_sheet()
        # priority 列も含めて追加
        sheet.append_row([todo_id, title, content, due_date, created_at, 'incomplete', priority])
        flash('Todo を登録しました', 'success')
    except Exception as e:
        flash(f'登録に失敗しました: {e}', 'error')

    return redirect(url_for('index'))


@app.route('/edit/<todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    """Todo の編集ページ表示・更新"""
    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        content  = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', '').strip()

        if not title:
            flash('タイトルを入力してください', 'error')
            return redirect(url_for('edit_todo', todo_id=todo_id))

        try:
            sheet   = get_initialized_sheet()
            headers = sheet.row_values(1)
            id_col  = sheet.col_values(1)

            for i, cell_id in enumerate(id_col):
                if cell_id == todo_id:
                    row_num = i + 1
                    sheet.update_cell(row_num, headers.index('title') + 1,    title)
                    sheet.update_cell(row_num, headers.index('content') + 1,  content)
                    sheet.update_cell(row_num, headers.index('due_date') + 1, due_date)
                    if 'priority' in headers:
                        sheet.update_cell(row_num, headers.index('priority') + 1, priority)
                    break

            flash('Todo を更新しました', 'success')
        except Exception as e:
            flash(f'更新に失敗しました: {e}', 'error')

        return redirect(url_for('index'))

    else:
        try:
            todos, _ = get_all_todos()
            todo = next((t for t in todos if str(t['id']) == todo_id), None)
            if not todo:
                flash('Todo が見つかりませんでした', 'error')
                return redirect(url_for('index'))
            return render_template('edit.html', todo=todo)
        except Exception as e:
            flash(f'エラー: {e}', 'error')
            return redirect(url_for('index'))


@app.route('/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """指定した Todo を削除する"""
    try:
        sheet  = get_initialized_sheet()
        id_col = sheet.col_values(1)

        for i, cell_id in enumerate(id_col):
            if cell_id == todo_id:
                sheet.delete_rows(i + 1)
                break

        flash('Todo を削除しました', 'success')
    except Exception as e:
        flash(f'削除に失敗しました: {e}', 'error')

    return redirect(url_for('index'))


@app.route('/toggle/<todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    """① 完了 / 未完了を切り替える"""
    try:
        sheet   = get_initialized_sheet()
        headers = sheet.row_values(1)

        if 'status' not in headers:
            flash('status 列が見つかりません。ページを再読み込みしてください。', 'error')
            return redirect(url_for('index'))

        status_col = headers.index('status') + 1
        id_col     = sheet.col_values(1)

        for i, cell_id in enumerate(id_col):
            if cell_id == todo_id:
                row_num        = i + 1
                current_status = sheet.cell(row_num, status_col).value or 'incomplete'
                new_status     = 'incomplete' if current_status == 'completed' else 'completed'
                sheet.update_cell(row_num, status_col, new_status)
                label = '完了' if new_status == 'completed' else '未完了'
                flash(f'Todo を{label}にしました', 'success')
                break

    except Exception as e:
        flash(f'ステータスの更新に失敗しました: {e}', 'error')

    return redirect(url_for('index'))


@app.route('/notify/line', methods=['POST'])
def notify_line():
    """③ 期日が近い未完了 Todo を LINE に通知する"""
    try:
        todos, _ = get_all_todos()
    except Exception as e:
        flash(f'Todo の取得に失敗しました: {e}', 'error')
        return redirect(url_for('index'))

    # 通知対象: 未完了 かつ（期限切れ / 今日 / 明日）
    target = [
        t for t in todos
        if t.get('status') != 'completed'
        and t.get('due_status') in ('overdue', 'today', 'tomorrow')
    ]

    if not target:
        flash(
            '通知対象のTodoはありませんでした'
            '（未完了で期日が今日・明日・期限切れのTodoがありません）',
            'info'
        )
        return redirect(url_for('index'))

    success, message = send_line_message(target)

    if success:
        flash(f'LINE に {len(target)} 件の Todo を通知しました', 'success')
    else:
        flash(f'LINE 通知に失敗しました: {message}', 'error')

    return redirect(url_for('index'))


# ========== アプリ起動 ==========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
