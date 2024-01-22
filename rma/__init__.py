import os
from flask import Flask
from datetime import datetime, timedelta, time

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) # tells the app that configuration files are relative to the instance folder
    app.config.from_mapping( # sets some default configuration that the app will use
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'rma.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True) # Notes: 如果不載入外部配置文件，Flask application 只能使用在 app.config.from_mapping 定義的預設配置。可能會限制應用程序的功能，並且難以在不同的環境中進行配置（例如，開發、測試、生產環境）

    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    from . import db
    db.init_app(app) 

    from . import auth
    app.register_blueprint(auth.bp) # 將與身分驗證相關的路由和視圖集中到一個地方

    from . import overview
    app.register_blueprint(overview.bp)
    app.add_url_rule('/', endpoint='index')

    return app


# def serialize_datetime(obj):
#     if isinstance(obj, datetime):
#         obj += timedelta(hours=8)
#         return obj.strftime('%Y/%m/%d %H:%M:%S ')
    
def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S') if obj.time() != time.min else obj.strftime('%Y-%m-%d')
   