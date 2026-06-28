"""Данные шкалы Гриффитс (0–2 года) из PDF, перевод Кешишян."""

from __future__ import annotations

import json
from pathlib import Path

_DATA_PATH = Path(__file__).with_name("griffiths_scale.json")
_raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))

SCALE_KEYS = tuple(_raw["scales"].keys())
MAX_AGE_MONTHS = _raw.get("maxAgeMonths", 24)

SCALE_NAMES: dict[str, str] = _raw["scaleNames"]

SCALE_SKILLS: dict[str, list[str]] = {
    key: [item["text"] for item in items] for key, items in _raw["scales"].items()
}

SCALE_BALL_BY_TEXT: dict[str, dict[str, int]] = {
    key: {item["text"]: item["ball"] for item in items}
    for key, items in _raw["scales"].items()
}

MAX_BALL_BY_SCALE: dict[str, int] = {
    key: max(balls.values()) if balls else 1 for key, balls in SCALE_BALL_BY_TEXT.items()
}

# Субшкалы A–E в базе игр
SCALE_TO_GAME_SUBSCALE = {
    "locomotion": "A",
    "social": "B",
    "speech": "C",
    "eye_hand": "D",
    "play": "E",
}


def skill_to_score(scale_key: str, skill_text: str | None) -> int:
    """Процент по баллу Гриффитс относительно максимума шкалы."""
    if not skill_text:
        return 0
    ball = SCALE_BALL_BY_TEXT.get(scale_key, {}).get(skill_text)
    if ball is None:
        return 50
    max_ball = MAX_BALL_BY_SCALE.get(scale_key, 51)
    return round(ball / max_ball * 100)
