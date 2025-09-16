from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required
from app.models import Champion, GameResult
from app import db
from .game import init_new_game, get_random_champion

bp = Blueprint('api', __name__)

@bp.route('/champions', methods=['GET'])
def get_champions():
    champions = Champion.query.all()
    result = []
    for champ in champions:
        result.append({
            "id": champ.id,
            "name": champ.name,
            "role": champ.role,
            "gender": champ.gender,
            "region": champ.region,
            "damage_type": champ.damage_type, # Исправлена опечатка "gamage_type"
            "position": champ.position
        })
    return jsonify(result)

@bp.route('/champion/<int:champ_id>', methods=['GET'])
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

@bp.route('/start_game', methods=['GET'])
def start_game():
    init_new_game()
    return jsonify({"message": "Game started", "attempts": 0})

@bp.route('/game_status', methods=['GET'])
def game_status():
    if 'target_id' not in session or session.get('attempts', 0) == 0:
        init_new_game()
    return jsonify({
        "in_progress": True,
        "attempts": session.get('attempts', 0)
    })

@bp.route('/guess', methods=['POST'])
def guess():
    data = request.json
    user_guess = data.get('name')

    if not user_guess:
        return jsonify({"error": "Введите имя чемпиона!"}), 400

    guessed_champ = Champion.query.filter_by(name=user_guess).first()

    if not guessed_champ:
        return jsonify({"error": "Чемпион не найден!"}), 404

    if 'guessed_names' not in session:
        session['guessed_names'] = []

    if user_guess in session['guessed_names']:
        return jsonify({'error': 'Вы уже вводили этого чемпиона!'}), 400

    session['guessed_names'].append(user_guess)
    session['attempts'] = session.get('attempts', 0) + 1
    session.modified = True

    target_id = session.get('target_id')

    if guessed_champ.id == target_id:
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

        correct_champ_name = session.get('target_name')
        correct_attempts = session.get('attempts')

        session.pop('target_id', None)
        session.pop('target_name', None)
        session.pop('target_role', None)
        session.pop('target_gender', None)
        session.pop('target_region', None)
        session.pop('target_damage_type', None)
        session.pop('target_position', None)
        session.pop('attempts', None)
        session.pop('guessed_names', None)

        return jsonify({
            "result": "correct",
            "attempts": correct_attempts,
            "accepted_name": correct_champ_name
        })
    else:
        hints = []
        guessed_roles = [r.strip() for r in guessed_champ.role.split(',')]
        guessed_positions = [r.strip() for r in guessed_champ.position.split(',')]
        target_role = session.get('target_role', '') or ''
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