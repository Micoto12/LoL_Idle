import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Инициализация расширений (без привязки к приложению)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Создаём экземпляр Flask, явно указывая корневую директорию
    app = Flask(
        __name__,
        root_path=basedir,
        static_folder='static',  # Папка static находится в root_path
        template_folder='app/templates'  # Папка templates находится внутри app/
    )
    app.config.from_object(config_class)

    # Привязка расширений к приложению
    db.init_app(app)
    login_manager.init_app(app)

    # Регистрация "блупринтов" (blueprints)
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.game import bp as game_bp
    app.register_blueprint(game_bp)

    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # В функции create_app() в app/__init__.py
    from app.routes.tft import bp as tft_bp
    app.register_blueprint(tft_bp)

    # Создание таблиц, если они не существуют
    with app.app_context():
        db.create_all()

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return db.session.get(User, int(user_id))