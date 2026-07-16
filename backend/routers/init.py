from fastapi import APIRouter, Depends

from backend.deps import get_current_user, get_optional_user
from backend.db import User
from backend.schemas.init import InitResponse
from backend.services.profile import is_profile_complete, profile_from_user
from backend.utils.name_auth import build_display_name

router = APIRouter(prefix="/api", tags=["init"])


def _user_init_response(user: User) -> InitResponse:
    profile = profile_from_user(user)
    return InitResponse(
        authenticated=True,
        display_name=build_display_name(user.first_name, user.patronymic, user.last_name),
        login_code=user.login_code or None,
        email=user.email,
        registered=is_profile_complete(user),
        baby_name=profile.baby_name if profile else None,
        baby_birthday=profile.baby_birthday if profile else None,
        age_label=profile.age_label if profile else None,
        age_months=profile.age_months if profile else None,
    )


@router.get("/init", response_model=InitResponse)
async def init_app(user: User | None = Depends(get_optional_user)) -> InitResponse:
    """Замена /start: состояние сессии и профиля."""
    if user is None:
        return InitResponse(authenticated=False)

    return _user_init_response(user)


@router.get("/me", response_model=InitResponse)
async def me(user: User = Depends(get_current_user)) -> InitResponse:
    return _user_init_response(user)
