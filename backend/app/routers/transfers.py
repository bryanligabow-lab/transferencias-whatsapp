from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Transfer
from ..reports import totals_for_date
from ..schemas import TotalsOut, TransferOut, TransferUpdate
from ..security import get_current_user

router = APIRouter(prefix="/api/transfers", tags=["transfers"])


@router.get("", response_model=list[TransferOut])
def list_transfers(
    date: str | None = None,
    group_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    q = db.query(Transfer)
    if date:
        q = q.filter(Transfer.local_date == date)
    if group_id is not None:
        q = q.filter(Transfer.group_id == group_id)
    if status:
        q = q.filter(Transfer.status == status)
    return q.order_by(Transfer.received_at.desc()).limit(500).all()


@router.get("/totals", response_model=TotalsOut)
def totals(
    date: str | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if not date:
        date = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")
    return totals_for_date(db, date)


@router.get("/{transfer_id}/image")
def get_image(
    transfer_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    t = db.get(Transfer, transfer_id)
    if not t or not t.image_path:
        raise HTTPException(404, "Imagen no encontrada")
    return FileResponse(t.image_path)


@router.put("/{transfer_id}", response_model=TransferOut)
def update_transfer(
    transfer_id: int,
    data: TransferUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    t = db.get(Transfer, transfer_id)
    if not t:
        raise HTTPException(404, "Transferencia no encontrada")
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(t, field, value)
    # Al corregir manualmente, si no se especifica estado, marcar como procesada
    if "status" not in payload:
        t.status = "processed"
        t.review_reason = None
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{transfer_id}")
def delete_transfer(
    transfer_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    t = db.get(Transfer, transfer_id)
    if not t:
        raise HTTPException(404, "Transferencia no encontrada")
    db.delete(t)
    db.commit()
    return {"ok": True}
