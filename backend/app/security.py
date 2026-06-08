from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

_ALGORITHM = "HS256"
# Hash de la contraseña admin (se calcula al iniciar desde la env var)
_admin_hash = pwd_context.hash(settings.admin_password)


def verify_credentials(username: str, password: str) -> bool:
    return username == settings.admin_username and pwd_context.verify(password, _admin_hash)


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
    return username
