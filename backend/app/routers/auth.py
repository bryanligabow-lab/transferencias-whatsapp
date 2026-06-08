from fastapi import APIRouter, HTTPException, status

from ..schemas import LoginIn, Token
from ..security import create_token, verify_credentials

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(data: LoginIn):
    if not verify_credentials(data.username, data.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
    return Token(access_token=create_token(data.username))
