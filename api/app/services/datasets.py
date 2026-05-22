"""Lightweight JSONL dataset registry.

Loads the manifest written by ``data/build_jsonl.py`` and exposes a
small read-only API: list available datasets, count records, peek the
first N rows.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"


def manifest() -> dict:
    p = DATA_DIR / "dataset_manifest.json"
    if not p.is_file():
        return {"files": []}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_datasets() -> list[dict]:
    out: list[dict] = []
    for entry in manifest().get("files", []):
        name = entry.get("name", "")
        p = REPO_ROOT / entry.get("path", "")
        present = p.is_file()
        count = entry.get("records", 0)
        # Verify on-disk count is consistent with the manifest.
        live_count = _count_lines(p) if present else 0
        out.append({
            "name": name,
            "path": str(p.relative_to(REPO_ROOT).as_posix()) if present else None,
            "records_manifest": count,
            "records_on_disk": live_count,
            "present": present,
        })
    return out


def peek(name: str, n: int = 3) -> list[dict]:
    p = DATA_DIR / name
    if not p.is_file():
        return []
    rows: list[dict] = []
    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def iter_jsonl(name: str) -> Iterable[dict]:
    p = DATA_DIR / name
    if not p.is_file():
        return
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _count_lines(p: Path) -> int:
    n = 0
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n
