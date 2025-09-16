# app/routes/tft.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.tft.achievements import check_achievements_for_player

bp = Blueprint('tft', __name__, url_prefix='/tft')

@bp.route('/')
@login_required
def index():
    """Главная страница модуля TFT."""
    return render_template('tft/index.html')

@bp.route('/search', methods=['POST'])
@login_required
def search_player():
    """Обрабатывает запрос на поиск игрока и проверку его достижений."""
    game_name = request.form.get('game_name', '').strip()
    tag_line = request.form.get('tag_line', '').strip()
    region = request.form.get('region', '').strip()

    if not game_name or not tag_line:
        flash('Пожалуйста, введите имя, тег и регион.')
        return redirect(url_for('tft.index'))

    # Вызываем функцию для проверки достижений
    result = check_achievements_for_player(game_name, tag_line, region=region , match_count=3)

    if result.get('error'):
        flash(f'Ошибка: {result["error"]}')
        return redirect(url_for('tft.index'))

    # Передаем результат в шаблон
    return render_template(
        'tft/index.html',
        player_name=result['player_name'],
        unlocked_achievements=result['unlocked_achievements'],
        analyzed_matches=result['analyzed_matches']
    )