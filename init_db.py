import sqlite3

# Подключение к базе данных
connection = sqlite3.connect('db/lolidle.db')
cursor = connection.cursor()

# Создание таблицы
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Сохранение изменений и закрытие соединения
connection.commit()
connection.close()