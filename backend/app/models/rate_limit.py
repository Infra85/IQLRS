"""Shared fixed-window counters; keys contain hashes rather than personal data."""
from sqlalchemy import String, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RateLimit(Base):
    __tablename__ = 'request_limits'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[int] = mapped_column(BigInteger, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
