"""
Redis Streams consumer: backend'in yayınladığı 'sale.created' olaylarını
dinler, anomali skorunu hesaplar ve sonucu doğrudan veritabanına
(sales, ml_insights) yazar.

Backend artık ML servisini senkron beklemiyor (bkz. backend/app/core/events.py);
bu consumer, event-driven mimarinin ML tarafını oluşturur. Consumer group
kullanılır ki servis kapalıyken gelen event'ler kaybolmasın, servis tekrar
başladığında işlenmemiş mesajlardan devam etsin.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from redis.exceptions import ResponseError
from sqlalchemy import text

from app.anomaly_detection.service import check_anomaly
from app.common.database import SessionLocal, settings

logger = logging.getLogger(__name__)

STREAM_KEY = "erp:events:sales"
GROUP_NAME = "ml_service"
CONSUMER_NAME = "ml_service-1"


async def _ensure_group(client: aioredis.Redis) -> None:
    try:
        await client.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def _process_sale_created(payload: dict) -> None:
    """Senkron DB işlemi; event loop'u bloklamamak için ayrı thread'de çalıştırılır."""
    db = SessionLocal()
    try:
        result = check_anomaly(db, payload)
        db.execute(
            text(
                """
                UPDATE sales
                SET is_flagged_anomaly = :is_anomaly, anomaly_score = :score
                WHERE id = :sale_id
                """
            ),
            {
                "is_anomaly": result["is_anomaly"],
                "score": result["anomaly_score"],
                "sale_id": payload["sale_id"],
            },
        )
        db.execute(
            text(
                """
                INSERT INTO ml_insights (id, insight_type, entity_id, payload, generated_at)
                VALUES (:id, :insight_type, :entity_id, :payload, :generated_at)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "insight_type": "anomaly",
                "entity_id": payload["sale_id"],
                "payload": json.dumps(result),
                "generated_at": datetime.now(timezone.utc),
            },
        )
        db.commit()
        logger.info(
            "sale.created işlendi: sale_id=%s is_anomaly=%s",
            payload["sale_id"],
            result["is_anomaly"],
        )
    except Exception:
        db.rollback()
        logger.exception("sale.created işlenirken hata: payload=%s", payload)
        raise
    finally:
        db.close()


async def consume_sales_events() -> None:
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await _ensure_group(client)
    logger.info("ml_service: '%s' stream'i '%s' grubuyla dinleniyor", STREAM_KEY, GROUP_NAME)

    try:
        while True:
            try:
                response = await client.xreadgroup(
                    GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=10, block=5000
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Redis Streams okuma hatası, 3sn sonra tekrar denenecek")
                await asyncio.sleep(3)
                continue

            if not response:
                continue

            for _stream_key, messages in response:
                for message_id, fields in messages:
                    if fields.get("event_type") == "sale.created":
                        try:
                            payload = json.loads(fields["payload"])
                            await asyncio.to_thread(_process_sale_created, payload)
                        except Exception:
                            logger.exception("Mesaj işlenemedi, yine de ACK'lenecek: %s", message_id)
                    await client.xack(STREAM_KEY, GROUP_NAME, message_id)
    finally:
        await client.aclose()
