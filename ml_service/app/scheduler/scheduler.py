"""
Model yeniden eğitim job'larını zamanlar. main.py'deki mevcut asyncio
background-task deseniyle (bkz. app/events/consumer.py) aynı şekilde
startup/shutdown event'lerine bağlanır — ayrı bir worker/broker süreci yok.
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.common.database import settings
from app.scheduler.retrain import run_scheduled_retraining

logger = logging.getLogger(__name__)

JOB_ID = "scheduled_model_retraining"


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour_str, minute_str = value.split(":")
    return int(hour_str), int(minute_str)


async def _run_retraining_job() -> None:
    logger.info("Zamanlanmış model yeniden eğitimi başlıyor")
    try:
        await asyncio.to_thread(run_scheduled_retraining)
    except Exception:
        logger.exception("Zamanlanmış model yeniden eğitimi sırasında beklenmeyen hata")


def build_scheduler() -> AsyncIOScheduler:
    hour, minute = _parse_hhmm(settings.RETRAIN_SCHEDULE_TIME)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _run_retraining_job,
        trigger=CronTrigger(hour=hour, minute=minute),
        id=JOB_ID,
        replace_existing=True,
        coalesce=True,  # servis bir süre kapalıysa, tek bir kayıp çalıştırmayı art arda tekrarlama
        misfire_grace_time=3600,
    )
    return scheduler
