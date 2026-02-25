import sqlite3
from fastapi import FastAPI

DB_PATH = "arenas.db"

app = FastAPI(title="Sylon Leaderboard")

def get_db():
    return sqlite3.connect(DB_PATH)

@app.get("/")
def home():
    return {
        "name": "Sylon",
        "description": "Public prediction leaderboard",
        "endpoints": ["/leaderboard"]
    }

@app.get("/leaderboard")
def leaderboard(limit: int = 20):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            username,
            total_predictions,
            wins,
            losses,
            ROUND((wins * 100.0) / total_predictions, 2) AS accuracy,
            current_streak,
            max_streak
        FROM user_stats
        WHERE total_predictions > 0
        ORDER BY accuracy DESC, wins DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    results = []
    for rank, r in enumerate(rows, start=1):
        results.append({
            "rank": rank,
            "username": f"@{r[0]}",
            "accuracy": r[4],
            "wins": r[2],
            "losses": r[3],
            "current_streak": r[5],
            "max_streak": r[6]
        })

    return {
        "leaderboard": results
    }
