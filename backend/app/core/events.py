"""
Event-driven mimarinin backend tarafı: satış oluştuğunda Redis Stream'e
bir olay yayınlar. ml_service bu stream'i ayrı bir consumer group ile dinler
(bkz. ml_service/app/events/consumer.py) ve anomali skorunu hesaplayıp
sonucu doğrudan veritabanına yazar.

Redis Streams tercih edildi (Pub/Sub değil): ml_service o anda ayakta
değilse bile olaylar stream'de kalır, servis tekrar başladığında kaldığı
yerden (consumer group offset'i ile) devam eder.
"""
import json

import redis.asyncio as aioredis

from app.core.config import settings

SALES_STREAM_KEY = "erp:events:sales"

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def publish_sale_created(sale) -> str:
    """`sales` router'ında bir satış commit edildikten hemen sonra çağrılır."""
    payload = {
        "sale_id": str(sale.id),
        "customer_id": str(sale.customer_id),
        "total_amount": float(sale.total_amount),
        "item_count": len(sale.items),
    }
    client = get_redis_client()
    return await client.xadd(
        SALES_STREAM_KEY,
        {"event_type": "sale.created", "payload": json.dumps(payload)},
    )
