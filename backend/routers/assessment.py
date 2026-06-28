from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_current_user
from backend.db import User
from backend.schemas.assessment import (
    AssessmentLatestResponse,
    AssessmentResultResponse,
    AssessmentSubmitRequest,
)
from backend.services.assessment import get_latest_assessment_result, submit_assessment
from backend.services.profile import is_profile_complete

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


def _require_profile(user: User) -> None:
    if not is_profile_complete(user):
        raise HTTPException(
            status_code=400,
            detail="Сначала заполните профиль ребёнка",
        )


@router.get("/latest", response_model=AssessmentLatestResponse)
async def assessment_latest(
    user: User = Depends(get_current_user),
) -> AssessmentLatestResponse:
    _require_profile(user)
    result = await get_latest_assessment_result(user)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Сохранённых оценок пока нет. Пройдите тест и нажмите «Сохранить».",
        )
    return result


@router.post("/submit", response_model=AssessmentResultResponse)
async def assessment_submit(
    body: AssessmentSubmitRequest,
    user: User = Depends(get_current_user),
) -> AssessmentResultResponse:
    _require_profile(user)
    try:
        return await submit_assessment(user, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
