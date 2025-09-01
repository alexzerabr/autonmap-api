import httpx
import hmac
import hashlib
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

async def send_webhook(callback_url: str, payload: dict):
    try:
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        signature = hmac.new(
            settings.WEBHOOK_HMAC_SECRET.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-Autonmap-Signature-256': signature
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, content=payload_bytes, headers=headers, timeout=10.0)
            response.raise_for_status()
            
        logger.info(f"Webhook sent successfully to {callback_url}")

    except httpx.RequestError as e:
        logger.error(f"Failed to send webhook to {callback_url}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending webhook: {e}")
