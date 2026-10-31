"""
SQLite State Store & Relational Database Layer
Implements the 5 core database tables from Section 7 of the architecture spec.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent.parent / "founder_box.db"


class Database:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    raw_prompt TEXT,
                    config_yaml TEXT NOT NULL,
                    credit_budget INTEGER DEFAULT 500,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 2. agent_runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    status TEXT NOT NULL, -- PENDING, RUNNING, COMPLETED, FAILED
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    crustdata_credits_used REAL DEFAULT 0.0,
                    summary TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # 3. agent_audit_logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    action_type TEXT NOT NULL, -- CRUSTDATA_SEARCH, LLM_SYNTHESIS, EVENT_EMITTED, POACHING_ALERT
                    summary_message TEXT NOT NULL,
                    raw_json_payload TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            # 4. discovered_entities
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discovered_entities (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL, -- CANDIDATE, VENDOR, VC, COMPETITOR
                    name TEXT NOT NULL,
                    identifier TEXT NOT NULL, -- domain, email, or linkedin URL
                    crustdata_id TEXT,
                    match_score REAL DEFAULT 0.0,
                    status TEXT NOT NULL, -- DISCOVERED, SHORTLISTED, DRAFT_READY, EMAIL_SENT
                    raw_data TEXT, -- Cached JSON from Crustdata
                    email_draft TEXT, -- Personalized draft for outreach
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 5. watcher_subscriptions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watcher_subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL, -- PERSON, COMPANY
                    target_identifier TEXT NOT NULL,
                    crustdata_query_hash TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    last_checked_at TEXT,
                    last_snapshot_hash TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # --------------------------------------------------------------------------
    # CRUD Helper Methods
    # --------------------------------------------------------------------------

    def save_project(self, project_id: str, name: str, raw_prompt: str, config_yaml: str, budget: int = 500):
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO projects (id, name, raw_prompt, config_yaml, credit_budget, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    raw_prompt=excluded.raw_prompt,
                    config_yaml=excluded.config_yaml,
                    credit_budget=excluded.credit_budget,
                    updated_at=excluded.updated_at
            """, (project_id, name, raw_prompt, config_yaml, budget, now, now))
            conn.commit()

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return dict(row) if row else None

    def get_latest_project(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT 1").fetchone()
            return dict(row) if row else None

    def log_agent_action(self, project_id: str, agent_type: str, action_type: str, message: str, payload: Any = None):
        now = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload, default=str) if payload is not None else "{}"
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO agent_audit_logs (project_id, agent_type, action_type, summary_message, raw_json_payload, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, agent_type, action_type, message, payload_str, now))
            conn.commit()

    def get_audit_logs(self, project_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM agent_audit_logs
                WHERE project_id = ?
                ORDER BY id DESC LIMIT ?
            """, (project_id, limit)).fetchall()
            return [dict(r) for r in reversed(rows)]

    def record_agent_run(self, project_id: str, agent_type: str, status: str = "RUNNING") -> str:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO agent_runs (run_id, project_id, agent_type, status, started_at)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, project_id, agent_type, status, now))
            conn.commit()
        return run_id

    def update_agent_run(self, run_id: str, status: str, credits_used: float = 0.0, summary: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE agent_runs
                SET status = ?, completed_at = ?, crustdata_credits_used = crustdata_credits_used + ?, summary = ?
                WHERE run_id = ?
            """, (status, now, credits_used, summary, run_id))
            conn.commit()

    def get_agent_runs(self, project_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM agent_runs WHERE project_id = ? ORDER BY started_at DESC
            """, (project_id,)).fetchall()
            return [dict(r) for r in rows]

    def save_entity(
        self,
        project_id: str,
        entity_type: str,
        name: str,
        identifier: str,
        match_score: float = 0.0,
        status: str = "DISCOVERED",
        raw_data: Any = None,
        email_draft: Optional[str] = None,
        crustdata_id: Optional[str] = None
    ) -> str:
        entity_id = f"ent_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        raw_str = json.dumps(raw_data, default=str) if raw_data is not None else "{}"
        with self.get_connection() as conn:
            # Check for existing entity by project_id and identifier to prevent duplicates
            existing = conn.execute(
                "SELECT id FROM discovered_entities WHERE project_id = ? AND identifier = ?",
                (project_id, identifier)
            ).fetchone()
            if existing:
                ent_id = existing["id"]
                conn.execute("""
                    UPDATE discovered_entities
                    SET name = ?, entity_type = ?, crustdata_id = coalesce(?, crustdata_id),
                        match_score = ?, status = ?, raw_data = ?,
                        email_draft = coalesce(?, email_draft), updated_at = ?
                    WHERE id = ?
                """, (name, entity_type, crustdata_id, match_score, status, raw_str, email_draft, now, ent_id))
                conn.commit()
                return ent_id

            conn.execute("""
                INSERT INTO discovered_entities (id, project_id, entity_type, name, identifier, crustdata_id, match_score, status, raw_data, email_draft, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entity_id, project_id, entity_type, name, identifier, crustdata_id, match_score, status, raw_str, email_draft, now, now))
            conn.commit()
        return entity_id

    def update_entity_status(self, entity_id: str, status: str, email_draft: Optional[str] = None):
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            if email_draft is not None:
                conn.execute("""
                    UPDATE discovered_entities
                    SET status = ?, email_draft = ?, updated_at = ?
                    WHERE id = ?
                """, (status, email_draft, now, entity_id))
            else:
                conn.execute("""
                    UPDATE discovered_entities
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (status, now, entity_id))
            conn.commit()

    def get_entities(self, project_id: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if entity_type:
                rows = conn.execute("""
                    SELECT * FROM discovered_entities
                    WHERE project_id = ? AND entity_type = ?
                    ORDER BY match_score DESC, updated_at DESC
                """, (project_id, entity_type)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM discovered_entities
                    WHERE project_id = ?
                    ORDER BY match_score DESC, updated_at DESC
                """, (project_id,)).fetchall()
            
            res = []
            for r in rows:
                d = dict(r)
                if d.get("raw_data"):
                    try:
                        d["raw_data"] = json.loads(d["raw_data"])
                    except Exception:
                        pass
                res.append(d)
            return res

    def save_watcher(self, project_id: str, entity_type: str, target: str, query_hash: str = "") -> str:
        sub_id = f"watch_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO watcher_subscriptions (subscription_id, project_id, entity_type, target_identifier, crustdata_query_hash, created_at, last_checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sub_id, project_id, entity_type, target, query_hash, now, now))
            conn.commit()
        return sub_id

    def get_watchers(self, project_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM watcher_subscriptions WHERE project_id = ? ORDER BY created_at DESC
            """, (project_id,)).fetchall()
            return [dict(r) for r in rows]


db = Database()

