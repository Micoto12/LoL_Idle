import datetime
from flask import Flask, jsonify, request, session, render_template
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy import text
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
    damage_type = db.Column(db.String(50))
    position = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_random_champion():
    champ = db.session.query(Champion).order_by(func.random()).first()
    return champ

def init_new_game():
    champion = get_random_champion()
    session['target_id'] = champion.id
    session['target_name'] = champion.name
    session['target_role'] = champion.role
    session['target_gender'] = champion.gender
    session['target_region'] = champion.region
    session['target_damage_type'] = champion.damage_type
    session['target_position'] = champion.position
    session['attempts'] = 0
    session['guessed_names'] = []  # Сброс использованных чемпионов

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
    champ = db.session.get(Champion, champ_id)
    if champ:
        return jsonify({
            "id": champ.id,
            "name": champ.name,
            "role": champ.role
        })
    else:
        return jsonify({"error": "Champion not found"}), 404
    
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '')
    used = request.args.get('used', '')
    used_names = [name.strip() for name in used.split(',') if name.strip()] if used else []

    if not query:
        return jsonify([])

    results = db.session.query(Champion).filter(
        text("name LIKE :q COLLATE NOCASE")
    ).params(q=f"{query}%").all()

    # Исключаем использованных
    names = [champ.name for champ in results if champ.name not in used_names]
    return jsonify(names)

@app.route('/api/start_game', methods=['GET'])
def start_game():
    init_new_game()
    return jsonify({"message": "Game started", "attempts": 0})

@app.route('/api/game_status', methods=['GET'])
def game_status():
    if session.get('attempts', 0) == 0 or 'target_id' not in session:
        init_new_game()
    return jsonify({"in_progress": True, "attempts": session.get('attempts', 0)})

@app.route('/api/guess', methods=['POST'])
def guess():
    data = request.json
    user_guess = data.get('name')

    # Проверка на пустой ввод
    if not user_guess:
        return jsonify({"error": "Введите имя чемпиона!"}), 400
    guessed_champ = db.session.query(Champion).filter_by(name=user_guess).first()

    # Проверка существования чемпиона
    if not guessed_champ:
        return jsonify({"error": "Чемпион не найден!"}), 404

    # Инициализация списка, если его нет
    if 'guessed_names' not in session:
        session['guessed_names'] = []

    # Проверка на повтор
    if user_guess in session['guessed_names']:
        return jsonify({'error': 'Вы уже вводили этого чемпиона!'}), 400

    # Добавляем имя в список попыток
    session['guessed_names'].append(user_guess)
    session['attempts'] = session.get('attempts', 0) + 1
    session.modified = True

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
        session['attempts'] = 0
        session['guessed_names'] = []
        return jsonify({
            "result": "correct",
            "attempts": session['attempts'],
            "accepted_name": guessed_champ.name
        })
    else:
        hints = []
        guessed_roles = [r.strip() for r in guessed_champ.role.split(',')]
        guessed_positions = [r.strip() for r in guessed_champ.position.split(',')]
        target_role = session.get('target_role', '') or ''  # Гарантирует строку даже если None
        target_roles = [r.strip() for r in target_role.split(',') if r.strip()]
        target_position = session.get('target_position', '') or ''
        target_positions = [r.strip() for r in target_position.split(',') if r.strip()]

        guessed_set = set(guessed_roles)
        target_set = set(target_roles)

        if guessed_set == target_set:
            hints.append(f"Роль: {', '.join(guessed_roles)} ✅")
        elif guessed_set & target_set:
            common_roles = guessed_set & target_set
            hints.append(f"Роль: частично совпадает ({', '.join(common_roles)}) ⚠️")
        else:
            hints.append(f"Роль: {', '.join(guessed_roles)} ❌")

        guessed_set = set(guessed_positions)
        target_set = set(target_positions)

        if guessed_set == target_set:
            hints.append(f"Позиция: {', '.join(guessed_positions)} ✅")
        elif guessed_set & target_set:
            common_positions = guessed_set & target_set
            hints.append(f"Позиция: частично совпадает ({', '.join(common_positions)}) ⚠️")
        else:
            hints.append(f"Позиция: {', '.join(guessed_positions)} ❌")

        if guessed_champ.gender == session.get('target_gender'):
            hints.append("Пол: " + guessed_champ.gender + " ✅")
        else:
            hints.append("Пол: " + guessed_champ.gender + " ❌")
        
        if guessed_champ.region == session.get('target_region'):
            hints.append("Регион: " + guessed_champ.region + " ✅")
        else:
            hints.append("Регион: " + guessed_champ.region + " ❌")
        
        if guessed_champ.damage_type == session.get('target_damage_type'):
            hints.append("Тип урона:" + guessed_champ.damage_type + " ✅")
        else:
            hints.append("Тип урона: " + guessed_champ.damage_type + " ❌")
        
        return jsonify({
            "result": "wrong",
            "attempts": session['attempts'],
            "hints": hints,
            "accepted_name": guessed_champ.name
        })
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Проверка на уникальность пользователя
        if db.session.query(User).filter_by(username=username).first():
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
        user = db.session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль')
            return redirect(url_for('login'))
    return render_template('login.html')

from flask_login import logout_user, login_required
from flask import redirect, url_for, flash

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.')
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    # Получаем все игры пользователя (GameResult — ваша модель результатов)
    games = db.session.query(GameResult).filter_by(user_id=current_user.id).order_by(GameResult.timestamp.desc()).all()
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

@app.route('/leaderboard')
def leaderboard():
    # Топ-10 по сумме очков
    points_results = (
        db.session.query(
            User.username,
            func.sum(GameResult.points).label('total_points')
        )
        .join(GameResult, User.id == GameResult.user_id)
        .group_by(User.id)
        .order_by(func.sum(GameResult.points).desc())
        .limit(10)
        .all()
    )

    # Топ-10 по рейтингу (средний рейтинг за последние 20 игр каждого пользователя)
    rating_results = []
    users = db.session.query(User).all()
    for user in users:
        last_20_games = (
            db.session.query(GameResult)
            .filter_by(user_id=user.id)
            .order_by(GameResult.id.desc())
            .limit(20)
            .all()
        )
        if last_20_games:
            avg_rating = sum(gr.points for gr in last_20_games) / len(last_20_games)
            rating_results.append((user.username, avg_rating))
    # Отсортировать по рейтингу и взять топ-10
    rating_results = sorted(rating_results, key=lambda x: x[1], reverse=True)[:10]

    return render_template(
        'leaderboard.html',
        points_results=points_results,
        rating_results=rating_results
    )

@app.route('/changelog')
def changelog():
    try:
        with open('version.txt', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "Файл version.txt не найден."
    return render_template('changelog.html', content=content)

@app.route('/game')
@login_required
def game():
    # Игровая логика только для авторизованных пользователей
    return render_template('game.html')

@app.route('/debug/used')
def debug_used():
    return jsonify(session.get('guessed_names', []))

from flask_login import current_user, login_required

@app.route('/admin/reset_used', methods=['POST'])
@login_required
def admin_reset_used():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    session['guessed_names'] = []
    return jsonify({'status': 'ok'})

@app.route('/admin/reset_attempts', methods=['POST'])
@login_required
def admin_reset_attempts():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    session['attempts'] = 0
    return jsonify({'status': 'ok'})

@app.route('/admin/show_target', methods=['GET'])
@login_required
def admin_show_target():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    target_name = session.get('target_name')
    return jsonify({'target_name': target_name})

if __name__ == '__main__':
    app.run(debug=True)