from pydantic import BaseModel, Field


class ProfileRequest(BaseModel):
    baby_name: str = Field(min_length=2, max_length=50)
    baby_birthday: str = Field(
        description="Дата в формате YYYY-MM-DD или ДД.ММ.ГГГГ"
    )


class ProfileResponse(BaseModel):
    baby_name: str
    baby_birthday: str
    age_label: str
    age_months: int
    warning: str | None = None
