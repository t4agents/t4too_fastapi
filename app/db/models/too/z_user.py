from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_GLOBAL


class ZUserDB(Base, BaseMixin):
    __tablename__ = "zuser"
    __table_args__ = {"schema": SCHEMA_TOO_GLOBAL}

    plan_type:  Mapped[str | None] = mapped_column(String(64))
    plan_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    plan_expires:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    plan_is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=True)

    # above is trigger generated
    # below is regular table
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)        # for backward compatibility, can be removed later
    full_name: Mapped[str] = mapped_column(String, nullable=True) 
    usr_type: Mapped[str] = mapped_column(String, nullable=True)
    avatar: Mapped[str] = mapped_column(String, nullable=True)    
    phone: Mapped[str] = mapped_column(String, nullable=True)
    position: Mapped[str] = mapped_column(String, nullable=True)
    note: Mapped[str] = mapped_column(String, nullable=True)

    # Social links
    facebook: Mapped[str] = mapped_column(String, nullable=True)
    twitter: Mapped[str] = mapped_column(String, nullable=True)
    github: Mapped[str] = mapped_column(String, nullable=True)
    reddit: Mapped[str] = mapped_column(String, nullable=True)

    # Address details
    country: Mapped[str] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=True)
    pin: Mapped[str] = mapped_column(String, nullable=True)
    zip: Mapped[str] = mapped_column(String, nullable=True)
    tax_no: Mapped[str] = mapped_column(String, nullable=True)

    role: Mapped[str] = mapped_column(String, nullable=True, default="owner")
    group: Mapped[str] = mapped_column(String, nullable=True, default="coregroup")

