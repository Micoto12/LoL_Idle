from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from sqlalchemy import text
from app.models import Champion, GameResult
from app import db

bp = Blueprint('game', __name__)

def get_random_champion():
    return Champion.query.order_by(func.random()).first()

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
    session['guessed_names'] = []

@bp.route('/')
@login_required
def game_index():
    return render_template('game.html')

@bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '')
    used = request.args.get('used', '')
    used_names = [name.strip() for name in used.split(',') if name.strip()] if used else []

    if not query:
        return jsonify([])

    results = db.session.query(Champion).filter(
        text("name LIKE :q COLLATE NOCASE")
    ).params(q=f"{query}%").all()

    names = [champ.name for champ in results if champ.name not in used_names]
    return jsonify(names)

@bp.route('/debug/used')
def debug_used():
    return jsonify(session.get('guessed_names', []))

@bp.route('/admin/reset_used', methods=['POST'])
@login_required
def admin_reset_used():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    session['guessed_names'] = []
    return jsonify({'status': 'ok'})

@bp.route('/admin/reset_attempts', methods=['POST'])
@login_required
def admin_reset_attempts():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    session['attempts'] = 0
    return jsonify({'status': 'ok'})

@bp.route('/admin/show_target', methods=['GET'])
@login_required
def admin_show_target():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    target_name = session.get('target_name')
    return jsonify({'target_name': target_name})