from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: int
    email: str
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    reset_base_url: str | None = None


class ForgotPasswordResponse(BaseModel):
    message: str
    email_sent: bool = False
    reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    password: str = Field(min_length=6, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str
