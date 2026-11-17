import sqlite3

# Xatoliklar bo'lmasligi uchun mutlaqo yangi baza nomini beramiz
db = sqlite3.connect("signal_pro.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    vip INTEGER DEFAULT 0,
    pocket_id TEXT DEFAULT NULL
)
""")
db.commit()

def add_user(user_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username)
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

# Yangi funksiya: ID saqlash
def update_pocket_id(user_id, pocket_id):
    cursor.execute("UPDATE users SET pocket_id = ? WHERE user_id = ?", (pocket_id, user_id))
    db.commit()