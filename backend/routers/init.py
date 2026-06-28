from fastapi import APIRouter, Depends

from backend.deps import get_current_user, get_optional_user
from backend.db import User
from backend.schemas.init import InitResponse
from backend.services.profile import is_profile_complete, profile_from_user

router = APIRouter(prefix="/api", tags=["init"])


@router.get("/init", response_model=InitResponse)
async def init_app(user: User | None = Depends(get_optional_user)) -> InitResponse:
    """Замена /start: состояние сессии и профиля."""
    if user is None:
        return InitResponse(authenticated=False)

    profile = profile_from_user(user)
    return InitResponse(
        authenticated=True,
        email=user.email,
        registered=is_profile_complete(user),
        baby_name=profile.baby_name if profile else None,
        baby_birthday=profile.baby_birthday if profile else None,
        age_label=profile.age_label if profile else None,
        age_months=profile.age_months if profile else None,
    )


@router.get("/me", response_model=InitResponse)
async def me(user: User = Depends(get_current_user)) -> InitResponse:
    profile = profile_from_user(user)
    return InitResponse(
        authenticated=True,
        email=user.email,
        registered=is_profile_complete(user),
        baby_name=profile.baby_name if profile else None,
        baby_birthday=profile.baby_birthday if profile else None,
        age_label=profile.age_label if profile else None,
        age_months=profile.age_months if profile else None,
    )
