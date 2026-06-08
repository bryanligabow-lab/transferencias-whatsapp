"""Generación y envío del informe diario (total + PDF) por WhatsApp y email."""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from . import pdf_report
from .config import settings
from .crypto import decrypt
from .evolution import EvolutionClient
from .mailer import send_email_with_pdf
from .models import Group, Instance, Transfer
from .store import get_config

log = logging.getLogger("reports")


def transfers_for_date(
    db: Session, date_str: str, group_id: int | None = None
) -> list[Transfer]:
    q = db.query(Transfer).filter(
        Transfer.local_date == date_str,
        Transfer.status.in_(["processed", "pending_review"]),
    )
    if group_id is not None:
        q = q.filter(Transfer.group_id == group_id)
    return q.order_by(Transfer.received_at).all()


def totals_for_date(db: Session, date_str: str) -> dict:
    transfers = transfers_for_date(db, date_str)
    total = sum(t.amount or 0 for t in transfers)
    by_group: dict[int | None, dict] = {}
    for t in transfers:
        g = by_group.setdefault(t.group_id, {"group_id": t.group_id, "total": 0.0, "count": 0})
        g["total"] += t.amount or 0
        g["count"] += 1
    return {
        "date": date_str,
        "total": round(total, 2),
        "count": len(transfers),
        "by_group": list(by_group.values()),
    }


async def _send_whatsapp(db: Session, phone: str, pdf_bytes: bytes, caption: str, filename: str):
    """Envía el PDF por WhatsApp usando la primera instancia conectada."""
    inst = (
        db.query(Instance)
        .filter(Instance.connected.is_(True))
        .first()
        or db.query(Instance).first()
    )
    if not inst:
        log.warning("No hay instancia de Evolution API para enviar el informe.")
        return
    client = EvolutionClient(
        decrypt(inst.base_url_enc), decrypt(inst.api_key_enc), inst.instance_name
    )
    b64 = base64.b64encode(pdf_bytes).decode()
    await client.send_media(phone, b64, filename, caption)


async def generate_and_send_report(
    db: Session, date_str: str | None = None, group: Group | None = None
) -> dict:
    if date_str is None:
        date_str = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")

    cfg = get_config(db)
    group_id = group.id if group else None
    phone = (group.report_phone if group else None) or cfg.get("report_phone", "")
    email = (group.report_email if group else None) or cfg.get("report_email", "")

    transfers = transfers_for_date(db, date_str, group_id)
    total = round(sum(t.amount or 0 for t in transfers), 2)
    pdf_bytes = pdf_report.build_pdf(transfers, date_str, group.name if group else None)
    filename = f"transferencias_{date_str}.pdf"
    caption = (
        f"Informe de transferencias {date_str}\n"
        f"Total vendido: ${total:,.2f}\n"
        f"Transferencias: {len(transfers)}"
    )

    sent = {"whatsapp": False, "email": False, "total": total, "count": len(transfers)}

    if phone:
        try:
            await _send_whatsapp(db, phone, pdf_bytes, caption, filename)
            sent["whatsapp"] = True
        except Exception as e:  # noqa: BLE001
            log.exception("Error enviando WhatsApp: %s", e)

    if email:
        try:
            send_email_with_pdf(
                email, f"Informe transferencias {date_str}", caption, pdf_bytes, filename
            )
            sent["email"] = True
        except Exception as e:  # noqa: BLE001
            log.exception("Error enviando email: %s", e)

    return sent


async def run_daily_reports(db: Session):
    """Ejecutado por el scheduler: informe global + informes por grupo configurado."""
    date_str = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")
    await generate_and_send_report(db, date_str)
    # Informes específicos por grupo que tengan su propia config
    groups = (
        db.query(Group)
        .filter(Group.active.is_(True))
        .filter((Group.report_phone.isnot(None)) | (Group.report_email.isnot(None)))
        .all()
    )
    for g in groups:
        await generate_and_send_report(db, date_str, group=g)
