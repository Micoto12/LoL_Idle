from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/leaderboard')
def leaderboard():
    from app.models import User, GameResult
    from sqlalchemy import func

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

    # Топ-10 по рейтингу
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

    rating_results = sorted(rating_results, key=lambda x: x[1], reverse=True)[:10]

    return render_template(
        'leaderboard.html',
        points_results=points_results,
        rating_results=rating_results
    )

@bp.route('/changelog')
def changelog():
    try:
        with open('version.txt', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "Файл version.txt не найден."
    return render_template('changelog.html', content=content)