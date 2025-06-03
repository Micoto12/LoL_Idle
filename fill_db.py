import sqlite3
import json

# Подключаемся к базе данных
conn = sqlite3.connect('db/lolidle.db')
cursor = conn.cursor()

# Читаем JSON
with open('lol-champions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Извлекаем список чемпионов
champions = data['data']['static_entry']['champions']

# Вставляем данные в таблицу champions
for champ in champions:
    champ_info = champ['value']
    champ_id = champ_info['id']
    champ_name = champ_info['name']
    # Преобразуем список тегов в строку через запятую
    champ_tags = ', '.join(champ_info['tags'])
    # Если нужно сохранить только первый тег, используйте champ_info['tags'][0]
    cursor.execute('''
    INSERT INTO champions (id, name, role)
    VALUES (?, ?, ?)
    ''', (champ_id, champ_name, champ_tags))

conn.commit()
conn.close()
print("База данных успешно заполнена!")