import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..crypto import decrypt, encrypt
from ..database import get_db
from ..evolution import EvolutionClient
from ..models import Group, Instance
from ..schemas import InstanceIn, InstanceOut
from ..security import get_current_user

log = logging.getLogger("instances")
router = APIRouter(prefix="/api/instances", tags=["instances"])


def _to_out(inst: Instance) -> InstanceOut:
    return InstanceOut(
        id=inst.id,
        name=inst.name,
        instance_name=inst.instance_name,
        base_url=decrypt(inst.base_url_enc),
        connected=inst.connected,
        status=inst.status,
    )


def _client(inst: Instance) -> EvolutionClient:
    return EvolutionClient(
        decrypt(inst.base_url_enc), decrypt(inst.api_key_enc), inst.instance_name
    )


@router.get("", response_model=list[InstanceOut])
def list_instances(db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    return [_to_out(i) for i in db.query(Instance).all()]


@router.post("", response_model=InstanceOut)
async def create_instance(
    data: InstanceIn, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    inst = Instance(
        name=data.name,
        instance_name=data.instance_name,
        base_url_enc=encrypt(data.base_url),
        api_key_enc=encrypt(data.api_key),
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    # Intentar configurar el webhook automáticamente
    await _try_set_webhook(inst)
    db.commit()
    return _to_out(inst)


@router.put("/{instance_id}", response_model=InstanceOut)
async def update_instance(
    instance_id: int,
    data: InstanceIn,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    inst = db.get(Instance, instance_id)
    if not inst:
        raise HTTPException(404, "Instancia no encontrada")
    inst.name = data.name
    inst.instance_name = data.instance_name
    inst.base_url_enc = encrypt(data.base_url)
    inst.api_key_enc = encrypt(data.api_key)
    db.commit()
    await _try_set_webhook(inst)
    db.commit()
    return _to_out(inst)


@router.delete("/{instance_id}")
def delete_instance(
    instance_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    inst = db.get(Instance, instance_id)
    if not inst:
        raise HTTPException(404, "Instancia no encontrada")
    db.delete(inst)
    db.commit()
    return {"ok": True}


async def _try_set_webhook(inst: Instance):
    webhook_url = f"{settings.public_base_url.rstrip('/')}/api/webhook/{inst.id}"
    try:
        await _client(inst).set_webhook(webhook_url)
        inst.status = "webhook_set"
    except Exception as e:  # noqa: BLE001
        log.warning("No se pudo configurar webhook: %s", e)
        inst.status = "webhook_error"


@router.post("/{instance_id}/test")
async def test_connection(
    instance_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    inst = db.get(Instance, instance_id)
    if not inst:
        raise HTTPException(404, "Instancia no encontrada")
    try:
        state = await _client(inst).connection_state()
        raw = state.get("instance", state)
        status_str = raw.get("state", raw.get("status", "unknown"))
        inst.connected = status_str in ("open", "connected")
        inst.status = status_str
        db.commit()
        return {"ok": True, "state": status_str, "connected": inst.connected}
    except Exception as e:  # noqa: BLE001
        inst.connected = False
        inst.status = "error"
        db.commit()
        raise HTTPException(502, f"Error de conexión: {e}")


@router.get("/{instance_id}/qr")
async def get_qr(
    instance_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    inst = db.get(Instance, instance_id)
    if not inst:
        raise HTTPException(404, "Instancia no encontrada")
    try:
        data = await _client(inst).connect()
        # Evolution devuelve {base64, code, pairingCode} o estado si ya está conectado
        qr = data.get("base64") or (data.get("qrcode") or {}).get("base64")
        code = data.get("code") or (data.get("qrcode") or {}).get("code")
        state = data.get("instance", {}).get("state") if isinstance(data.get("instance"), dict) else None
        if state in ("open", "connected"):
            inst.connected = True
            inst.status = state
            db.commit()
        return {"qr": qr, "code": code, "state": state}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Error obteniendo QR: {e}")


@router.post("/{instance_id}/sync-groups")
async def sync_groups(
    instance_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    inst = db.get(Instance, instance_id)
    if not inst:
        raise HTTPException(404, "Instancia no encontrada")
    try:
        groups = await _client(inst).fetch_groups()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Error obteniendo grupos: {e}")

    count = 0
    for g in groups:
        jid = g.get("id") or g.get("jid")
        name = g.get("subject") or g.get("name") or ""
        if not jid:
            continue
        existing = (
            db.query(Group)
            .filter(Group.instance_id == inst.id, Group.group_jid == jid)
            .first()
        )
        if existing:
            existing.name = name or existing.name
        else:
            db.add(Group(instance_id=inst.id, group_jid=jid, name=name, active=False))
            count += 1
    db.commit()
    return {"ok": True, "new_groups": count, "total": len(groups)}
