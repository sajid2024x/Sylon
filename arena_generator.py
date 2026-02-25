import time
import random
import requests
import sqlite3
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------

DAILY_ARENA_LIMIT = 3
BTC_PRICE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

HIT_LEVELS = [88000, 90000, 92000, 95000]
FLOOR_LEVELS = [82000, 85000, 88000]

DB_PATH = "arenas.db"

# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS arenas (
            arena_id TEXT PRIMARY KEY,
            type TEXT,
            question TEXT,
            target REAL,
            floor REAL,
            deadline TEXT,
            rules TEXT,
            status TEXT,
            outcome TEXT,
            resolved_price REAL,
            created_at TEXT,
            resolved_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arena_id TEXT,
            username TEXT,
            prediction TEXT,
            created_at TEXT,
            UNIQUE(arena_id, username)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            username TEXT PRIMARY KEY,
            total_predictions INTEGER,
            wins INTEGER,
            losses INTEGER,
            current_streak INTEGER,
            max_streak INTEGER
        )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# PRICE FETCHER
# -----------------------------

def get_btc_price():
    return float(requests.get(BTC_PRICE_URL, timeout=10).json()["price"])

# -----------------------------
# ARENA GENERATORS
# -----------------------------

def generate_hit_target_arena(num):
    now = datetime.now(timezone.utc)
    target = random.choice(HIT_LEVELS)
    deadline = now + timedelta(days=3)
    return {
        "arena_id": f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}",
        "type": "CRYPTO",
        "question": f"Will BTC hit {target} USD before {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "target": target,
        "floor": None,
        "deadline": deadline,
        "rules": "YES if BTC price on Binance reaches or exceeds target before deadline.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

def generate_stay_above_arena(num):
    now = datetime.now(timezone.utc)
    floor = random.choice(FLOOR_LEVELS)
    deadline = now + timedelta(days=2)
    return {
        "arena_id": f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}",
        "type": "CRYPTO",
        "question": f"Will BTC stay above {floor} USD until {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "target": None,
        "floor": floor,
        "deadline": deadline,
        "rules": "YES if BTC price on Binance is still above floor at deadline.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

def generate_macro_arena(num):
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(days=2)
    return {
        "arena_id": f"SYLON-{now.strftime('%Y%m%d')}-{num:03d}",
        "type": "MACRO",
        "question": f"Will a major U.S. government economic announcement occur before {deadline.strftime('%Y-%m-%d %H:%M')} UTC?",
        "target": None,
        "floor": None,
        "deadline": deadline,
        "rules": "YES if confirmed by official government announcement.",
        "status": "OPEN",
        "outcome": None,
        "resolved_price": None,
        "created_at": now,
        "resolved_at": None
    }

# -----------------------------
# DATABASE HELPERS
# -----------------------------

def save_arena(arena):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO arenas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        arena["arena_id"], arena["type"], arena["question"],
        arena["target"], arena["floor"], arena["deadline"].isoformat(),
        arena["rules"], arena["status"], arena["outcome"],
        arena["resolved_price"], arena["created_at"].isoformat(),
        arena["resolved_at"].isoformat() if arena["resolved_at"] else None
    ))
    conn.commit()
    conn.close()

def get_arena(arena_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM arenas WHERE arena_id=?", (arena_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "arena_id": r[0],
        "type": r[1],
        "question": r[2],
        "target": r[3],
        "floor": r[4],
        "deadline": datetime.fromisoformat(r[5]),
        "rules": r[6],
        "status": r[7],
        "outcome": r[8],
        "resolved_price": r[9],
        "created_at": datetime.fromisoformat(r[10]),
        "resolved_at": datetime.fromisoformat(r[11]) if r[11] else None
    }

# -----------------------------
# FORMATTERS (X READY)
# -----------------------------

def format_arena_post(arena):
    return (
        "🧠 SYLON PREDICTION ARENA\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"{arena['question']}\n\n"
        f"Deadline: {arena['deadline'].strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        "Reply YES or NO 👇\n\n"
        f"{arena['rules']}"
    )

def format_resolution_post(arena):
    return (
        "🧠 SYLON ARENA RESOLVED\n\n"
        f"Arena ID: {arena['arena_id']}\n\n"
        f"Outcome: {arena['outcome']}\n"
        f"Resolved Price: {arena['resolved_price']}\n\n"
        f"{arena['question']}"
    )

def format_leaderboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, wins, losses,
               ROUND((wins * 100.0) / total_predictions, 2) acc,
               current_streak
        FROM user_stats
        ORDER BY acc DESC, wins DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    conn.close()

    text = "🏆 SYLON LEADERBOARD\n\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. @{r[0]} — {r[3]}% | W:{r[1]} L:{r[2]} | Streak:{r[4]}\n"
    return text

# -----------------------------
# CLI COMMANDS
# -----------------------------

def handle_command(cmd):
    p = cmd.split()
    if not p:
        return
    if p[0] == "post" and p[1] == "arena":
        print(format_arena_post(get_arena(p[2])))
    elif p[0] == "post" and p[1] == "resolution":
        print(format_resolution_post(get_arena(p[2])))
    elif p[0] == "post" and p[1] == "leaderboard":
        print(format_leaderboard())
    else:
        print("Commands:")
        print("post arena <ARENA_ID>")
        print("post resolution <ARENA_ID>")
        print("post leaderboard")

# -----------------------------
# MAIN LOOP
# -----------------------------

if __name__ == "__main__":
    init_db()
    print("\nSylon running (Share Mode Ready).\n")
    while True:
        try:
            cmd = input(">> ").strip()
            if cmd:
                handle_command(cmd)
        except EOFError:
            pass
        time.sleep(1)
