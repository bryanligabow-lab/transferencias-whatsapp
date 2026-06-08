from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Instance(Base):
    """Conexión a una instancia de Evolution API (credenciales encriptadas)."""

    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))  # etiqueta visible
    instance_name: Mapped[str] = mapped_column(String(120))  # instance name en Evolution
    base_url_enc: Mapped[str] = mapped_column(Text)  # encriptado
    api_key_enc: Mapped[str] = mapped_column(Text)  # encriptado
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(40), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    groups: Mapped[list["Group"]] = relationship(
        back_populates="instance", cascade="all, delete-orphan"
    )


class Group(Base):
    """Grupo de WhatsApp monitoreado dentro de una instancia."""

    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("instance_id", "group_jid", name="uq_instance_group"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id", ondelete="CASCADE"))
    group_jid: Mapped[str] = mapped_column(String(120))  # ej. 12036...@g.us
    name: Mapped[str] = mapped_column(String(200), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Config de reporte por grupo (opcional, si null usa la global)
    report_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    report_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    report_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "HH:MM"

    instance: Mapped["Instance"] = relationship(back_populates="groups")
    transfers: Mapped[list["Transfer"]] = relationship(back_populates="group")


class Transfer(Base):
    """Transferencia bancaria extraída de una imagen."""

    __tablename__ = "transfers"
    __table_args__ = (
        UniqueConstraint("dedup_key", name="uq_transfer_dedup"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )
    instance_id: Mapped[int | None] = mapped_column(ForeignKey("instances.id"), nullable=True)

    # Campos extraídos
    sender_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    account: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank: Mapped[str | None] = mapped_column(String(120), nullable=True)
    transfer_datetime: Mapped[str | None] = mapped_column(String(60), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadatos
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(400), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="processed")
    # processed | pending_review | invalid
    review_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    parse_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(64))
    sender_jid: Mapped[str | None] = mapped_column(String(120), nullable=True)

    received_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # Fecha local (YYYY-MM-DD) usada para el corte diario
    local_date: Mapped[str] = mapped_column(String(10), index=True)

    group: Mapped["Group"] = relationship(back_populates="transfers")


class AppConfig(Base):
    """Configuración global del sistema (clave/valor)."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
