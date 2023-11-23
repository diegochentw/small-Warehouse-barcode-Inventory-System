import sqlite3
import click
from flask import current_app, g

# current_app 用於存取應用程式級別的配置和功能，代表當前 Flask 應用程式的全域變數，例如資料庫連接資訊、應用程式密鑰等。
# g 也是一個全域變數，但它主要用於存儲應用程式上下文中的數據，以便在不同的函式之間共享數據，而不需要額外的參數傳遞。

# 連結資料庫
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect( # 如果 'db' 變數不存在，則這一行建立一個 SQLite3 資料庫連接對象，並將它儲存在 g.db 變數中。資料庫的位置和其他設置是使用 Flask 應用程式的配置（current_app.config）來設定的。
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        ) 
        g.db.row_factory = sqlite3.Row  #設置資料庫連接對象的 row_factory 屬性，使其返回的查詢結果行具有字典樣式的存取方式。

    return g.db

# 關閉資料庫
def close_db(e=None):
    db = g.pop('db', None) # 從'g'這個物件中彈出'db'資訊，並且賦值給'db'，如果'g'不存在此資訊，則將'None'賦值給'g'
    if db is not None: # 如果db不是None，則執行下一行
        db.close()

# 新建資料表
def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


# 註冊application
def init_app(app): ## 為了在Flask應用程序中註冊 close_db 和 init_db_command 函數，以便它們可以被應用程序正確使用
    app.teardown_appcontext(close_db) #函數的目的通常是關閉與資料庫的連接或進行一些類似的清理工作，以確保在請求處理後不會留下未關閉的資源。這有助於避免資源洩漏和提高應用程式的穩定性。
    app.cli.add_command(init_db_command) #是一個用於初始化資料庫的命令，當您需要在應用程式中執行一些初始化工作時，可以透過命令行界面來執行

