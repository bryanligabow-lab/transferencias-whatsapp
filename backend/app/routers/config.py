from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..reports import generate_and_send_report
from ..schemas import ConfigOut
from ..scheduler import reschedule
from ..security import get_current_user
from ..store import get_config, set_config

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("", response_model=ConfigOut)
def read_config(db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    return ConfigOut(**{k: get_config(db).get(k, "") for k in ConfigOut.model_fields})


@router.put("", response_model=ConfigOut)
def update_config(
    data: ConfigOut, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    set_config(db, data.model_dump())
    reschedule()
    return data


@router.post("/send-report-now")
async def send_report_now(
    date: str | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Genera y envía el informe del día (o de la fecha dada) inmediatamente."""
    result = await generate_and_send_report(db, date)
    return result
