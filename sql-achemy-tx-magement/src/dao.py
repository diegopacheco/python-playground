from decimal import Decimal

from sqlalchemy import select

from models import Account, LedgerEntry
from tx import current_session


class AccountDAO:
    async def insert(self, owner: str, balance: Decimal) -> Account:
        session = current_session()
        account = Account(owner=owner, balance=balance)
        session.add(account)
        await session.flush()
        return account

    async def find(self, account_id: int) -> Account | None:
        return await current_session().get(Account, account_id)

    async def find_all(self) -> list[Account]:
        result = await current_session().execute(select(Account).order_by(Account.id))
        return list(result.scalars())

    async def update_balance(self, account: Account, balance: Decimal) -> Account:
        account.balance = balance
        await current_session().flush()
        return account


class LedgerDAO:
    async def insert(
        self, source_id: int, target_id: int, amount: Decimal
    ) -> LedgerEntry:
        session = current_session()
        entry = LedgerEntry(source_id=source_id, target_id=target_id, amount=amount)
        session.add(entry)
        await session.flush()
        return entry

    async def find_all(self) -> list[LedgerEntry]:
        result = await current_session().execute(
            select(LedgerEntry).order_by(LedgerEntry.id)
        )
        return list(result.scalars())
