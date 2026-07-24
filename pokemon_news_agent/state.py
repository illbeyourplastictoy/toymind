"""Простое JSON-хранилище состояния: какие новости уже показывали.

Чтобы одну и ту же новость не предлагать на апрув каждые 6 часов.
"""

import json
import os
import threading

import config

_lock = threading.Lock()


def _load():
    try:
        with open(config.STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"seen_ids": [], "posted_ids": []}


def _save(data):
    tmp = config.STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, config.STATE_FILE)


def get_seen_ids():
    with _lock:
        return set(_load().get("seen_ids", []))


def mark_seen(ids):
    """Помечает новости как показанные (ограничиваем историю 2000 записей)."""
    with _lock:
        data = _load()
        seen = data.get("seen_ids", [])
        seen.extend(i for i in ids if i not in seen)
        data["seen_ids"] = seen[-2000:]
        _save(data)


def mark_posted(ids):
    with _lock:
        data = _load()
        posted = data.get("posted_ids", [])
        posted.extend(i for i in ids if i not in posted)
        data["posted_ids"] = posted[-2000:]
        _save(data)
