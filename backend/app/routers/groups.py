from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Group
from ..schemas import GroupOut, GroupUpdate
from ..scheduler import reschedule
from ..security import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("", response_model=list[GroupOut])
def list_groups(
    instance_id: int | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    q = db.query(Group)
    if instance_id is not None:
        q = q.filter(Group.instance_id == instance_id)
    return q.order_by(Group.name).all()


@router.put("/{group_id}", response_model=GroupOut)
def update_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Grupo no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    db.commit()
    db.refresh(group)
    reschedule()  # por si cambió report_time
    return group
