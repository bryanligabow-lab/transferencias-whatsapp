from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class InstanceIn(BaseModel):
    name: str
    instance_name: str
    base_url: str
    api_key: str


class InstanceOut(BaseModel):
    id: int
    name: str
    instance_name: str
    base_url: str  # se devuelve desencriptada solo para el admin autenticado
    connected: bool
    status: str

    class Config:
        from_attributes = True


class GroupOut(BaseModel):
    id: int
    instance_id: int
    group_jid: str
    name: str
    active: bool
    report_phone: str | None = None
    report_email: str | None = None
    report_time: str | None = None

    class Config:
        from_attributes = True


class GroupSync(BaseModel):
    group_jid: str
    name: str


class GroupUpdate(BaseModel):
    active: bool | None = None
    report_phone: str | None = None
    report_email: str | None = None
    report_time: str | None = None


class TransferOut(BaseModel):
    id: int
    group_id: int | None
    sender_name: str | None
    reference: str | None
    account: str | None
    bank: str | None
    transfer_datetime: str | None
    amount: float | None
    status: str
    review_reason: str | None
    parse_method: str | None
    received_at: datetime
    local_date: str

    class Config:
        from_attributes = True


class TransferUpdate(BaseModel):
    sender_name: str | None = None
    reference: str | None = None
    account: str | None = None
    bank: str | None = None
    transfer_datetime: str | None = None
    amount: float | None = None
    status: str | None = None


class ConfigOut(BaseModel):
    report_phone: str = ""
    report_email: str = ""
    report_time: str = "20:00"


class TotalsOut(BaseModel):
    date: str
    total: float
    count: int
    by_group: list[dict]
