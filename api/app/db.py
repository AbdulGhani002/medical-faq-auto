"""Storage layer with a graceful fallback.

If MongoDB is reachable on import we use Motor. Otherwise we fall back to
an in-memory store backed by the JSON files in `data/`. The fallback is
intentional: it means a teammate can clone the repo, run `uvicorn` and
get a working chatbot demo even without Docker installed.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError

from app.config import settings

_client: AsyncIOMotorClient | None = None
_mode: str | None = None  # "mongo" | "memory"
_memdb: "_MemoryDB | None" = None


# ---------------------- in-memory mock -------------------------------------


class _Cursor:
    def __init__(self, items: list[dict]) -> None:
        self._items = list(items)
        self._sort_key: tuple[str, int] | None = None
        self._limit: int | None = None

    def sort(self, key: str, direction: int = 1) -> "_Cursor":
        self._sort_key = (key, direction)
        return self

    def limit(self, n: int) -> "_Cursor":
        self._limit = n
        return self

    def __aiter__(self) -> AsyncIterator[dict]:
        return self._aiter()

    async def _aiter(self) -> AsyncIterator[dict]:
        items = self._items
        if self._sort_key:
            key, direction = self._sort_key
            items = sorted(items, key=lambda d: d.get(key, ""),
                           reverse=direction == -1)
        if self._limit is not None:
            items = items[: self._limit]
        for it in items:
            yield dict(it)  # shallow copy so callers can't mutate the store

    async def to_list(self, length: int | None = None) -> list[dict]:
        out: list[dict] = []
        async for it in self:
            out.append(it)
            if length and len(out) >= length:
                break
        return out


class _Collection:
    def __init__(self, name: str, parent: "_MemoryDB") -> None:
        self.name = name
        self._parent = parent
        self._items: list[dict] = []

    def find(self, query: dict | None = None,
             projection: dict | None = None) -> _Cursor:
        q = query or {}
        out = [it for it in self._items if _match(it, q)]
        if projection:
            cols = [k for k, v in projection.items() if v]
            out = [{k: it.get(k) for k in cols + ["_id"]} for it in out]
        return _Cursor(out)

    async def find_one(self, query: dict | None = None,
                       projection: dict | None = None) -> dict | None:
        cur = self.find(query, projection)
        async for it in cur:
            return dict(it)
        return None

    async def insert_one(self, doc: dict) -> Any:
        doc = dict(doc)
        if "_id" not in doc:
            doc["_id"] = _new_oid()
        self._items.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()

    async def update_one(self, q: dict, update: dict, upsert: bool = False) -> Any:
        match = next((it for it in self._items if _match(it, q)), None)
        if match is None:
            if upsert:
                base = {k: v for k, v in q.items() if not k.startswith("$")}
                base.update(update.get("$set", {}))
                await self.insert_one(base)
                return type("R", (), {"matched_count": 0,
                                       "modified_count": 1})()
            return type("R", (), {"matched_count": 0, "modified_count": 0})()
        for k, v in update.get("$set", {}).items():
            match[k] = v
        return type("R", (), {"matched_count": 1, "modified_count": 1})()

    async def delete_many(self, q: dict) -> Any:
        before = len(self._items)
        self._items = [it for it in self._items if not _match(it, q)]
        return type("R", (), {"deleted_count": before - len(self._items)})()

    async def count_documents(self, q: dict) -> int:
        return sum(1 for it in self._items if _match(it, q))


class _MemoryDB:
    def __init__(self) -> None:
        self.faqs = _Collection("faqs", self)
        self.chat_turns = _Collection("chat_turns", self)
        self.sessions = _Collection("sessions", self)
        self.reactions = _Collection("reactions", self)

    def __getitem__(self, name: str) -> _Collection:
        if not hasattr(self, name):
            setattr(self, name, _Collection(name, self))
        return getattr(self, name)


def _match(doc: dict, q: dict) -> bool:
    for k, v in q.items():
        if isinstance(v, dict):
            if "$ne" in v:
                if doc.get(k) == v["$ne"]:
                    return False
            else:
                # Unsupported: treat as not matching.
                return False
        else:
            if doc.get(k) != v:
                return False
    return True


def _new_oid() -> str:
    """Generate a 24-hex pseudo ObjectId for the memory store."""
    import secrets
    return secrets.token_hex(12)


def _seed_memory(db: _MemoryDB) -> None:
    repo_root = Path(__file__).parent.parent.parent
    loaded = 0
    source = ""

    # 1. Prefer the JSONL bundle if it exists.
    jsonl_path = repo_root / "data" / "faqs.jsonl"
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                doc = {
                    "_id": _new_oid(),
                    "specialty": item["specialty"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "count": item.get("count", 1),
                    "approved": item.get("approved", True),
                    "rejected": False,
                    "cluster_id": item.get("id") or f"mem-{item['specialty']}-{i}",
                    "tags": item.get("tags", []),
                    "updated_at": datetime.utcnow(),
                }
                db.faqs._items.append(doc)
                loaded += 1
        source = "data/faqs.jsonl"

    # 2. Fall back to the per-specialty JSON files.
    if loaded == 0:
        for name in ("faqs_radiology.json", "faqs_physiotherapy.json",
                     "faqs_cardiovascular.json"):
            p = repo_root / "data" / name
            if not p.exists():
                continue
            with p.open("r", encoding="utf-8") as f:
                chunk = json.load(f)
            for i, item in enumerate(chunk):
                doc = {
                    "_id": _new_oid(),
                    "specialty": item["specialty"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "count": item.get("count", 1),
                    "approved": item.get("approved", True),
                    "rejected": False,
                    "cluster_id": f"mem-{item['specialty']}-{i}",
                    "updated_at": datetime.utcnow(),
                }
                db.faqs._items.append(doc)
                loaded += 1
        source = "per-specialty JSON files"

    print(f"[memstore] seeded {loaded} FAQs from {source}")


def _seed_mongo_from_jsonl(db) -> None:
    """One-shot Mongo seed used when the collection is empty.

    Tries ``data/faqs.jsonl`` first, then the per-specialty JSON files.
    The image bakes ``data/`` in so this is always available.
    """
    repo_root = Path(__file__).parent.parent.parent
    docs: list[dict] = []
    jsonl_path = repo_root / "data" / "faqs.jsonl"
    if jsonl_path.is_file():
        with jsonl_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                docs.append({
                    "specialty": item["specialty"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "count": item.get("count", 1),
                    "approved": item.get("approved", True),
                    "rejected": False,
                    "cluster_id": item.get("id") or f"jsonl-{i}",
                    "tags": item.get("tags", []),
                    "updated_at": datetime.utcnow(),
                })
    if not docs:
        for name in ("faqs_radiology.json", "faqs_physiotherapy.json",
                     "faqs_cardiovascular.json"):
            p = repo_root / "data" / name
            if not p.is_file():
                continue
            with p.open("r", encoding="utf-8") as f:
                for i, item in enumerate(json.load(f)):
                    docs.append({
                        "specialty": item["specialty"],
                        "question": item["question"],
                        "answer": item["answer"],
                        "count": item.get("count", 1),
                        "approved": item.get("approved", True),
                        "rejected": False,
                        "cluster_id": f"json-{item['specialty']}-{i}",
                        "updated_at": datetime.utcnow(),
                    })
    if docs:
        db.faqs.insert_many(docs)
        print(f"[mongo] auto-seeded {len(docs)} FAQs into "
              f"{settings.mongo_db}.faqs")


# ---------------------- public API -----------------------------------------


def get_db() -> "AsyncIOMotorDatabase | _MemoryDB":
    global _client, _mode, _memdb
    if _mode == "memory":
        return _memdb  # type: ignore[return-value]
    if _client is not None:
        return _client[settings.mongo_db]
    # First call: probe Mongo synchronously via pymongo client. If forced
    # to memory by env var, skip the probe entirely.
    force_memory = os.environ.get("FAQ_FORCE_MEMORY") == "1"
    if not force_memory:
        try:
            from pymongo import MongoClient
            tester = MongoClient(settings.mongo_uri,
                                 serverSelectionTimeoutMS=2000)
            tester.admin.command("ping")
            # Auto-seed Mongo from JSONL when the FAQ collection is empty.
            # This makes ``docker compose up`` a true one-shot setup.
            db = tester[settings.mongo_db]
            try:
                n = db.faqs.count_documents({})
            except Exception:
                n = 0
            if n == 0:
                _seed_mongo_from_jsonl(db)
            tester.close()
        except Exception:
            force_memory = True
    if force_memory:
        _mode = "memory"
        _memdb = _MemoryDB()
        _seed_memory(_memdb)
        return _memdb
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _mode = "mongo"
    return _client[settings.mongo_db]


def storage_mode() -> str:
    if _mode is None:
        get_db()
    return _mode or "unknown"
