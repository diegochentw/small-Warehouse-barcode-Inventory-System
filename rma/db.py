import sqlite3
import click
from flask import current_app, g

# current_app 用於存取應用程式級別的配置和功能，代表當前 Flask 應用程式的全域變數，例如資料庫連接資訊、應用程式密鑰等。
# g 也是一個全域變數，但它主要用於存儲應用程式上下文中的數據，以便在不同的函式之間共享數據，而不需要額外的參數傳遞。

# 連結資料庫
import sqlite3

def get_db():
    """
    Get the SQLite database connection object.

    If the 'db' variable does not exist in the global 'g' object, create a new SQLite3 database connection
    object and store it in the 'g.db' variable. The location and other settings of the database are configured
    using the Flask application's configuration ('current_app.config').

    Returns:
        The SQLite database connection object.

    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

# 關閉資料庫
def close_db(e=None):
    db = g.pop('db', None) # 從'g'這個物件中彈出'db'資訊，並且賦值給'db'，如果'g'不存在此資訊，則將'None'賦值給'g'
    if db is not None: # 如果db不是None，則執行下一行
        db.close()

# 新建資料表
def init_db():
    """
    Initialize the database by executing the schema.sql file.
    """
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        # Read the contents of the schema.sql file
        schema_sql = f.read().decode('utf8')
        
        # Execute the SQL script
        db.executescript(schema_sql)

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


# 註冊application
def init_app(app):
    """
    Registers the `close_db` and `init_db_command` functions in the Flask application.
    
    :param app: The Flask application object.
    """
    app.teardown_appcontext(close_db) 
    """
    Registers the `close_db` function to be called when the application context is torn down.
    This function is typically used to close database connections or perform similar cleanup tasks
    to ensure that no unclosed resources are left after request handling. 
    This helps avoid resource leaks and improves the stability of the application.
    """
    app.cli.add_command(init_db_command)
    """
    Adds the `init_db_command` command to the Flask CLI.
    This command can be used to initialize the database.
    """

