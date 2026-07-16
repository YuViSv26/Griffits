import re

from backend.data.assessment_scales import (
    SCALE_BALL_BY_TEXT,
    SCALE_KEYS,
    SCALE_NAMES,
    skill_to_score,
)
from backend.data.griffiths_scoring import compute_griffiths_summary
from backend.db import User, get_latest_assessment, save_assessment_v2
from backend.schemas.assessment import (
    AssessmentLatestResponse,
    AssessmentResultResponse,
    AssessmentSubmitRequest,
    GriffithsSummaryResponse,
    ScaleResultItem,
)
from backend.services.games import _is_new_format, _scale_results


def _build_response(
    age_months: int,
    results: dict[str, str | None],
) -> AssessmentResultResponse:
    summary_raw = compute_griffiths_summary(results, age_months)

    scales = []
    for item in summary_raw["scales"]:
        key = item["scale"]
        skill = item["skill"]
        scales.append(
            ScaleResultItem(
                scale=key,
                name=item["name"],
                skill=skill,
                score=skill_to_score(key, skill),
                ball=item["ball"],
                age_equivalent_months=item["age_equivalent_months"],
            )
        )

    norm = summary_raw["norm_total_at_age"]
    summary = GriffithsSummaryResponse(
        chronologic_age_months=summary_raw["chronologic_age_months"],
        total_balls=summary_raw["total_balls"],
        total_age_equivalent_months=summary_raw["total_age_equivalent_months"],
        norm_total_min=norm["min"],
        norm_total_max=norm["max"],
        scales=scales,
    )

    return AssessmentResultResponse(
        age_months=age_months,
        scales=scales,
        summary=summary,
    )


async def submit_assessment(
    user: User, body: AssessmentSubmitRequest
) -> AssessmentResultResponse:
    results = body.results.model_dump()
    await save_assessment_v2(user.id, body.age_months, results)
    return _build_response(body.age_months, results)


async def get_latest_assessment_result(user: User) -> AssessmentLatestResponse | None:
    assessment = await get_latest_assessment(user.id)
    if assessment is None or not _is_new_format(assessment):
        return None

    results = _scale_results(assessment)
    age_months = assessment.child_age_months or 0
    base = _build_response(age_months, results)

    return AssessmentLatestResponse(
        **base.model_dump(),
        test_date=assessment.date.strftime("%d.%m.%Y %H:%M"),
    )


ORGANIZATION_RECIPIENTS: dict[str, str] = {
    "днкц им л м рошаля": "airazrab@mail.ru",
}


def _normalize_organization(name: str) -> str:
    text = name.strip().lower().replace("ё", "е")
    text = re.sub(r"[.,\-—_'\"«»()]", " ", text)
    return " ".join(text.split())


def _resolve_organization_email(organization: str) -> str | None:
    normalized = _normalize_organization(organization)
    if normalized in ORGANIZATION_RECIPIENTS:
        return ORGANIZATION_RECIPIENTS[normalized]
    if "днкц" in normalized and "рошал" in normalized:
        return ORGANIZATION_RECIPIENTS["днкц им л м рошаля"]
    return None


def _format_assessment_email_body(
    baby_name: str,
    age_label: str,
    parent_email: str,
    organization: str,
    test_date: str,
    result: AssessmentLatestResponse,
) -> str:
    norm = result.summary
    norm_range = (
        f"{norm.norm_total_min}–{norm.norm_total_max}"
        if norm.norm_total_min != norm.norm_total_max
        else str(norm.norm_total_min)
    )
    lines = [
        f"Организация: {organization}",
        "",
        f"Ребёнок: {baby_name}",
        f"Возраст: {age_label}",
        f"Дата теста: {test_date}",
        f"Email родителя: {parent_email}",
        "",
        f"Сумма баллов: {norm.total_balls}",
        f"Возрастной эквивалент: {norm.total_age_equivalent_months} мес.",
        f"Норма для возраста: {norm_range}",
        "",
        "Результаты по субшкалам:",
    ]
    for scale in result.scales:
        age_eq = (
            f"{scale.age_equivalent_months} мес."
            if scale.age_equivalent_months
            else "—"
        )
        lines.append(
            f"• {scale.name}: балл {scale.ball or '—'}, "
            f"возр. экв. {age_eq}, навык: {scale.skill or '—'}"
        )
    return "\n".join(lines)


async def send_assessment_to_organization(
    user: User, organization: str
) -> tuple[str, bool]:
    from backend.services.email import send_assessment_results_email, smtp_configured
    from backend.services.profile import profile_from_user

    if not smtp_configured():
        raise ValueError("Почта не настроена на сервере. Обратитесь к администратору.")

    recipient = _resolve_organization_email(organization)
    if not recipient:
        raise ValueError(
            "Организация не найдена. Проверьте название или обратитесь в поддержку."
        )

    result = await get_latest_assessment_result(user)
    if result is None:
        raise ValueError("Сохранённых результатов теста нет.")

    profile = profile_from_user(user)
    if not profile:
        raise ValueError("Сначала заполните профиль ребёнка.")

    body_text = _format_assessment_email_body(
        baby_name=profile.baby_name,
        age_label=profile.age_label,
        parent_email=user.email,
        organization=organization.strip(),
        test_date=result.test_date,
        result=result,
    )

    ok, err = send_assessment_results_email(
        to_email=recipient,
        organization=organization.strip(),
        baby_name=profile.baby_name,
        age_label=profile.age_label,
        parent_email=user.email,
        test_date=result.test_date,
        body_text=body_text,
    )
    if not ok:
        raise ValueError(err or "Не удалось отправить письмо")

    return (
        f"Результат теста отправлен в «{organization.strip()}».",
        True,
    )
