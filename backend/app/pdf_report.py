"""Generación del PDF de detalle de transferencias del día con ReportLab."""

from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import Transfer


def build_pdf(transfers: list[Transfer], date_str: str, group_name: str | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    elems = []

    title = f"Informe de transferencias — {date_str}"
    if group_name:
        title += f" — {group_name}"
    elems.append(Paragraph(title, styles["Title"]))
    elems.append(Paragraph(
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]
    ))
    elems.append(Spacer(1, 0.5 * cm))

    header = ["#", "Nombre", "Referencia", "Cuenta", "Banco", "Fecha", "Valor"]
    rows = [header]
    total = 0.0
    for i, t in enumerate(transfers, 1):
        amount = t.amount or 0.0
        total += amount
        rows.append([
            str(i),
            (t.sender_name or "-")[:24],
            (t.reference or "-")[:16],
            (t.account or "-")[:16],
            (t.bank or "-")[:18],
            (t.transfer_datetime or "-")[:16],
            f"${amount:,.2f}",
        ])
    rows.append(["", "", "", "", "", "TOTAL", f"${total:,.2f}"])

    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6feb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -2), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f2f6ff")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dde8ff")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(table)
    elems.append(Spacer(1, 0.6 * cm))
    elems.append(Paragraph(
        f"<b>Total vendido por transferencias: ${total:,.2f}</b> "
        f"({len(transfers)} transferencias)", styles["Heading3"]
    ))

    doc.build(elems)
    return buf.getvalue()
