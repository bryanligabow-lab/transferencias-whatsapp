import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from .config import settings


def _get_fernet() -> Fernet:
    key = settings.encryption_key.strip()
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY no configurada. Genera una con "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    # Si la clave no es Fernet válida (44 chars base64), derivar una a partir del texto.
    try:
        Fernet(key.encode())
        return Fernet(key.encode())
    except (ValueError, Exception):  # noqa: BLE001
        derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        return Fernet(derived)


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("No se pudo desencriptar el dato (clave incorrecta).") from exc
