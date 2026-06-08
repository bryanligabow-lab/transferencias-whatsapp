"""Recibe los webhooks de Evolution API (evento MESSAGES_UPSERT).

Detecta mensajes con imagen dentro de los grupos monitoreados activos,
descarga la imagen y la procesa con el pipeline OCR local.
"""

from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, BackgroundTasks, Request

from ..crypto import decrypt
from ..database import SessionLocal
from ..evolution import EvolutionClient
from ..models import Group, Instance
from ..processing import process_image

log = logging.getLogger("webhook")
router = APIRouter(prefix="/api/webhook", tags=["webhook"])


def _extract_messages(payload: dict) -> list[dict]:
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _is_image(msg: dict) -> bool:
    mtype = msg.get("messageType") or ""
    message = msg.get("message") or {}
    return mtype == "imageMessage" or "imageMessage" in message


def _remote_jid(msg: dict) -> str | None:
    return (msg.get("key") or {}).get("remoteJid")


def _extract_base64(msg: dict) -> str | None:
    # Evolution puede incluir el base64 directamente cuando webhookBase64=true
    message = msg.get("message") or {}
    return (
        msg.get("base64")
        or message.get("base64")
        or (message.get("imageMessage") or {}).get("base64")
    )


@router.post("/{instance_id}")
async def receive_webhook(
    instance_id: int,
    request: Request,
    background: BackgroundTasks,
):
    payload = await request.json()
    background.add_task(_handle_payload, instance_id, payload)
    return {"received": True}


async def _handle_payload(instance_id: int, payload: dict):
    db = SessionLocal()
    try:
        inst = db.get(Instance, instance_id)
        if not inst:
            return
        client = EvolutionClient(
            decrypt(inst.base_url_enc), decrypt(inst.api_key_enc), inst.instance_name
        )
        for msg in _extract_messages(payload):
            if (msg.get("key") or {}).get("fromMe"):
                continue
            if not _is_image(msg):
                continue
            jid = _remote_jid(msg)
            if not jid or not jid.endswith("@g.us"):
                continue  # solo grupos
            group = (
                db.query(Group)
                .filter(
                    Group.instance_id == instance_id,
                    Group.group_jid == jid,
                    Group.active.is_(True),
                )
                .first()
            )
            if not group:
                continue  # grupo no monitoreado

            image_bytes = await _get_image_bytes(client, msg)
            if not image_bytes:
                log.warning("No se pudo obtener la imagen del mensaje en %s", jid)
                continue

            sender = (msg.get("key") or {}).get("participant")
            try:
                t = await process_image(db, image_bytes, group, instance_id, sender)
                if t:
                    log.info(
                        "Transferencia %s registrada (grupo=%s, estado=%s, monto=%s)",
                        t.id, group.name, t.status, t.amount,
                    )
            except Exception as e:  # noqa: BLE001
                log.exception("Error procesando imagen: %s", e)
    finally:
        db.close()


async def _get_image_bytes(client: EvolutionClient, msg: dict) -> bytes | None:
    b64 = _extract_base64(msg)
    if not b64:
        try:
            b64 = await client.get_media_base64(msg)
        except Exception as e:  # noqa: BLE001
            log.warning("getBase64FromMediaMessage falló: %s", e)
            return None
    if not b64:
        return None
    try:
        return base64.b64decode(b64)
    except Exception:  # noqa: BLE001
        return None
