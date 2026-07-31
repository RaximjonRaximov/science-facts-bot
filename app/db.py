import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("data/facts_bot.db")


class FactsDatabase:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_schema(self) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    username TEXT,
                    daily_enabled INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    fact_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, fact_id)
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_favorites_user
                ON favorites(user_id)
                """
            )

    @contextmanager
    def _cursor(self):
        conn = self._connection()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def ensure_user(self, user_id: int, chat_id: int, username: str | None = None) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (user_id, chat_id, username)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    chat_id=excluded.chat_id,
                    username=excluded.username
                """,
                (user_id, chat_id, username),
            )

    def set_daily(self, user_id: int, enabled: bool) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE users SET daily_enabled = ? WHERE user_id = ?",
                (1 if enabled else 0, user_id),
            )

    def is_daily_enabled(self, user_id: int) -> bool:
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT daily_enabled FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return bool(row and row["daily_enabled"])

    def add_favorite(self, user_id: int, fact_id: int) -> bool:
        try:
            with self._cursor() as cur:
                cur.execute(
                    "INSERT INTO favorites (user_id, fact_id) VALUES (?, ?)",
                    (user_id, fact_id),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_favorite(self, user_id: int, fact_id: int) -> None:
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM favorites WHERE user_id = ? AND fact_id = ?",
                (user_id, fact_id),
            )

    def get_favorites(self, user_id: int) -> list[int]:
        with self._cursor() as cur:
            rows = cur.execute(
                "SELECT fact_id FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            return [row["fact_id"] for row in rows]

    def get_stats(self) -> dict[str, Any]:
        with self._cursor() as cur:
            users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            favorites = cur.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
            daily = cur.execute(
                "SELECT COUNT(*) FROM users WHERE daily_enabled = 1"
            ).fetchone()[0]
        return {"users": users, "favorites": favorites, "daily_subscribers": daily}
