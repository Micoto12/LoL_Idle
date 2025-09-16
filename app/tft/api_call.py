import requests
import time
import os
from flask import current_app

# Задержка между запросами (уважаем рейт-лимиты)
REQUEST_DELAY = 0.5  # Увеличим до 1.2 сек, чтобы точно не превысить лимит

def get_riot_api_key():
    """Получает ключ API из переменной окружения или конфига Flask."""
    key = os.environ.get('RIOT_API_KEY')
    print(key)
    if not key:
        # Если не задана переменная, берем из конфига приложения
        key = getattr(current_app.config, 'RIOT_API_KEY', None)
    if not key:
        raise ValueError("RIOT_API_KEY не задан ни в переменных окружения, ни в конфиге приложения.")
    return key

def get_puuid_by_riot_id(game_name: str, tag_line: str, region: str) -> str:
    """
    Получает PUUID по Riot ID (имя#тег) и региону.
    """
    API_KEY = get_riot_api_key()
    BASE_HEADERS = {"X-Riot-Token": API_KEY}

    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    response = requests.get(url, headers=BASE_HEADERS)

    if response.status_code == 404:
        raise ValueError(f"Игрок {game_name}#{tag_line} не найден.")
    elif response.status_code != 200:
        raise Exception(f"Ошибка Riot API: {response.status_code} — {response.text}")

    data = response.json()
    time.sleep(REQUEST_DELAY)  # Уважаем лимиты
    return data['puuid']

def get_match_ids_by_puuid(puuid: str, region: str, count: int = 3) -> list:
    """
    Получает список ID матчей по PUUID
    """
    API_KEY = get_riot_api_key()
    BASE_HEADERS = {"X-Riot-Token": API_KEY}

    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?count={count}"
    response = requests.get(url, headers=BASE_HEADERS)

    if response.status_code != 200:
        raise Exception(f"Ошибка получения матчей: {response.status_code} — {response.text}")

    data = response.json()
    time.sleep(REQUEST_DELAY)
    return data

def get_match_data(match_id: str,  region: str) -> dict:
    """
    Получает полные данные матча по его ID
    """
    API_KEY = get_riot_api_key()
    BASE_HEADERS = {"X-Riot-Token": API_KEY}

    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/{match_id}"
    response = requests.get(url, headers=BASE_HEADERS)

    if response.status_code != 200:
        raise Exception(f"Ошибка получения данных матча {match_id}: {response.status_code} — {response.text}")

    data = response.json()
    time.sleep(REQUEST_DELAY)
    return data