"""Parsing híbrido opcional con un modelo de lenguaje LOCAL vía Ollama.

Corre en el mismo servidor => NO consume tokens de ninguna API externa.
Se usa solo si PARSE_MODE=hybrid. Estructura el texto del OCR en JSON.
"""

from __future__ import annotations

import json

import httpx

from .config import settings

PROMPT = """Eres un extractor de datos de comprobantes de transferencias bancarias.
A partir del TEXTO OCR (puede tener errores), devuelve SOLO un JSON válido con estas claves:
"sender_name" (nombre de quien envía o beneficiario),
"reference" (número de referencia/comprobante),
"account" (número de cuenta),
"bank" (banco/entidad),
"transfer_datetime" (fecha y hora tal cual aparece),
"amount" (monto como número decimal, sin símbolos),
"is_transfer" (true/false si el texto corresponde a una transferencia).
Si un dato no aparece, usa null. No inventes datos.

TEXTO OCR:
\"\"\"
{ocr}
\"\"\"
JSON:"""


async def parse_with_ollama(ocr_text: str) -> dict | None:
    payload = {
        "model": settings.ollama_model,
        "prompt": PROMPT.format(ocr=ocr_text[:4000]),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{settings.ollama_base_url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            raw = data.get("response", "").strip()
            parsed = json.loads(raw)
            if isinstance(parsed.get("amount"), str):
                amt = parsed["amount"].replace("$", "").replace(",", "").strip()
                try:
                    parsed["amount"] = float(amt)
                except ValueError:
                    parsed["amount"] = None
            return parsed
    except Exception:  # noqa: BLE001 - si falla el modelo local, caemos a reglas
        return None
