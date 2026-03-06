import sqlite3
import json
from contextlib import contextmanager


class Database(object):
    def __init__(self, db_path):
        self.db_path = db_path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    old_state TEXT,
                    new_state TEXT,
                    attributes_json TEXT,
                    context_user_id TEXT,
                    context_id TEXT,
                    source TEXT,
                    is_manual INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    trigger_entity_id TEXT NOT NULL,
                    trigger_to_state TEXT,
                    condition_type TEXT,
                    condition_value TEXT,
                    action_entity_id TEXT NOT NULL,
                    action_service TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    repetitions INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    yaml_preview TEXT NOT NULL,
                    why_text TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_id INTEGER NOT NULL,
                    feedback TEXT NOT NULL,
                    ts TEXT NOT NULL
                )
            """)

    def insert_event(self, event):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO events (
                    ts, entity_id, domain, old_state, new_state, attributes_json,
                    context_user_id, context_id, source, is_manual
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event["ts"],
                event["entity_id"],
                event["domain"],
                event.get("old_state"),
                event.get("new_state"),
                json.dumps(event.get("attributes", {})),
                event.get("context_user_id"),
                event.get("context_id"),
                event.get("source", "unknown"),
                1 if event.get("is_manual", False) else 0,
            ))

    def get_recent_events(self, seconds=120, entity_id=None):
        with self.connect() as conn:
            query = """
                SELECT *
                FROM events
                WHERE ts >= datetime('now', ?)
            """
            params = [f"-{int(seconds)} seconds"]
            if entity_id:
                query += " AND entity_id = ?"
                params.append(entity_id)
            query += " ORDER BY ts ASC"
            return conn.execute(query, params).fetchall()

    def find_matching_pattern_count(self, trigger_entity_id, trigger_to_state, action_entity_id, action_service):
        with self.connect() as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS cnt
                FROM suggestions
                WHERE trigger_entity_id = ?
                  AND COALESCE(trigger_to_state, '') = COALESCE(?, '')
                  AND action_entity_id = ?
                  AND action_service = ?
            """, (
                trigger_entity_id,
                trigger_to_state,
                action_entity_id,
                action_service,
            )).fetchone()
            return row["cnt"] if row else 0

    def suggestion_exists(self, trigger_entity_id, trigger_to_state, action_entity_id, action_service):
        with self.connect() as conn:
            row = conn.execute("""
                SELECT id
                FROM suggestions
                WHERE trigger_entity_id = ?
                  AND COALESCE(trigger_to_state, '') = COALESCE(?, '')
                  AND action_entity_id = ?
                  AND action_service = ?
                  AND status IN ('new', 'accepted', 'snoozed')
                LIMIT 1
            """, (
                trigger_entity_id,
                trigger_to_state,
                action_entity_id,
                action_service,
            )).fetchone()
            return row is not None

    def insert_suggestion(self, suggestion):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO suggestions (
                    created_at, trigger_entity_id, trigger_to_state, condition_type,
                    condition_value, action_entity_id, action_service, confidence,
                    repetitions, status, yaml_preview, why_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion["created_at"],
                suggestion["trigger_entity_id"],
                suggestion.get("trigger_to_state"),
                suggestion.get("condition_type"),
                suggestion.get("condition_value"),
                suggestion["action_entity_id"],
                suggestion["action_service"],
                suggestion["confidence"],
                suggestion["repetitions"],
                suggestion.get("status", "new"),
                suggestion["yaml_preview"],
                suggestion["why_text"],
            ))

    def get_suggestions(self):
        with self.connect() as conn:
            return conn.execute("""
                SELECT *
                FROM suggestions
                ORDER BY confidence DESC, created_at DESC
            """).fetchall()

    def set_suggestion_status(self, suggestion_id, status):
        with self.connect() as conn:
            conn.execute("""
                UPDATE suggestions
                SET status = ?
                WHERE id = ?
            """, (status, suggestion_id))
