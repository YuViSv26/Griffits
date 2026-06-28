from datetime import date

from backend.db import User, update_user_profile
from backend.schemas.profile import ProfileResponse
from backend.utils.age import AgeValidationError, calculate_age, parse_birthday


def is_profile_complete(user: User) -> bool:
    return bool(user.baby_name and user.baby_birthday)


async def save_profile(user_id: int, baby_name: str, birthday_raw: str) -> ProfileResponse:
    try:
        birthday = parse_birthday(birthday_raw)
        age = calculate_age(birthday)
    except AgeValidationError as exc:
        raise ValueError(str(exc)) from exc

    await update_user_profile(user_id, baby_name.strip(), birthday)
    return ProfileResponse(
        baby_name=baby_name.strip(),
        baby_birthday=birthday.isoformat(),
        age_label=age.label,
        age_months=age.total_months,
        warning=age.warning,
    )


def profile_from_user(user: User) -> ProfileResponse | None:
    if not is_profile_complete(user):
        return None
    age = calculate_age(user.baby_birthday)
    return ProfileResponse(
        baby_name=user.baby_name,
        baby_birthday=user.baby_birthday.isoformat(),
        age_label=age.label,
        age_months=age.total_months,
        warning=age.warning,
    )
