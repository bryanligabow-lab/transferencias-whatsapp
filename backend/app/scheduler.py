"""Programador de tareas (APScheduler) para el informe diario.

Respeta la zona horaria de Ecuador (configurable) para el corte diario.
Reprograma los jobs cuando cambia la configuración de hora.
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .database import SessionLocal
from .models import Group
from .reports import generate_and_send_report, run_daily_reports
from .store import get_config

log = logging.getLogger("scheduler")
_scheduler: AsyncIOScheduler | None = None


def _parse_hhmm(value: str) -> tuple[int, int]:
    try:
        h, m = value.split(":")
        return int(h), int(m)
    except (ValueError, AttributeError):
        return 20, 0


async def _global_job():
    db = SessionLocal()
    try:
        await run_daily_reports(db)
    finally:
        db.close()


def _group_job(group_id: int):
    async def job():
        db = SessionLocal()
        try:
            group = db.get(Group, group_id)
            if group:
                await generate_and_send_report(db, group=group)
        finally:
            db.close()

    return job


def reschedule():
    """Reconstruye los jobs según la config actual."""
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.remove_all_jobs()

    db = SessionLocal()
    try:
        cfg = get_config(db)
        h, m = _parse_hhmm(cfg.get("report_time", "20:00"))
        _scheduler.add_job(
            _global_job,
            CronTrigger(hour=h, minute=m, timezone=settings.timezone),
            id="global_report",
            replace_existing=True,
        )
        log.info("Informe global programado a las %02d:%02d (%s)", h, m, settings.timezone)

        # Jobs por grupo con hora propia distinta de la global
        groups = (
            db.query(Group)
            .filter(Group.active.is_(True), Group.report_time.isnot(None))
            .all()
        )
        for g in groups:
            gh, gm = _parse_hhmm(g.report_time)
            _scheduler.add_job(
                _group_job(g.id),
                CronTrigger(hour=gh, minute=gm, timezone=settings.timezone),
                id=f"group_report_{g.id}",
                replace_existing=True,
            )
    finally:
        db.close()


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone=settings.timezone)
    _scheduler.start()
    reschedule()


def shutdown_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
