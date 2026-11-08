"""Shared helpers: the node's normalisation, row identity, JSONL I/O, the kit's render."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "third_party" / "telegraph-wasm-baseline"
FOUNDATION = ROOT / "third_party" / "foundation"

INTENTS = {
    # family prefix -> (file stem, eval-pool child intent)
    "SECURITY_REVIEW": ("security_review", "SECURITY_REVIEW_GENERAL"),
    "SMART_CONTRACT_AUDIT": ("smart_contract_audit", "SMART_CONTRACT_AUDIT_GENERAL"),
}

SPLIT_DIRS = {"public": "public", "validation": "validation", "private": "private"}
SPLIT_SUFFIX = {"public": "train", "validation": "val", "private": "pool"}

ADVISORY_ID = re.compile(r"\b(?:CVE-\d{4}-\d{4,7}|GHSA(?:-[23456789cfghjmpqrvwx]{4}){3})\b", re.I)
_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    """The node's prompt normalisation: Unicode NFC, runs of whitespace -> one space."""
    return _WS.sub(" ", unicodedata.normalize("NFC", text)).strip()


def row_id(prompt: str, chosen: str, rejected: str) -> str:
    h = hashlib.sha256()
    h.update("\x00".join(normalise(x) for x in (prompt, chosen, rejected)).encode())
    return h.hexdigest()


def render(prompt: str, answer: str) -> str:
    """The node's RenderForJudgment, character for character (kit train_adapter.render)."""
    return f"### Task:\n{prompt}\n\n### Answer:\n{answer}"


def read_jsonl(path: Path) -> Iterator[tuple[int, dict]]:
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                yield n, json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def output_path(intent: str, split: str) -> Path:
    stem, child = INTENTS[intent]
    name = (child.lower() if split == "private" else stem) + f".{SPLIT_SUFFIX[split]}.jsonl"
    return ROOT / "data" / SPLIT_DIRS[split] / name


def meta_path(intent: str, split: str) -> Path:
    stem, _ = INTENTS[intent]
    base = ROOT / "data" / ("private" if split == "private" else "meta")
    return base / f"{stem}.{SPLIT_SUFFIX[split]}.meta.jsonl"


def load_sources() -> dict[str, dict]:
    """Every advisory id and alias -> its verified source record."""
    out: dict[str, dict] = {}
    p = ROOT / "data" / "sources" / "sources.jsonl"
    if not p.exists():
        return out
    for _, r in read_jsonl(p):
        for k in [r["id"], *r.get("cves", [])]:
            out[k.upper()] = r
    return out
