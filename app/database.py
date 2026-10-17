import sqlite3
import os
from flask import g, current_app
from config import Config

def get_db():
    """Retrieve or establish an active SQLite database connection for the current request context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            Config.DATABASE_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database tables using schema.sql."""
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    db = sqlite3.connect(Config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    
    db.commit()
    db.close()

def init_app(app):
    """Register database teardown hook and ensure database is ready."""
    app.teardown_appcontext(close_db)
    # Auto-initialize database on application launch
    with app.app_context():
        init_db()
