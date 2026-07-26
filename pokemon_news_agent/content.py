"""PLASTIC CULT — генерация редакторской сводки и поста через Claude API."""

import json
import re

import anthropic

import config

_client = anthropic.Anthropic()

_SYSTEM = """You are the editor of PLASTIC CULT — an independent culture media
covering where Pokémon TCG, anime, video games, art and fashion collide.
Tagline: "Worship the object." Pop culture, treated like luxury.

On each run you receive a list of raw stories from RSS/news sources. Do this:
1. Select ONLY what genuinely matters to our readers across our pillars
   (Pokémon/market, anime, games, art, fashion). Drop hype, ads, duplicates,
   and anything off-brand.
2. Write a SHORT digest FOR THE OWNER in Russian (bullet points) — what you
   picked and why.
3. Write ONE ready-to-publish post in ENGLISH, in the PLASTIC CULT voice.

VOICE RULES (strict):
- Editorial and reported, not a hot take. Observation over verdict.
- Cold, confident, few words. No clickbait, no hype, no "smart money".
- NO AI clichés: never "isn't just X, it's Y", no rhetorical questions,
  no exclamation marks, no triadic lists as filler, no "in a world where".
- End on a concrete image or fact, not a moral.
- Do not invent facts — rely only on the provided stories.

If nothing is worth posting, return has_news=false and an empty post.

Also propose the REAL image to use (we use real photos, not generated):
name the exact image and its source (official press / brand / studio / the
source article's own image) plus a credit line. Only suggest generating an
image when no real one could exist (an abstract concept cover).

BRAND STYLE REFERENCE:
---
{style}
---

Reply with ONLY a valid JSON object, no prose, no markdown fence, exactly:
{{
  "has_news": true | false,
  "pillar": "pokemon | anime | games | art | fashion | culture",
  "headline": "short editorial headline, English, Title Case",
  "post": "ready English post in the PLASTIC CULT voice (empty if has_news=false)",
  "summary": "краткая сводка для владельца, по-русски, пунктами",
  "image": {{
    "type": "real | generate",
    "note": "which exact real image to use + where it comes from",
    "source_url": "link to the source/asset if known, else empty",
    "credit": "credit line, e.g. 'Courtesy of ...' (empty if generate)",
    "gen_prompt": "prompt for a concept cover, only if type=generate, else empty"
  }}
}}"""


def _format_items(items):
    lines = []
    for i, it in enumerate(items[: config.MAX_ITEMS], 1):
        lines.append(
            f"{i}. [{it['source']}] {it['title']}\n"
            f"   {it['summary'][:400]}\n"
            f"   Image: {it.get('image') or '—'}\n"
            f"   Link: {it['link']}"
        )
    return "\n".join(lines)


def _extract_json(text):
    """Достаёт JSON-объект из ответа модели (терпимо к обёрткам/фенсам)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Модель не вернула валидный JSON")


def build_digest(items, variation_hint=""):
    """Возвращает dict: has_news, pillar, headline, post, summary, image."""
    style = config.load_style()
    system = _SYSTEM.format(style=style or "(no style file — write cold, editorial, minimal)")

    user = "Fresh stories:\n\n" + _format_items(items)
    if variation_hint:
        user += f"\n\nNote: {variation_hint}"

    resp = _client.messages.create(
        model=config.MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    data = _extract_json(text)

    img = data.get("image") or {}
    return {
        "has_news": bool(data.get("has_news")),
        "pillar": (data.get("pillar") or "").strip(),
        "headline": (data.get("headline") or "").strip(),
        "post": (data.get("post") or "").strip(),
        "summary": (data.get("summary") or "").strip(),
        "image": {
            "type": (img.get("type") or "real").strip(),
            "note": (img.get("note") or "").strip(),
            "source_url": (img.get("source_url") or "").strip(),
            "credit": (img.get("credit") or "").strip(),
            "gen_prompt": (img.get("gen_prompt") or "").strip(),
        },
    }
