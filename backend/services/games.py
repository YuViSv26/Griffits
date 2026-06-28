from backend.data.assessment_scales import SCALE_KEYS, SCALE_NAMES, skill_to_score
from backend.db import (
    User,
    get_assessment_history,
    get_game_for_today,
    get_latest_assessment,
)
from backend.schemas.games import GameResponse, ProgressItem, ProgressResponse
from backend.utils.age import calculate_age

# Для обратной совместимости со старыми тестами Гриффитс A–E
from backend.constants import SUBSCALE_NAMES


async def get_today_game(user: User) -> GameResponse | None:
    age = calculate_age(user.baby_birthday)
    assessment = await get_latest_assessment(user.id)
    game, focus = await get_game_for_today(user, age.total_months, assessment)

    if game is None:
        return None

    focus_name = SUBSCALE_NAMES.get(focus, focus)
    return GameResponse(
        id=game.id,
        title=game.title,
        subscale=game.subscale,
        subscale_name=SUBSCALE_NAMES[game.subscale],
        age_label=age.label,
        focus_subscale=focus,
        focus_subscale_name=focus_name,
        develops=game.develops,
        description=game.description,
        safety_rules=game.safety_rules,
    )


def _is_new_format(assessment) -> bool:
    return assessment.child_age_months is not None and (
        assessment.result_locomotion is not None
        or assessment.result_social is not None
        or assessment.result_speech is not None
        or assessment.result_eye_hand is not None
        or assessment.result_play is not None
        or assessment.result_gross_motor is not None
    )


def _scale_results(assessment) -> dict[str, str | None]:
    if assessment.result_locomotion is not None or assessment.result_eye_hand is not None:
        return {k: getattr(assessment, f"result_{k}", None) for k in SCALE_KEYS}
    # Совместимость со старой 4-шкальной моделью
    legacy = {
        "locomotion": assessment.result_gross_motor,
        "social": assessment.result_social,
        "speech": assessment.result_speech,
        "eye_hand": assessment.result_fine_motor,
        "play": None,
    }
    return legacy


async def get_progress(user: User) -> ProgressResponse:
    history = await get_assessment_history(user.id, limit=2)

    if not history:
        return ProgressResponse(
            baby_name=user.baby_name,
            last_test_date=None,
            items=[],
            strongest="",
            weakest="",
            message="Пройдите оценку навыков, чтобы увидеть прогресс.",
        )

    latest = history[0]
    prev = history[1] if len(history) > 1 else None

    if _is_new_format(latest):
        items = []
        latest_scores = {}
        prev_scores = {}
        for key in SCALE_KEYS:
            skill = _scale_results(latest).get(key)
            score = skill_to_score(key, skill)
            latest_scores[key] = score
            delta = None
            if prev and _is_new_format(prev):
                prev_skill = _scale_results(prev).get(key)
                prev_score = skill_to_score(key, prev_skill)
                prev_scores[key] = prev_score
                delta = score - prev_score
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            items.append(
                ProgressItem(
                    subscale=key,
                    name=SCALE_NAMES[key],
                    score=score,
                    bar=bar,
                    delta=delta,
                    skill=skill,
                )
            )
        strongest_key = max(latest_scores, key=latest_scores.get)
        weakest_key = min(latest_scores, key=latest_scores.get)
        return ProgressResponse(
            baby_name=user.baby_name,
            last_test_date=latest.date.strftime("%d.%m.%Y %H:%M"),
            items=items,
            strongest=f"{SCALE_NAMES[strongest_key]} ({latest_scores[strongest_key]}%)",
            weakest=f"{SCALE_NAMES[weakest_key]} ({latest_scores[weakest_key]}%)",
        )

    scores = {
        "A": latest.score_a,
        "B": latest.score_b,
        "C": latest.score_c,
        "D": latest.score_d,
        "E": latest.score_e,
    }
    prev_scores = None
    if prev:
        prev_scores = {
            "A": prev.score_a,
            "B": prev.score_b,
            "C": prev.score_c,
            "D": prev.score_d,
            "E": prev.score_e,
        }

    items = []
    for key in ("A", "B", "C", "D", "E"):
        delta = None
        if prev_scores is not None:
            delta = scores[key] - prev_scores[key]
        bar = "█" * (scores[key] // 10) + "░" * (10 - scores[key] // 10)
        items.append(
            ProgressItem(
                subscale=key,
                name=SUBSCALE_NAMES[key],
                score=scores[key],
                bar=bar,
                delta=delta,
            )
        )

    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)

    return ProgressResponse(
        baby_name=user.baby_name,
        last_test_date=latest.date.strftime("%d.%m.%Y %H:%M"),
        items=items,
        strongest=f"{SUBSCALE_NAMES[strongest]} ({scores[strongest]}%)",
        weakest=f"{SUBSCALE_NAMES[weakest]} ({scores[weakest]}%)",
    )
