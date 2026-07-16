from pydantic import BaseModel


class InitResponse(BaseModel):
    authenticated: bool
    display_name: str | None = None
    login_code: str | None = None
    email: str | None = None
    registered: bool = False
    baby_name: str | None = None
    baby_birthday: str | None = None
    age_label: str | None = None
    age_months: int | None = None
