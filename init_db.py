import sqlite3

connection = sqlite3.connect('database.db')
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        weight REAL NOT NULL,
        height REAL NOT NULL,
        date TEXT NOT NULL
    )
''')

connection.commit()
connection.close()

