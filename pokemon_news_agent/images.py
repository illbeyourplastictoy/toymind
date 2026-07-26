"""Картинка к посту.

Порядок: сгенерировать через подключаемый image-API (OpenAI-совместимый),
иначе взять картинку из статьи, иначе — без картинки.
Возвращает путь к локальному файлу или URL (Telegram принимает оба), либо None.
"""

import base64
import os
import tempfile

import requests

import config


def _generate(prompt):
    """OpenAI-совместимый вызов images/generations. Возвращает путь к файлу или None."""
    if not (config.IMAGE_API_URL and config.IMAGE_API_KEY and prompt):
        return None
    try:
        resp = requests.post(
            config.IMAGE_API_URL,
            headers={
                "Authorization": f"Bearer {config.IMAGE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.IMAGE_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
            },
            timeout=120,
        )
        if resp.status_code != 200:
            print(f"⚠️ Image API {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json().get("data", [])
        if not data:
            return None
        item = data[0]
        fd, path = tempfile.mkstemp(suffix=".png", prefix="pokenews_")
        os.close(fd)
        if item.get("b64_json"):
            with open(path, "wb") as f:
                f.write(base64.b64decode(item["b64_json"]))
            return path
        if item.get("url"):
            img = requests.get(item["url"], timeout=60)
            if img.status_code == 200:
                with open(path, "wb") as f:
                    f.write(img.content)
                return path
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Ошибка генерации картинки: {e}")
    return None


def get_image(prompt, fallback_url=None):
    """Возвращает путь к файлу / URL картинки или None."""
    path = _generate(prompt)
    if path:
        return path
    if fallback_url:
        return fallback_url
    return None
