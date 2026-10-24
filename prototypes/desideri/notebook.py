"""Isolated prototype: a scoped, durable notebook of users' software wishes.

Not an HTTP server or MCP tool. AuthenticatedPrincipal MUST come from a verified
OAuth/Telegram gateway, never directly from untrusted browser or model input.
"""
from __future__ import annotations

import hashlib
import html
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS wishes (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    project_label TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('registrato','in_analisi','proposto','in_test','in_attesa_approvazione','realizzato','rifiutato')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(tenant_id, user_id, request_id)
);
CREATE INDEX IF NOT EXISTS wishes_owner_idx ON wishes(tenant_id, user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS wish_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wish_id TEXT NOT NULL REFERENCES wishes(id),
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    note TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    tenant_id: str
    user_id: str


class WishConflict(ValueError):
    pass


class WishNotebook:
    def __init__(self, database: sqlite3.Connection):
        self.db = database
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    @staticmethod
    def _text(value: str, limit: int, field: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
            raise ValueError(f"invalid_{field}")
        return value.strip()

    @classmethod
    def _principal(cls, principal: AuthenticatedPrincipal) -> tuple[str, str]:
        if not isinstance(principal, AuthenticatedPrincipal):
            raise ValueError("unverified_principal")
        return (cls._text(principal.tenant_id, 96, "tenant"), cls._text(principal.user_id, 96, "user"))

    @staticmethod
    def _public(row: sqlite3.Row) -> dict:
        return {name: row[name] for name in (
            "id", "request_id", "project_label", "title", "description", "status", "created_at", "updated_at"
        )} | {"source_labels": json.loads(row["sources_json"])}

    def record(self, principal: AuthenticatedPrincipal, *, request_id: str, project_label: str,
               title: str, description: str, source_labels: list[str] | None = None) -> dict:
        tenant_id, user_id = self._principal(principal)
        request_id = self._text(request_id, 96, "request_id")
        project_label = self._text(project_label, 120, "project")
        title = self._text(title, 180, "title")
        description = self._text(description, 4000, "description")
        if source_labels is None:
            source_labels = []
        if not isinstance(source_labels, list) or len(source_labels) > 8:
            raise ValueError("invalid_sources")
        sources = [self._text(label, 120, "source") for label in source_labels]
        # Only explicit source labels are stored: no ChatGPT Project file bytes.
        sources_json = json.dumps(sources, ensure_ascii=False)
        fingerprint = hashlib.sha256(json.dumps(
            [project_label, title, description, sources], ensure_ascii=False,
            separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        stamp = datetime.now(timezone.utc).isoformat()
        wish_id = uuid.uuid4().hex
        with self.db:
            try:
                self.db.execute("""INSERT INTO wishes
                    (id, tenant_id, user_id, request_id, project_label, title,
                     description, sources_json, payload_hash, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'registrato', ?, ?)""",
                    (wish_id, tenant_id, user_id, request_id, project_label, title,
                     description, sources_json, fingerprint, stamp, stamp))
            except sqlite3.IntegrityError:
                prior = self.db.execute("""SELECT * FROM wishes WHERE tenant_id=? AND user_id=? AND request_id=?""",
                                        (tenant_id, user_id, request_id)).fetchone()
                if prior is None or prior["payload_hash"] != fingerprint:
                    raise WishConflict("request_id_reused_for_different_wish") from None
                return self._public(prior)
            self.db.execute("INSERT INTO wish_events (wish_id,event_type,occurred_at,note) VALUES (?, 'registrato', ?, '')",
                            (wish_id, stamp))
        return self.get_mine(principal, wish_id)

    def get_mine(self, principal: AuthenticatedPrincipal, wish_id: str) -> dict | None:
        tenant_id, user_id = self._principal(principal)
        row = self.db.execute("SELECT * FROM wishes WHERE id=? AND tenant_id=? AND user_id=?",
                              (wish_id, tenant_id, user_id)).fetchone()
        return self._public(row) if row else None

    def list_mine(self, principal: AuthenticatedPrincipal, *, limit: int = 50) -> list[dict]:
        tenant_id, user_id = self._principal(principal)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("invalid_limit")
        rows = self.db.execute("""SELECT * FROM wishes WHERE tenant_id=? AND user_id=?
                                  ORDER BY created_at DESC, id DESC LIMIT ?""",
                               (tenant_id, user_id, limit)).fetchall()
        return [self._public(row) for row in rows]

    def history_mine(self, principal: AuthenticatedPrincipal, wish_id: str) -> list[dict]:
        if self.get_mine(principal, wish_id) is None:
            return []
        rows = self.db.execute("""SELECT event_type,occurred_at,note FROM wish_events
                                  WHERE wish_id=? ORDER BY id ASC""", (wish_id,)).fetchall()
        return [dict(row) for row in rows]


def render_private_page(book: WishNotebook, principal: AuthenticatedPrincipal) -> str:
    """HTML for a trusted authenticated web route; NO public endpoint here."""
    pieces = []
    for wish in book.list_mine(principal):
        esc = lambda value: html.escape(str(value), quote=True)
        pieces.append("<article><h2>" + esc(wish["title"]) + "</h2>"
                      + "<p>Progetto: " + esc(wish["project_label"]) + "</p>"
                      + "<p>Stato: " + esc(wish["status"]) + "</p>"
                      + "<p>" + esc(wish["description"]) + "</p>"
                      + "<small>ID: " + esc(wish["id"]) + "</small></article>")
    return ("<!doctype html><html lang='it'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>Il mio quaderno dei desideri</title></head><body>"
            "<main><h1>Il mio quaderno dei desideri</h1>"
            + ("".join(pieces) if pieces else "<p>Nessun desiderio registrato.</p>")
            + "</main></body></html>")
