"""
Utility helpers used by the orchestrator.
All paths are relative; use os.path.join for safety with spaces.
"""

import json
import time
import os
import re
from typing import Pattern
from pathlib import Path
from typing import List, Dict


def ensure_dir(path: str):
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)


def safe_append_json(filepath: str, obj: Dict):
    """Append a JSON line to a file in an atomic-friendly way.
    The file contains newline-delimited JSON objects for easy appends.
    """
    # Ensure directory exists
    dirpath = os.path.dirname(filepath) or '.'
    ensure_dir(dirpath)

    # Append a newline-delimited JSON object for simple append semantics.
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def prune_history(history: List[Dict], max_utts: int) -> List[Dict]:
    """Keep only the last `max_utts` utterances from history.
    Each utterance is a dict {sender, role, content, ts}.
    """
    if len(history) <= max_utts:
        return history[:]
    return history[-max_utts:]


def exponential_backoff(func, exceptions=(Exception,), max_tries=3, initial_delay=1.0, **kwargs):
    """Run `func(**kwargs)` with a small exponential backoff retry loop.
    Returns the function result or re-raises the last exception.
    """
    tries = 0
    delay = initial_delay
    while True:
        tries += 1
        try:
            return func(**kwargs)
        except exceptions:
            if tries >= max_tries:
                raise
            time.sleep(delay)
            delay *= 2

# compile common patterns once
_THOUGHT_PATTERNS = [
    re.compile(r'<think>.*?</think>', re.I | re.S),
    re.compile(r'\[THOUGHT[:\s].*?\]', re.I | re.S),
    re.compile(r'^[A-Za-z]+:\s*<think>.*', re.I | re.S),
    # any leading "Role: <think>..." or "Role: " lines we'll remove
    re.compile(r'^[A-Za-z]+:\s*', re.M)
]

def sanitize_reply(text: str) -> str:
    """Remove model internal thoughts and leading role tags, return trimmed text."""
    if not text:
        return text
    t = text
    for p in _THOUGHT_PATTERNS:
        t = p.sub('', t)
    # Remove multiple blank lines and trim
    t = re.sub(r'\n\s*\n+', '\n\n', t).strip()
    return t
