from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_current_user
from backend.db import User
from backend.schemas.profile import ProfileRequest, ProfileResponse
from backend.services.profile import profile_from_user, save_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user)) -> ProfileResponse:
    profile = profile_from_user(user)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль ребёнка не заполнен")
    return profile


@router.post("", response_model=ProfileResponse)
@router.put("", response_model=ProfileResponse)
async def upsert_profile(
    body: ProfileRequest, user: User = Depends(get_current_user)
) -> ProfileResponse:
    try:
        return await save_profile(user.id, body.baby_name, body.baby_birthday)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
