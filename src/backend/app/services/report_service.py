"""报告组装：区间/片段/来源/免责声明/全文/指标/章节/来源明细（AC-05/08/09）。"""

import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import conflict, not_found
from app.repositories import check_result_repo, check_task_repo, plan_repo
from app.schemas.report import (
    ChapterOut,
    MetricsOut,
    ReportOut,
    SegmentOut,
    SourceDetailOut,
    SourceOut,
)


def _load_full_text(task_id: int) -> str:
    """读取任务文档全文（原文落盘于 storage/uploads/{task_id}.txt）。"""
    path = os.path.join(settings.storage_dir, "uploads", f"{task_id}.txt")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""


def _build_source_detail(seg: dict) -> list[SourceDetailOut]:
    """从片段/引擎 sources 组装来源明细；缺字段置 null。"""
    return [
        SourceDetailOut(
            title=None,
            author=None,
            source=seg.get("matched_source"),
            similarity=float(seg.get("similarity", 0.0)),
            is_cited=seg.get("highlight_type") == "cite",
            year=None,
        )
    ]


async def get_report(db: AsyncSession, user_id: int, task_id: int) -> ReportOut:
    task = await check_task_repo.get_by_id(db, task_id)
    if not task or task.user_id != user_id:
        raise not_found("任务不存在或无权访问")
    if task.status != "succeeded":
        raise conflict("任务未完成，报告尚不可用")
    result = await check_result_repo.get_by_task_id(db, task.id)
    if not result:
        raise conflict("报告数据缺失")

    raw_segments = [
        seg
        for seg in (result.segments_json or [])
        if seg.get("end_offset", 0) > seg.get("start_offset", 0)
    ]
    segments = [
        SegmentOut(
            start_offset=int(seg["start_offset"]),
            end_offset=int(seg["end_offset"]),
            highlight_type=seg["highlight_type"],
            matched_source=seg.get("matched_source", ""),
            similarity=float(seg.get("similarity", 0.0)),
            source_detail=_build_source_detail(seg),
        )
        for seg in raw_segments
    ]
    # 来源统计（从片段聚合）
    source_counter: dict[str, int] = {}
    for seg in segments:
        source_counter[seg.matched_source] = source_counter.get(seg.matched_source, 0) + 1
    sources = [SourceOut(source=k, count=v) for k, v in source_counter.items()]

    # 全文 + 指标 + 章节（与引擎同一套函数，防口径漂移）
    full_text = _load_full_text(task.id)
    metrics_out: MetricsOut | None = None
    chapters_out: list[ChapterOut] = []
    if full_text:
        from engine.scoring.metrics import compute_chapters, compute_metrics

        metrics = compute_metrics(raw_segments, len(full_text))
        metrics_out = MetricsOut(**metrics)
        chapters_out = [ChapterOut(**c) for c in compute_chapters(full_text, raw_segments)]

    return ReportOut(
        task_id=task.id,
        plan_code=task.plan_code,
        est_median=float(result.est_median),
        est_low=float(result.est_low),
        est_high=float(result.est_high),
        confidence=float(result.confidence),
        segments=segments,
        sources=sources,
        full_text=full_text,
        metrics=metrics_out,
        chapters=chapters_out,
        created_at=result.created_at,
    )


def render_html(report: ReportOut) -> str:
    """生成 HTML 报告（免责声明常驻，AC-09）。"""
    seg_blocks = []
    for seg in report.segments[:200]:
        color = {"high": "#DC2626", "mid": "#EA580C", "cite": "#B45309"}.get(seg.highlight_type, "#6B7280")
        seg_blocks.append(
            f"<li>{seg.matched_source}（{seg.similarity:.1f}%）[{seg.start_offset}-{seg.end_offset}] "
            f"<span style='color:{color};'>类型:{seg.highlight_type}</span></li>"
        )
    seg_html = "\n".join(seg_blocks) or "<li>无命中片段</li>"
    sources_html = "\n".join(f"<li>{s.source} x {s.count}</li>" for s in report.sources) or "<li>无</li>"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>预查重报告 #{report.task_id}</title>
<style>
body {{ font-family: sans-serif; margin: 40px; color: #1F2937; }}
h1 {{ color: #0D9488; }}
.card {{ border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; margin: 16px 0; }}
.disclaimer {{ background: #F0FDFA; padding: 12px; border-radius: 8px; margin-top: 24px; }}
</style>
</head>
<body>
<h1>预查重报告</h1>
<div class="card">
<p><strong>任务 ID:</strong> {report.task_id}</p>
<p><strong>方案:</strong> {report.plan_code}</p>
<p><strong>预估中值:</strong> {report.est_median:.1f}%</p>
<p><strong>预估区间:</strong> {report.est_low:.1f}% - {report.est_high:.1f}%</p>
<p><strong>置信度:</strong> {report.confidence:.1f}%</p>
</div>
<div class="card"><h2>相似片段</h2><ul>{seg_html}</ul></div>
<div class="card"><h2>来源统计</h2><ul>{sources_html}</ul></div>
<div class="disclaimer"><strong>{report.disclaimer}</strong></div>
</body>
</html>"""


def save_html(report: ReportOut) -> str:
    """落盘 HTML 报告，返回路径。"""
    os.makedirs(settings.report_dir, exist_ok=True)
    path = os.path.join(settings.report_dir, f"report_{report.task_id}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_html(report))
    return path


def render_pdf(report: ReportOut) -> bytes:  # pragma: no cover
    """生成 PDF（依赖 reportlab，未安装时抛错，前端可回退 HTML）。"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
    except ImportError as exc:
        raise RuntimeError("PDF 导出需要 reportlab，请安装") from exc

    from io import BytesIO

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, f"Pre-SPC Check Report #{report.task_id}")
    y -= 10 * mm
    c.setFont("Helvetica", 11)
    lines = [
        f"Plan: {report.plan_code}",
        f"Est. median: {report.est_median:.1f}%",
        f"Est. range: {report.est_low:.1f}% - {report.est_high:.1f}%",
        f"Confidence: {report.confidence:.1f}%",
        f"Segments: {len(report.segments)}",
        f"{report.disclaimer}",
    ]
    for line in lines:
        c.drawString(20 * mm, y, line)
        y -= 7 * mm
    c.save()
    return buf.getvalue()
