import sqlite3

# Xatoliklar bo'lmasligi uchun baza nomi
db = sqlite3.connect("signal_pro.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    vip INTEGER DEFAULT 0,
    pocket_id TEXT DEFAULT NULL,
    referred_by INTEGER DEFAULT NULL,
    invited_count INTEGER DEFAULT 0
)
""")
db.commit()

# Agar eski bazada bu ustunlar bo'lmasa, xatolik bermasdan o'zi qo'shib ketadi:
try:
    cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL")
    db.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN invited_count INTEGER DEFAULT 0")
    db.commit()
except sqlite3.OperationalError:
    pass

def add_user(user_id, username, referred_by=None):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
        (user_id, username, referred_by)
    )
    db.commit()
    
    if referred_by and cursor.rowcount > 0 and referred_by != user_id:
        cursor.execute(
            "UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?",
            (referred_by,)
        )
        db.commit()

def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()

def give_vip(user_id):
    cursor.execute("UPDATE users SET vip = 1 WHERE user_id = ?", (user_id,))
    db.commit()

def check_vip(user_id):
    cursor.execute("SELECT vip FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return 0

def update_pocket_id(user_id, pocket_id):
    cursor.execute("UPDATE users SET pocket_id = ? WHERE user_id = ?", (pocket_id, user_id))
    db.commit()

def get_invited_count(user_id):
    cursor.execute("SELECT invited_count FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return 0
