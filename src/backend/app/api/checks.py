"""查重任务端点：创建/历史/详情/报告/导出/再检测。"""

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse, Response

from app.api.deps import CurrentUser, DbDep
from app.core.exceptions import ApiError, CODE_INTERNAL, bad_request
from app.schemas import ok
from app.schemas.report import ReportOut
from app.services import check_service, report_service

router = APIRouter(prefix="/api/v1/checks", tags=["checks"])


@router.post("", status_code=202)
async def create_check(
    db: DbDep,
    user: CurrentUser,
    file: UploadFile = File(...),
    plan_code: str = Form(...),
) -> dict:
    content = await file.read()
    summary = await check_service.create_check(db, user, file.filename or "", len(content), content, plan_code)
    return ok({"task_id": summary.task_id, "status": summary.status})


@router.get("")
async def list_checks(
    db: DbDep,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    items, total = await check_service.list_checks(db, user.id, page, limit)
    return ok(
        {
            "items": [s.model_dump(mode="json") for s in items],
            "total": total,
            "page": page,
            "limit": limit,
            "hasMore": page * limit < total,
        }
    )


@router.get("/{task_id}")
async def get_check(db: DbDep, user: CurrentUser, task_id: int) -> dict:
    detail = await check_service.get_check_detail(db, user.id, task_id)
    return ok(detail.model_dump(mode="json"))


@router.get("/{task_id}/report")
async def get_report(db: DbDep, user: CurrentUser, task_id: int) -> dict:
    report = await report_service.get_report(db, user.id, task_id)
    return ok(ReportOut.model_validate(report).model_dump(mode="json"))


@router.get("/{task_id}/export")
async def export_report(
    db: DbDep,
    user: CurrentUser,
    task_id: int,
    format: str = Query(..., pattern="^(pdf|html)$"),
) -> Response:
    report = await report_service.get_report(db, user.id, task_id)
    if format == "html":
        html = report_service.render_html(report)
        return HTMLResponse(content=html)
    try:
        pdf_bytes = report_service.render_pdf(report)
    except RuntimeError as exc:
        # reportlab 未安装：服务器能力缺失，返回 500，前端回退 HTML 导出
        raise ApiError(500, CODE_INTERNAL, str(exc)) from exc
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.pdf"},
    )


@router.post("/{task_id}/recheck", status_code=202)
async def recheck(db: DbDep, user: CurrentUser, task_id: int, body: dict) -> dict:
    plan_code = (body or {}).get("plan_code", "")
    if not plan_code:
        raise bad_request("plan_code 不能为空")
    summary = await check_service.recheck(db, user, task_id, plan_code)
    return ok({"task_id": summary.task_id, "status": summary.status})
