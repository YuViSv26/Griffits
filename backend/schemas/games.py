from pydantic import BaseModel


class GameResponse(BaseModel):
    id: int
    title: str
    subscale: str
    subscale_name: str
    age_label: str
    focus_subscale: str
    focus_subscale_name: str
    develops: str
    description: str
    safety_rules: str


class ProgressItem(BaseModel):
    subscale: str
    name: str
    score: int
    bar: str
    delta: int | None = None
    skill: str | None = None


class ProgressResponse(BaseModel):
    baby_name: str
    last_test_date: str | None
    items: list[ProgressItem]
    strongest: str
    weakest: str
    message: str | None = None
