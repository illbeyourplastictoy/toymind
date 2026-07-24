"""Сбор новостей рынка покемонов из RSS-лент."""

import time
from datetime import datetime, timezone, timedelta

import feedparser

import config


def _entry_id(entry):
    return getattr(entry, "id", None) or getattr(entry, "link", None) or getattr(entry, "title", "")


def _entry_image(entry):
    """Пытается достать URL картинки из RSS-записи."""
    media = entry.get("media_content") or []
    for m in media:
        if m.get("url"):
            return m["url"]
    thumbs = entry.get("media_thumbnail") or []
    for t in thumbs:
        if t.get("url"):
            return t["url"]
    for enc in entry.get("links", []):
        if enc.get("rel") == "enclosure" and str(enc.get("type", "")).startswith("image"):
            return enc.get("href")
    return None


def _entry_dt(entry):
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        return datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc)
    return None


def fetch_items():
    """Возвращает список свежих новостей из всех лент.

    Каждая новость — dict: id, title, link, source, summary, image, published.
    Фильтруем по окну NEWS_WINDOW_HOURS.
    """
    feeds = config.load_feeds()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.NEWS_WINDOW_HOURS)

    items = []
    seen_local = set()
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Не удалось разобрать ленту {url}: {e}")
            continue

        source = parsed.feed.get("title", url)
        for entry in parsed.entries:
            eid = _entry_id(entry)
            if not eid or eid in seen_local:
                continue

            dt = _entry_dt(entry)
            if dt and dt < cutoff:
                continue

            seen_local.add(eid)
            items.append({
                "id": eid,
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "source": source,
                "summary": (entry.get("summary", "") or "").strip(),
                "image": _entry_image(entry),
                "published": dt.isoformat() if dt else None,
            })

    # Свежие сверху
    items.sort(key=lambda x: x["published"] or "", reverse=True)
    return items
