from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_current_user
from backend.db import User
from backend.schemas.games import GameResponse, ProgressResponse
from backend.schemas.today_plan import TodayPlanResponse
from backend.services.games import get_progress, get_today_game
from backend.services.today_plan import get_today_plan
from backend.services.profile import is_profile_complete

router = APIRouter(prefix="/api", tags=["games"])


def _require_profile(user: User) -> None:
    if not is_profile_complete(user):
        raise HTTPException(
            status_code=400,
            detail="Сначала заполните профиль ребёнка",
        )


@router.get("/games/today-plan", response_model=TodayPlanResponse)
async def game_today_plan(user: User = Depends(get_current_user)) -> TodayPlanResponse:
    _require_profile(user)
    return await get_today_plan(user)


@router.get("/games/today", response_model=GameResponse)
async def game_today(user: User = Depends(get_current_user)) -> GameResponse:
    _require_profile(user)
    game = await get_today_game(user)
    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Нет игр для текущего возраста",
        )
    return game


@router.get("/progress", response_model=ProgressResponse)
async def progress(user: User = Depends(get_current_user)) -> ProgressResponse:
    _require_profile(user)
    return await get_progress(user)
