import datetime
from flask import Flask, jsonify, request, session, render_template
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
import random
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'db', 'lolidle.db')}"
app.secret_key = 'your_secret_key'  # Для работы с сессиями
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    total_points = db.Column(db.Float, default=0)

class GameResult(db.Model):
    __tablename__ = 'game_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    champion_id = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    def __repr__(self):
        return f'<GameResult {self.id} user={self.user_id} champ={self.champion_id} points={self.points}>'

class Champion(db.Model):
    __tablename__ = 'champions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    region = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_random_champion():
    champ = Champion.query.order_by(func.random()).first()
    return champ

# Эндпоинт для получения списка всех персонажей
@app.route('/api/champions', methods=['GET'])
def get_champions():
    champions = Champion.query.all()
    result = []
    for champ in champions:
        result.append({
            "id": champ.id,
            "name": champ.name,
            "role": champ.role
        })
    return jsonify(result)

# Эндпоинт для получения одного персонажа по ID
@app.route('/api/champion/<int:champ_id>', methods=['GET'])
def get_champion(champ_id):
    champ = Champion.query.get(champ_id)
    if champ:
        return jsonify({
            "id": champ.id,
            "name": champ.name,
            "role": champ.role
        })
    else:
        return jsonify({"error": "Champion not found"}), 404
    
from flask import jsonify, request

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    # Найти чемпионов, имя которых начинается с введённой строки (регистр не важен)
    results = Champion.query.filter(Champion.name.ilike(f'{query}%')).all()
    names = [champ.name for champ in results]
    return jsonify(names)


@app.route('/api/start_game', methods=['GET'])
def start_game():
    champion = get_random_champion()
    session['target_id'] = champion.id
    session['target_name'] = champion.name
    session['target_role'] = champion.role
    session['target_gender'] = champion.gender
    session['target_region'] = champion.region
    session['attempts'] = 0
    return jsonify({"message": "Game started", "attempts": 0})

@app.route('/api/guess', methods=['POST'])
def guess():
    data = request.json
    user_guess = data.get('name')
    if not user_guess:
        return jsonify({"error": "Name is required"}), 400

    guessed_champ = Champion.query.filter_by(name=user_guess).first()
    if not guessed_champ:
        return jsonify({"error": "Champion not found"}), 404

    session['attempts'] += 1
    target_id = session.get('target_id')
    if guessed_champ.id == target_id:
        # --- Начало блока сохранения результата ---
        if current_user.is_authenticated:
            attempts = session['attempts']
            points = 100 / attempts
            game_result = GameResult(
                user_id=current_user.id,
                champion_id=target_id,
                attempts=attempts,
                points=points
            )
            db.session.add(game_result)
            db.session.commit()
        # --- Конец блока сохранения результата ---

        return jsonify({
            "result": "correct",
            "attempts": session['attempts']
        })
    else:
        hints = []
        if guessed_champ.role == session.get('target_role'):
            hints.append("Роль совпадает")
        else:
            hints.append("Роль не совпадает")
        if guessed_champ.gender == session.get('target_gender'):
            hints.append("Пол совпадает")
        else:
            hints.append("Пол не совпадает")
        if guessed_champ.region == session.get('target_region'):
            hints.append("Регион совпадает")
        else:
            hints.append("Регион не совпадает")
        return jsonify({
            "result": "wrong",
            "attempts": session['attempts'],
            "hints": hints
        })
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        # Проверка на уникальность пользователя
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация завершена. Можете войти в аккаунт')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    # Получаем все игры пользователя (GameResult — ваша модель результатов)
    games = GameResult.query.filter_by(user_id=current_user.id).order_by(GameResult.timestamp.desc()).all()
    total_games = len(games)
    total_points = sum(game.points for game in games)
    last_20_games = games[:20]
    rating = round(sum(game.points for game in last_20_games) / len(last_20_games), 2) if last_20_games else 0

    return render_template(
        'profile.html',
        username=current_user.username,
        total_games=total_games,
        total_points=round(total_points, 2),
        rating=rating
    )

@app.route('/game')
@login_required
def game():
    # Игровая логика только для авторизованных пользователей
    return render_template('game.html')

if __name__ == '__main__':
    app.run(debug=True)