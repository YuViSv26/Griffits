from pydantic import BaseModel, Field


class ScaleResultsPayload(BaseModel):
    locomotion: str | None = None
    social: str | None = None
    speech: str | None = None
    eye_hand: str | None = None
    play: str | None = None


class AssessmentSubmitRequest(BaseModel):
    age_months: int = Field(ge=0, le=24, description="Возраст ребёнка в полных месяцах (0–24)")
    results: ScaleResultsPayload


class ScaleResultItem(BaseModel):
    scale: str
    name: str
    skill: str | None
    score: int
    ball: int | None = None
    age_equivalent_months: int | None = None


class GriffithsSummaryResponse(BaseModel):
    chronologic_age_months: int
    total_balls: int
    total_age_equivalent_months: int
    norm_total_min: int
    norm_total_max: int
    scales: list[ScaleResultItem]


class AssessmentResultResponse(BaseModel):
    age_months: int
    scales: list[ScaleResultItem]
    summary: GriffithsSummaryResponse


class AssessmentLatestResponse(AssessmentResultResponse):
    test_date: str
