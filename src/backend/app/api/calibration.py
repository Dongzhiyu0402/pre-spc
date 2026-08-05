"""校准端点：回传报告（AC-14）、校准状态（AC-15）。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import CurrentUser, DbDep
from app.schemas import ok
from app.schemas.report import CalibrationStatusOut
from app.services import calibration_service

router = APIRouter(prefix="/api/v1/calibration", tags=["calibration"])


@router.post("/reports", status_code=201)
async def submit_report(
    db: DbDep,
    user: CurrentUser,
    file: UploadFile = File(...),
    platform: str = Form(...),
    real_rate: float = Form(...),
    task_id: int = Form(...),
) -> dict:
    content = await file.read()
    sample_id = await calibration_service.submit_report(
        db, user, file.filename or "", content, platform, real_rate, task_id
    )
    return ok({"sample_id": sample_id, "status": "pending_validation"})


@router.get("/status")
async def calibration_status(db: DbDep, user: CurrentUser) -> dict:
    status = await calibration_service.get_status(db)
    return ok(CalibrationStatusOut.model_validate(status).model_dump(mode="json"))
