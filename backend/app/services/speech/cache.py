"""SQLite is shared across workers/restarts; bounded audio and atomic daily budgets."""
import sqlite3
import time
import threading
from contextlib import contextmanager
from pathlib import Path


class AudioCache:
    def __init__(self, path: str, max_bytes: int, ttl: int):
        self.path, self.max_bytes, self.ttl = path, max_bytes, ttl
        self._schema_lock = threading.Lock()
        self._initialized = False

    @contextmanager
    def connection(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with self._schema_lock:
                if not self._initialized:
                    # Concurrent first requests must not race SQLite's WAL transition.
                    for attempt in range(100):
                        try:
                            db.execute("PRAGMA journal_mode=WAL")
                            break
                        except sqlite3.OperationalError as error:
                            if "locked" not in str(error).lower() or attempt == 99:
                                raise
                            time.sleep(0.01)
                    db.execute("CREATE TABLE IF NOT EXISTS audio (key TEXT PRIMARY KEY, data BLOB NOT NULL, created REAL, accessed REAL)")
                    db.execute("CREATE TABLE IF NOT EXISTS budget (day TEXT PRIMARY KEY, characters INTEGER NOT NULL)")
                    db.commit()
                    self._initialized = True
            yield db
            db.commit()
        finally:
            db.close()

    def get(self, key: str) -> bytes | None:
        now = time.time()
        with self.connection() as db:
            db.execute("DELETE FROM audio WHERE created < ?", (now - self.ttl,))
            row = db.execute("SELECT data FROM audio WHERE key = ?", (key,)).fetchone()
            if row:
                db.execute("UPDATE audio SET accessed = ? WHERE key = ?", (now, key))
                return bytes(row[0])
        return None

    def put(self, key: str, data: bytes):
        if len(data) > self.max_bytes:
            return
        now = time.time()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM audio WHERE created < ?", (now - self.ttl,))
            db.execute("INSERT OR REPLACE INTO audio VALUES (?, ?, ?, ?)", (key, data, now, now))
            total = db.execute("SELECT COALESCE(SUM(length(data)), 0) FROM audio").fetchone()[0]
            while total > self.max_bytes:
                oldest = db.execute("SELECT key, length(data) FROM audio ORDER BY accessed LIMIT 1").fetchone()
                db.execute("DELETE FROM audio WHERE key = ?", (oldest[0],))
                total -= oldest[1]

    def reserve_characters(self, count: int, limit: int) -> bool:
        day = time.strftime("%Y-%m-%d", time.gmtime())
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM budget WHERE day != ?", (day,))
            db.execute("INSERT OR IGNORE INTO budget VALUES (?, 0)", (day,))
            used = db.execute("SELECT characters FROM budget WHERE day = ?", (day,)).fetchone()[0]
            if used + count > limit:
                return False
            db.execute("UPDATE budget SET characters = characters + ? WHERE day = ?", (count, day))
            return True
