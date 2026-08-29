from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0 and balance <> 'NaN'", name="balance_is_money"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(80), unique=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2))


class LedgerEntry(Base):
    __tablename__ = "ledger"
    __table_args__ = (
        CheckConstraint("amount > 0 and amount <> 'NaN'", name="amount_is_money"),
        CheckConstraint("source_id <> target_id", name="two_different_accounts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    target_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
