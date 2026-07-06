from pydantic import BaseModel


class CreatePlanPaymentResponse(BaseModel):
    payment_id: str
    confirmation_url: str
    amount_rub: int
    status: str


class PlanPaymentStatusResponse(BaseModel):
    payment_id: str
    status: str
    paid: bool
    can_download: bool
    amount_rub: int
