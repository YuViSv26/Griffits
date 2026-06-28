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
