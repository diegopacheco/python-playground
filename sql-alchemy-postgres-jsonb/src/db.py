import os
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, create_engine, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://jsonb_user:jsonb_pass@localhost:5433/jsonb_db",
)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
        }


engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine, expire_on_commit=False)


def create_schema() -> None:
    Base.metadata.create_all(engine)
