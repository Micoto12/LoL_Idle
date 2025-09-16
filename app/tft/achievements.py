from typing import List, Dict, Any

def define_achievements() -> List[Dict[str, Any]]:
    """Возвращает список всех возможных достижений с их условиями."""
    return [
        {
            "id": "top1",
            "name": "Чемпион!",
            "description": "Занять 1 место в матче.",
            "icon": "🏆",
            "condition": lambda match_data, player_data: player_data['placement'] == 1
        },
        {
            "id": "level9",
            "name": "Максимальный уровень",
            "description": "Достичь 9 уровня в матче.",
            "icon": "📈",
            "condition": lambda match_data, player_data: player_data['level'] == 9
        },
        {
            "id": "20gold",
            "name": "Золотой запас",
            "description": "Закончить матч с 20+ золота.",
            "icon": "💰",
            "condition": lambda match_data, player_data: player_data['gold_left'] >= 20
        },
        {
            "id": "6trait",
            "name": "Мастер синергий",
            "description": "Активировать синергию 6-го уровня.",
            "icon": "🧬",
            "condition": lambda match_data, player_data: any(trait['tier_current'] >= 6 for trait in player_data['traits'])
        },
        {
            "id": "3star",
            "name": "Легендарный юнит",
            "description": "Иметь хотя бы одного 3-звездочного юнита.",
            "icon": "⭐",
            "condition": lambda match_data, player_data: any(unit['tier'] == 3 for unit in player_data['units'])
        },
    ]

def check_achievements_for_player(game_name: str, tag_line: str, region: str, match_count: int = 3) -> Dict[str, Any]:
    """
    Анализирует последние матчи игрока и возвращает информацию о полученных достижениях.
    """
    from .api_call import get_puuid_by_riot_id, get_match_ids_by_puuid, get_match_data

    achievements_list = define_achievements()
    unlocked_achievements = []
    analyzed_matches = []

    try:
        puuid = get_puuid_by_riot_id(game_name, tag_line, region)
        match_ids = get_match_ids_by_puuid(puuid, region, count=match_count)

        for match_id in match_ids:
            match_data = get_match_data(match_id, region)
            participants = match_data['info']['participants']
            player_data = next((p for p in participants if p['puuid'] == puuid), None)

            if not player_data:
                continue

            # Сохраняем данные матча для вывода
            match_summary = {
                "id": match_id,
                "placement": player_data['placement'],
                "level": player_data['level'],
                "gold_left": player_data['gold_left'],
                "last_round": player_data['last_round'],
                "traits": [
                    {
                        "name": trait['name'].replace("TFT15_", ""),
                        "tier": trait['tier_current']
                    }
                    for trait in player_data['traits'] if trait['tier_current'] > 0
                ],
                "units": [
                    {
                        "character": unit['character_id'].replace("TFT15_", "").replace("tft15_", ""),
                        "tier": unit['tier'],
                        "items": (
                            [
                                n.replace("TFT_Item_", "").replace("TFT15_Item_", "").replace("TFT_Artifact_", "Artifact_")
                                for n in (unit.get('itemNames', []) if isinstance(unit.get('itemNames'), list) else [])
                                if isinstance(n, str)
                            ]
                            if isinstance(unit.get('itemNames'), (list, type(None))) else []
                        )
                    }
                    for unit in player_data['units']
                ],
                "unlocked_in_match": []
            }

            # Проверяем каждое достижение
            for ach in achievements_list:
                if ach["id"] not in [a["id"] for a in unlocked_achievements]:  # Проверяем только новые
                    if ach["condition"](match_data, player_data):
                        unlocked_achievements.append(ach)
                        match_summary["unlocked_in_match"].append(ach)
        
            analyzed_matches.append(match_summary)

    except Exception as e:
        return {
            "error": str(e),
            "unlocked_achievements": [],
            "analyzed_matches": []
        }

    return {
        "player_name": f"{game_name}#{tag_line}",
        "unlocked_achievements": unlocked_achievements,
        "analyzed_matches": analyzed_matches,
        "error": None
    }