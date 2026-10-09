from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class PhoneRecord(Base):
    __tablename__ = "phone_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rawTranscript: Mapped[str] = mapped_column(Text, nullable=False)
    parsedNumber: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    collectedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
