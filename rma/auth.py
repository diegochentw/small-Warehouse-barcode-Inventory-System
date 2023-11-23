import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from rma.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth') # a Blueprint named 'auth'. Like the application object, the blueprint needs to know where it’s defined, so __name__ is passed as the second argument. The url_prefix will be prepended to all the URLs associated with the blueprint.

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['user_id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE user_id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view): #定義了一個名為 login_required 的函數，它接受一個參數 view。這個函數將作為裝飾器使用，用於裝飾需要保護的視圖函數。
    @functools.wraps(view) #使用 @ 語法將 functools.wraps(view) 裝飾器應用於下面的 wrapped_view 函數。functools.wraps 用於保留 view 函數的元數據，以確保 wrapped_view 的行為不會影響原始視圖函數。
    def wrapped_view(**kwargs): # 定義了一個名為 wrapped_view 的內部函數，這將成為實際用於保護視圖函數的函數。
        if g.user is None: # 檢查全局變數 g.user 是否為 None。通常情況下，g.user 可能是用戶對象，表示當前登錄的使用者。
            return redirect(url_for('auth.login')) # 如果 g.user 是 None，則執行重定向操作，將使用者導向登錄頁面。這意味著如果使用者未登錄，將無法訪問該視圖，而被重定向到登錄頁面。
        
        return view(**kwargs) # 如果使用者已登錄（g.user 不是 None），則呼叫原始的視圖函數 view 並將任何關鍵字引數（kwargs）傳遞給它。
    
    return wrapped_view # 返回內部函數 wrapped_view，這意味著當您將 @login_required 裝飾器應用於某個視圖函數時，實際上是使用 wrapped_view 來保護該視圖函數，確保只有登錄的使用者可以訪問它。