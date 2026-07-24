"""Генерация сводки и поста в твоём стиле через Claude API."""

import json
import re

import anthropic

import config

_client = anthropic.Anthropic()

_SYSTEM = """Ты — редактор Telegram-канала про рынок коллекционных карт покемонов
(Pokemon TCG): наборы, чейз-карты, запечатанный продукт, цены, аукционы, тренды.

Твои задачи на каждый запуск:
1. Из списка сырых новостей выбрать только то, что реально важно для РЫНКА
   (цены, спрос, релизы, дефицит, крупные продажи). Отбрось нерелевантное,
   рекламу и дубли.
2. Собрать короткую СВОДКУ для владельца канала (по-русски, пунктами).
3. Написать ОДИН готовый пост для канала СТРОГО в стиле, описанном ниже.

Пиши по-русски. Не выдумывай факты, опирайся только на переданные новости.
Если важных рыночных новостей нет — верни has_news=false и пустой post.

СТИЛЬ КАНАЛА (следуй ему точно):
---
{style}
---

Отвечай ТОЛЬКО валидным JSON-объектом, без пояснений и без markdown-обёртки,
строго такого вида:
{{
  "has_news": true | false,
  "summary": "краткая сводка для владельца, по-русски, пунктами",
  "post": "готовый пост в канал в твоём стиле (пустая строка, если has_news=false)",
  "image_prompt": "короткий промпт на английском для картинки к посту"
}}"""


def _format_items(items):
    lines = []
    for i, it in enumerate(items[: config.MAX_ITEMS], 1):
        lines.append(
            f"{i}. [{it['source']}] {it['title']}\n"
            f"   {it['summary'][:400]}\n"
            f"   Ссылка: {it['link']}"
        )
    return "\n".join(lines)


def _extract_json(text):
    """Достаёт JSON-объект из ответа модели (терпимо к обёрткам/фенсам)."""
    text = text.strip()
    # снять ```json ... ``` если есть
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # взять от первой { до последней }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Модель не вернула валидный JSON")


def build_digest(items, variation_hint=""):
    """Возвращает dict: has_news, summary, post, image_prompt.

    variation_hint — доп. указание при перегенерации ('сделай иначе').
    """
    style = config.load_style()
    system = _SYSTEM.format(style=style or "(стиль не задан — пиши нейтрально и живо)")

    user = "Свежие новости:\n\n" + _format_items(items)
    if variation_hint:
        user += f"\n\nДополнительно: {variation_hint}"

    resp = _client.messages.create(
        model=config.MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    data = _extract_json(text)

    # нормализация полей
    return {
        "has_news": bool(data.get("has_news")),
        "summary": (data.get("summary") or "").strip(),
        "post": (data.get("post") or "").strip(),
        "image_prompt": (data.get("image_prompt") or "").strip(),
    }
