"""Parser de comprobantes de transferencia mediante reglas/regex por banco.

Extensible: para añadir un banco nuevo, agrega una entrada en BANKS con sus
palabras clave de detección y (opcionalmente) regex específicas de campos.
El parser combina reglas específicas del banco con regex genéricas de respaldo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Definición de bancos (Ecuador como referencia, extensible a cualquier banco)
# ---------------------------------------------------------------------------


@dataclass
class BankRule:
    name: str
    keywords: list[str]
    # regex específicas opcionales por campo (con grupo 1 = valor)
    patterns: dict[str, str] = field(default_factory=dict)


BANKS: list[BankRule] = [
    BankRule("Banco Pichincha", ["pichincha"]),
    BankRule("Banco Guayaquil", ["banco guayaquil", "bancoguayaquil"]),
    BankRule("Banco del Pacífico", ["pacifico", "pacífico", "bancodelpacifico"]),
    BankRule("Produbanco", ["produbanco"]),
    BankRule("Banco Internacional", ["banco internacional", "bancointernacional"]),
    BankRule("Banco Bolivariano", ["bolivariano"]),
    BankRule("Cooperativa JEP", ["jep", "juventud ecuatoriana"]),
    BankRule("Banco del Austro", ["del austro", "austro"]),
    BankRule("BanEcuador", ["banecuador"]),
    BankRule("DeUna", ["deuna", "de una"]),
]

# Indicadores de que la imagen realmente es un comprobante de transferencia
TRANSFER_HINTS = [
    "transferencia",
    "comprobante",
    "transferiste",
    "enviaste",
    "exitosa",
    "pago",
    "monto",
    "valor",
    "beneficiario",
    "referencia",
    "comprobante no",
    "nro. transacción",
    "transaccion",
]

# ---------------------------------------------------------------------------
# Regex genéricas de respaldo
# ---------------------------------------------------------------------------

AMOUNT_RE = re.compile(
    r"(?:USD|US\$|\$|valor|monto|total)\s*[:\-]?\s*\$?\s*"
    r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2})",
    re.IGNORECASE,
)
AMOUNT_FALLBACK_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})")

REFERENCE_RE = re.compile(
    r"(?:referencia|comprobante|transacci[oó]n|operaci[oó]n|documento)\s*"
    r"(?:n[roº°o]*\.?)?\s*[:#\-]?\s*([A-Z0-9\-]{4,30})",
    re.IGNORECASE,
)

ACCOUNT_RE = re.compile(
    r"(?:cuenta|cta|account)[^\d\nX\*]{0,15}?([0-9X\*]{4,}[0-9X\*\-]{0,20})",
    re.IGNORECASE,
)

DATE_RE = re.compile(
    r"(\d{1,2}[\/\- ](?:\d{1,2}|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
    r"[\/\- ]\d{2,4}(?:[ ,]+\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?)?)",
    re.IGNORECASE,
)

NAME_RE = re.compile(
    r"(?:beneficiario|para|destinatario|nombre|titular|recibe|a nombre de)\s*[:#\-]?[ \t]*"
    r"([A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ\. ]{4,60})",
    re.IGNORECASE,
)


@dataclass
class ParseResult:
    bank: str | None = None
    sender_name: str | None = None
    reference: str | None = None
    account: str | None = None
    transfer_datetime: str | None = None
    amount: float | None = None
    is_transfer: bool = False
    missing: list[str] = field(default_factory=list)

    def as_fields(self) -> dict:
        return {
            "bank": self.bank,
            "sender_name": self.sender_name,
            "reference": self.reference,
            "account": self.account,
            "transfer_datetime": self.transfer_datetime,
            "amount": self.amount,
        }


def _normalize_amount(raw: str) -> float | None:
    raw = raw.strip()
    # Detectar separador decimal por la última aparición de . o ,
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        # coma como decimal si hay 2 dígitos después
        if re.search(r",\d{2}$", raw):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    try:
        return round(float(raw), 2)
    except ValueError:
        return None


def detect_bank(text_lower: str) -> str | None:
    for bank in BANKS:
        if any(k in text_lower for k in bank.keywords):
            return bank.name
    return None


def looks_like_transfer(text_lower: str, amount: float | None) -> bool:
    hits = sum(1 for h in TRANSFER_HINTS if h in text_lower)
    return hits >= 1 and amount is not None or hits >= 2


def parse_transfer(text: str) -> ParseResult:
    res = ParseResult()
    if not text or not text.strip():
        res.missing = ["all"]
        return res

    text_lower = text.lower()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    res.bank = detect_bank(text_lower)

    # Reglas específicas del banco (si las hubiera)
    bank_rule = next((b for b in BANKS if b.name == res.bank), None)
    if bank_rule:
        for fieldname, pat in bank_rule.patterns.items():
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                setattr(res, fieldname, m.group(1).strip())

    # Monto
    if res.amount is None:
        m = AMOUNT_RE.search(text)
        if not m:
            m = AMOUNT_FALLBACK_RE.search(text)
        if m:
            res.amount = _normalize_amount(m.group(1))

    # Referencia (debe contener al menos un dígito)
    if not res.reference:
        for m in REFERENCE_RE.finditer(text):
            candidate = m.group(1).strip()
            if any(ch.isdigit() for ch in candidate):
                res.reference = candidate
                break

    # Cuenta
    if not res.account:
        m = ACCOUNT_RE.search(text)
        if m:
            res.account = re.sub(r"\s+", "", m.group(1)).strip(" -")

    # Fecha
    if not res.transfer_datetime:
        m = DATE_RE.search(text)
        if m:
            res.transfer_datetime = m.group(1).strip()

    # Nombre
    if not res.sender_name:
        m = NAME_RE.search(text)
        if m:
            res.sender_name = re.sub(r"\s+", " ", m.group(1)).strip()
        elif lines:
            # heurística: línea en mayúsculas con 2+ palabras
            for ln in lines:
                words = ln.split()
                if 1 < len(words) <= 5 and ln.upper() == ln and ln.replace(" ", "").isalpha():
                    res.sender_name = ln.title()
                    break

    res.is_transfer = looks_like_transfer(text_lower, res.amount)

    # Campos faltantes para decidir "pendiente de revisión"
    for fname in ("amount", "reference", "bank", "transfer_datetime"):
        if not getattr(res, fname):
            res.missing.append(fname)

    return res
