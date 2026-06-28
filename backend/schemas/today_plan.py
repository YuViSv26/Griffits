from pydantic import BaseModel


class ExpectedSkillBlock(BaseModel):
    scale: str
    scale_name: str
    skills: list[str]


class GameSuggestion(BaseModel):
    title: str
    develops: str
    description: str
    safety_rules: str


class PracticeTip(BaseModel):
    icon: str
    label: str
    value: str


class TodayPlanResponse(BaseModel):
    baby_name: str
    age_label: str
    age_months: int
    focus_scale: str
    focus_scale_name: str
    focus_subscale_code: str
    expected_skills: list[ExpectedSkillBlock]
    attention_points: list[str]
    games: list[GameSuggestion]
    practice_tips: list[PracticeTip]
    important_reminder: str
    has_assessment: bool
    weakest_scale_name: str | None = None
    weakest_score: int | None = None
