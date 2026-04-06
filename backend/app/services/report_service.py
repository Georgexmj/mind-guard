from datetime import date
from io import BytesIO
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from app.models.assessment import AssessmentResult, AssessmentSession


def _safe_get_shap(result: AssessmentResult, key: str, default: Any = None) -> Any:
    shap = result.shap_values if isinstance(result.shap_values, dict) else {}
    return shap.get(key, default)


def _draw_line(c: canvas.Canvas, y: float, text: str, size: int = 11) -> float:
    c.setFont("STSong-Light", size)
    c.drawString(16 * mm, y, text)
    return y - 7 * mm


def _draw_qr(c: canvas.Canvas, x: float, y: float, text: str, size_mm: int = 24) -> None:
    qrw = qr.QrCodeWidget(text)
    bounds = qrw.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    side = size_mm * mm
    drawing = Drawing(side, side, transform=[side / width, 0, 0, side / height, 0, 0])
    drawing.add(qrw)
    renderPDF.draw(drawing, c, x, y)


def build_doctor_report_pdf(
    session: AssessmentSession,
    result: AssessmentResult,
    recommendations: List[Dict[str, Any]],
    next_reassessment_date: date,
    hospital_name: str = "MindGuard 社区认知门诊",
    doctor_name: str = "-",
    signature_text: str = "电子签名有效",
    verify_token: str = "",
) -> bytes:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 18 * mm
    y = _draw_line(c, y, f"\u3010{hospital_name} | MindGuard 医生标准化报告\u3011", 14)
    y = _draw_line(c, y, f"\u4f1a\u8bddID: {session.id}    \u8001\u4ebaID: {session.user_id}")
    y = _draw_line(c, y, f"\u8bc4\u4f30\u65f6\u95f4: {result.created_at.strftime('%Y-%m-%d %H:%M') if result.created_at else '-'}")
    y = _draw_line(c, y, f"\u98ce\u9669\u7b49\u7ea7: {result.risk_level.value if hasattr(result.risk_level, 'value') else result.risk_level}")
    y = _draw_line(c, y, f"MMSE: {result.mmse_score if result.mmse_score is not None else '-'} / 30")
    y = _draw_line(
        c,
        y,
        f"MoCA(\u6821\u6b63\u540e): {_safe_get_shap(result, 'moca_score_corrected', '-')}",
    )

    y -= 2 * mm
    y = _draw_line(c, y, "\u91cf\u8868\u5206\u9879\uff08MMSE/MoCA\uff09", 12)
    mmse_sub = _safe_get_shap(result, "mmse_subscores", {}) or {}
    moca_sub = _safe_get_shap(result, "moca_subscores", {}) or {}
    if not mmse_sub and not moca_sub:
        y = _draw_line(c, y, "- \u672a\u83b7\u53d6\u5230\u5206\u9879\u6570\u636e")
    else:
        if mmse_sub:
            y = _draw_line(c, y, f"- MMSE: {mmse_sub}")
        if moca_sub:
            y = _draw_line(c, y, f"- MoCA: {moca_sub}")

    y -= 2 * mm
    y = _draw_line(c, y, "\u5e72\u9884\u5efa\u8bae Top-5", 12)
    if recommendations:
        for item in recommendations[:5]:
            y = _draw_line(
                c,
                y,
                f"{item.get('rank', '-')}. {item.get('title', '-')}"
                f" | {item.get('frequency', '-')}"
                f" | {item.get('duration_minutes', '-')}min",
            )
            if y < 24 * mm:
                c.showPage()
                pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
                y = height - 18 * mm
    else:
        y = _draw_line(c, y, "- \u6682\u65e0\u53ef\u7528\u5e72\u9884\u5efa\u8bae")

    y -= 2 * mm
    y = _draw_line(c, y, "\u968f\u8bbf\u5efa\u8bae", 12)
    y = _draw_line(c, y, f"\u5efa\u8bae\u4e0b\u6b21\u590d\u8bc4\u65f6\u95f4: {next_reassessment_date.isoformat()}")
    y = _draw_line(
        c,
        y,
        "\u8bf7\u7ed3\u5408\u4e34\u5e8a\u75c7\u72b6\u548c\u65e5\u5e38\u8868\u73b0\uff0c"
        "\u6309\u65f6\u5b8c\u6210\u5e72\u9884\u6253\u5361\u4e0e\u590d\u8bc4\u3002",
    )

    y -= 3 * mm
    y = _draw_line(c, y, f"责任医生: {doctor_name}")
    y = _draw_line(c, y, f"签名状态: {signature_text}")
    verify_text = verify_token or f"mindguard-session-{session.id}"
    _draw_qr(c, width - 42 * mm, 12 * mm, verify_text, size_mm=24)
    c.setFont("STSong-Light", 8)
    c.drawString(width - 42 * mm, 9 * mm, "扫码验真")

    c.setFont("STSong-Light", 9)
    c.drawString(16 * mm, 10 * mm, "MindGuard - \u672c\u62a5\u544a\u4ec5\u7528\u4e8e\u8f85\u52a9\u7b5b\u67e5\u548c\u968f\u8bbf\u3002")
    c.save()
    return buf.getvalue()
