import sqlite3


def get_db(database):
    """Get a database connection."""
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    return db


def init_db(database):
    """
    Initialize the database with the telemetry table.
    
    Assume that the database name or schema will never change for this exercise.
    In an actual production system, you would want to use a more robust system where it would not be instantiating itself.
    """
    db = get_db(database)
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            satelliteId TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            altitude REAL NOT NULL,
            velocity REAL NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()