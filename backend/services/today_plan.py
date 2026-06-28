"""План «Игра на сегодня»: навыки по возрасту, внимание, игры, рекомендации."""

from __future__ import annotations

import json
import random
from pathlib import Path

from sqlalchemy import select

from backend.data.assessment_scales import (
    SCALE_KEYS,
    SCALE_NAMES,
    SCALE_TO_GAME_SUBSCALE,
    skill_to_score,
)
from backend.db import Game, User, get_game_for_today, get_latest_assessment, get_session
from backend.schemas.today_plan import (
    ExpectedSkillBlock,
    GameSuggestion,
    PracticeTip,
    TodayPlanResponse,
)
from backend.services.games import _is_new_format, _scale_results
from backend.utils.age import calculate_age

_SCALE_JSON = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "griffiths_scale.json").read_text(
        encoding="utf-8"
    )
)


def _expected_skills_for_age(age_months: int) -> list[ExpectedSkillBlock]:
    month = max(1, min(24, age_months))
    blocks: list[ExpectedSkillBlock] = []

    for key in SCALE_KEYS:
        items = _SCALE_JSON["scales"][key]
        at_month = [i for i in items if i["normMonth"] == month]
        if not at_month:
            prior = [i for i in items if i["normMonth"] <= month]
            if prior:
                best = max(i["normMonth"] for i in prior)
                at_month = [i for i in prior if i["normMonth"] == best]
        texts = [i["text"] for i in at_month[:4]]
        if texts:
            blocks.append(
                ExpectedSkillBlock(
                    scale=key,
                    scale_name=SCALE_NAMES[key],
                    skills=texts,
                )
            )
    return blocks


def _weakest_from_assessment(assessment) -> tuple[str | None, int | None]:
    if not assessment or not _is_new_format(assessment):
        return None, None
    scores = {
        k: skill_to_score(k, _scale_results(assessment).get(k))
        for k in SCALE_KEYS
    }
    weakest = min(scores, key=scores.get)
    return SCALE_NAMES[weakest], scores[weakest]


def _attention_points(
    age_months: int,
    focus_name: str,
    has_assessment: bool,
    weakest_name: str | None,
    weakest_score: int | None,
) -> list[str]:
    points: list[str] = [
        f"В {age_months} мес. по шкале Гриффитс ожидаются навыки, перечисленные ниже — "
        "сравните их с тем, что вы видите дома в спокойной обстановке.",
    ]
    if not has_assessment:
        points.append(
            "Пройдите «Шкалу Гриффитс» в приложении — тогда фокус занятий "
            "подстроится под слабые стороны ребёнка."
        )
    elif weakest_score is not None and weakest_score == 0:
        points.append(
            f"По субшкале «{weakest_name}» в тесте 0% — уточните, "
            "предлагались ли задания ребёнку и в каком настроении проходил опрос."
        )
        points.append(
            "Если навыки этой сферы в жизни есть, пересдайте соответствующую часть шкалы."
        )
    elif weakest_name and weakest_score is not None and weakest_score < 60:
        points.append(
            f"Сейчас фокус — «{focus_name}»: эта сфера отстаёт от остальных "
            f"({weakest_score}% в последнем тесте)."
        )
    else:
        points.append(
            f"Сегодня уделяем внимание «{focus_name}» для поддержания гармоничного развития."
        )
    points.append(
        "Не сравнивайте с другими детьми: важна динамика самого малыша за 2–3 недели."
    )
    return points


def _practice_tips(baby_name: str) -> list[PracticeTip]:
    return [
        PracticeTip(icon="⏱", label="Длительность", value="5–10 минут"),
        PracticeTip(icon="🔄", label="Частота", value="2–3 раза в день"),
        PracticeTip(
            icon="😊",
            label="Настроение",
            value=f"Только когда {baby_name} в ресурсе",
        ),
        PracticeTip(
            icon="🏆",
            label="Главное",
            value="Хвалите за попытку, не только за результат",
        ),
    ]


def _important_reminder(focus_scale_name: str) -> str:
    return (
        f"Если через 2–3 недели регулярных занятий навыки субшкалы "
        f"«{focus_scale_name}» не появляются совсем — это повод обратиться "
        "к педиатру или детскому нейропсихологу."
    )


async def _games_for_focus(
    focus_code: str, age_months: int, limit: int = 3
) -> list[Game]:
    async with get_session() as session:
        result = await session.execute(
            select(Game).where(
                Game.subscale == focus_code,
                Game.min_age_months <= age_months,
                Game.max_age_months >= age_months,
            )
        )
        games = list(result.scalars().all())
        if len(games) < limit:
            extra = await session.execute(
                select(Game).where(
                    Game.subscale == focus_code,
                )
            )
            for g in extra.scalars().all():
                if g not in games:
                    games.append(g)
        random.shuffle(games)
        return games[:limit]


async def get_today_plan(user: User) -> TodayPlanResponse:
    age = calculate_age(user.baby_birthday)
    assessment = await get_latest_assessment(user.id)
    has_assessment = assessment is not None and _is_new_format(assessment)

    game_row, focus_code = await get_game_for_today(
        user, age.total_months, assessment
    )
    weakest_name, weakest_score = _weakest_from_assessment(assessment)

    focus_scale_key = next(
        (k for k, v in SCALE_TO_GAME_SUBSCALE.items() if v == focus_code),
        SCALE_KEYS[0],
    )
    focus_scale_name = SCALE_NAMES[focus_scale_key]

    db_games = await _games_for_focus(focus_code, age.total_months, limit=3)
    if not db_games and game_row:
        db_games = [game_row]

    games = [
        GameSuggestion(
            title=g.title,
            develops=g.develops,
            description=g.description,
            safety_rules=g.safety_rules,
        )
        for g in db_games
    ]

    return TodayPlanResponse(
        baby_name=user.baby_name or "Малыш",
        age_label=age.label,
        age_months=age.total_months,
        focus_scale=focus_scale_key,
        focus_scale_name=focus_scale_name,
        focus_subscale_code=focus_code,
        expected_skills=_expected_skills_for_age(age.total_months),
        attention_points=_attention_points(
            age.total_months,
            focus_scale_name,
            has_assessment,
            weakest_name,
            weakest_score,
        ),
        games=games,
        practice_tips=_practice_tips(user.baby_name or "малыш"),
        important_reminder=_important_reminder(focus_scale_name),
        has_assessment=has_assessment,
        weakest_scale_name=weakest_name,
        weakest_score=weakest_score,
    )
