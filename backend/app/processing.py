"""Pipeline: imagen -> OCR -> parser (reglas o híbrido) -> persistencia."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from . import ocr, parser
from .config import settings
from .llm import parse_with_ollama
from .models import Group, Transfer

LOW_OCR_CONF = 45.0  # umbral de confianza bajo => pendiente de revisión


def _local_date() -> str:
    return datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")


def _dedup_key(image_bytes: bytes, reference: str | None) -> str:
    if reference:
        return hashlib.sha256(f"ref:{reference}".encode()).hexdigest()
    return hashlib.sha256(image_bytes).hexdigest()


def save_image(image_bytes: bytes) -> str:
    fname = f"{uuid.uuid4().hex}.jpg"
    path = settings.media_path / fname
    path.write_bytes(image_bytes)
    return str(path)


async def process_image(
    db: Session,
    image_bytes: bytes,
    group: Group | None,
    instance_id: int | None,
    sender_jid: str | None = None,
) -> Transfer | None:
    """Procesa una imagen y guarda la transferencia. Devuelve None si es duplicado."""
    text = ocr.image_to_text(image_bytes)
    conf = ocr.ocr_confidence(image_bytes)

    result = parser.parse_transfer(text)
    method = "rules"

    # Modo híbrido: refinar con modelo local si faltan campos clave
    if settings.parse_mode == "hybrid" and (result.missing or not result.is_transfer):
        llm_data = await parse_with_ollama(text)
        if llm_data:
            method = "hybrid"
            for k in ("sender_name", "reference", "account", "bank", "transfer_datetime"):
                if not getattr(result, k) and llm_data.get(k):
                    setattr(result, k, llm_data[k])
            if result.amount is None and llm_data.get("amount") is not None:
                try:
                    result.amount = round(float(llm_data["amount"]), 2)
                except (ValueError, TypeError):
                    pass
            if llm_data.get("is_transfer"):
                result.is_transfer = True
            result.missing = [
                f for f in ("amount", "reference", "bank", "transfer_datetime")
                if not getattr(result, f)
            ]

    # ¿Es realmente una transferencia?
    if not result.is_transfer and result.amount is None:
        # Imagen que no parece transferencia (meme/foto): marcar inválida
        status = "invalid"
        review_reason = "La imagen no parece un comprobante de transferencia."
    elif conf < LOW_OCR_CONF:
        status = "pending_review"
        review_reason = f"OCR de baja calidad (confianza {conf:.0f}%)."
    elif result.missing:
        status = "pending_review"
        review_reason = "Campos no extraídos: " + ", ".join(result.missing)
    else:
        status = "processed"
        review_reason = None

    dedup = _dedup_key(image_bytes, result.reference)
    existing = db.query(Transfer).filter(Transfer.dedup_key == dedup).first()
    if existing:
        return None  # duplicado

    image_path = save_image(image_bytes)

    transfer = Transfer(
        group_id=group.id if group else None,
        instance_id=instance_id,
        sender_name=result.sender_name,
        reference=result.reference,
        account=result.account,
        bank=result.bank,
        transfer_datetime=result.transfer_datetime,
        amount=result.amount,
        raw_text=text,
        image_path=image_path,
        status=status,
        review_reason=review_reason,
        parse_method=method,
        dedup_key=dedup,
        sender_jid=sender_jid,
        local_date=_local_date(),
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer
