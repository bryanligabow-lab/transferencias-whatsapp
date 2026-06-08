"""Helpers de configuración global (tabla app_config clave/valor)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import AppConfig

DEFAULTS = {
    "report_phone": "",
    "report_email": "",
    "report_time": "20:00",
}


def get_config(db: Session) -> dict:
    cfg = dict(DEFAULTS)
    for row in db.query(AppConfig).all():
        cfg[row.key] = row.value
    return cfg


def set_config(db: Session, data: dict):
    for key, value in data.items():
        row = db.get(AppConfig, key)
        if row:
            row.value = value or ""
        else:
            db.add(AppConfig(key=key, value=value or ""))
    db.commit()
