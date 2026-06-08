"""Cliente para Evolution API (v2).

Documentación de referencia de endpoints usados:
- GET  /instance/connectionState/{instance}        -> estado de la sesión
- GET  /instance/connect/{instance}                -> QR para vincular WhatsApp
- POST /webhook/set/{instance}                     -> configura el webhook
- GET  /group/fetchAllGroups/{instance}            -> lista de grupos
- POST /chat/getBase64FromMediaMessage/{instance}  -> descarga media en base64
- POST /message/sendMedia/{instance}               -> envía archivo (PDF) por WhatsApp
"""

from __future__ import annotations

import httpx


class EvolutionClient:
    def __init__(self, base_url: str, api_key: str, instance: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.instance = instance

    @property
    def _headers(self) -> dict:
        return {"apikey": self.api_key, "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    async def connection_state(self) -> dict:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                self._url(f"/instance/connectionState/{self.instance}"),
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()

    async def connect(self) -> dict:
        """Devuelve el QR (base64) o el estado de conexión."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                self._url(f"/instance/connect/{self.instance}"),
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()

    async def set_webhook(self, webhook_url: str) -> dict:
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "webhookByEvents": False,
                "webhookBase64": True,
                "events": ["MESSAGES_UPSERT"],
            }
        }
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                self._url(f"/webhook/set/{self.instance}"),
                headers=self._headers,
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    async def fetch_groups(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.get(
                self._url(f"/group/fetchAllGroups/{self.instance}"),
                headers=self._headers,
                params={"getParticipants": "false"},
            )
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict):
                data = data.get("groups", data.get("data", []))
            return data or []

    async def get_media_base64(self, message: dict) -> str | None:
        """Descarga la media de un mensaje y devuelve base64."""
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                self._url(f"/chat/getBase64FromMediaMessage/{self.instance}"),
                headers=self._headers,
                json={"message": message, "convertToMp4": False},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("base64")

    async def send_media(
        self, number: str, file_b64: str, filename: str, caption: str = ""
    ) -> dict:
        payload = {
            "number": number,
            "mediatype": "document",
            "fileName": filename,
            "media": file_b64,
            "caption": caption,
        }
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                self._url(f"/message/sendMedia/{self.instance}"),
                headers=self._headers,
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    async def send_text(self, number: str, text: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                self._url(f"/message/sendText/{self.instance}"),
                headers=self._headers,
                json={"number": number, "text": text},
            )
            r.raise_for_status()
            return r.json()
