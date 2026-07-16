from pydantic import BaseModel, Field, field_validator

from backend.utils.name_auth import parse_birth_date


class LoginCodeAuthRequest(BaseModel):
    login_code: str = Field(min_length=6, max_length=6)
    birth_day: int = Field(ge=1, le=31)
    birth_month: int = Field(ge=1, le=12)
    birth_year: int = Field(ge=1920, le=2100)

    @field_validator("login_code")
    @classmethod
    def normalize_login_code(cls, value: str) -> str:
        code = value.strip().upper()
        if len(code) != 6:
            raise ValueError("ФИО должно содержать ровно 6 знаков")
        return code

    def birth_date(self):
        return parse_birth_date(self.birth_day, self.birth_month, self.birth_year)


class RegisterRequest(LoginCodeAuthRequest):
    pass


class LoginRequest(LoginCodeAuthRequest):
    pass


class AuthResponse(BaseModel):
    user_id: int
    display_name: str
    login_code: str
    access_token: str
    token_type: str = "bearer"
