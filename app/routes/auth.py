from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, GameResult
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация завершена. Можете войти в аккаунт')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Неправильное имя пользователя или пароль')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.')
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
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