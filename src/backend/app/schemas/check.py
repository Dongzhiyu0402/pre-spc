"""查重任务/方案模型。"""

from datetime import datetime

from pydantic import BaseModel


class PlanOut(BaseModel):
    code: str
    name: str
    type: str
    price_info: dict
    enabled: bool

    model_config = {"from_attributes": True}


class CheckTaskSummary(BaseModel):
    task_id: int
    status: str
    progress: int | None = None
    plan_code: str | None = None
    file_name: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CheckResultSummary(BaseModel):
    est_median: float
    est_low: float
    est_high: float
    confidence: float


class CheckTaskDetail(CheckTaskSummary):
    error: str | None = None
    result: CheckResultSummary | None = None


class RecheckRequest(BaseModel):
    plan_code: str
