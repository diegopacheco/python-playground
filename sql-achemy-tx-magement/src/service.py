from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from dao import AccountDAO, LedgerDAO
from models import Account, LedgerEntry
from tx import transactional


CENTS = Decimal("0.01")
MAX_MONEY = Decimal("10000000000000000")


class AccountNotFound(Exception):
    pass


class InsufficientFunds(Exception):
    pass


class InvalidAmount(Exception):
    pass


class InvalidTransfer(Exception):
    pass


@dataclass(frozen=True)
class AccountView:
    id: int
    owner: str
    balance: Decimal


@dataclass(frozen=True)
class LedgerView:
    id: int
    source_id: int
    target_id: int
    amount: Decimal
    created_at: datetime


def _check_money(value: Decimal) -> None:
    if not value.is_finite():
        raise InvalidAmount("amount must be a finite number")
    if value.as_tuple().exponent < -2:
        raise InvalidAmount("amount cannot be finer than one cent")
    if abs(value) >= MAX_MONEY:
        raise InvalidAmount("amount is too large to store")


def _account_view(account: Account) -> AccountView:
    return AccountView(account.id, account.owner, account.balance.quantize(CENTS))


def _ledger_view(entry: LedgerEntry) -> LedgerView:
    return LedgerView(
        entry.id,
        entry.source_id,
        entry.target_id,
        entry.amount.quantize(CENTS),
        entry.created_at,
    )


class LedgerService:
    def __init__(self) -> None:
        self.entries = LedgerDAO()
        self.accounts = AccountDAO()

    @transactional
    async def record(
        self, source_id: int, target_id: int, amount: Decimal
    ) -> LedgerView:
        await self.accounts.find_all_for_update({source_id, target_id})
        return _ledger_view(await self.entries.insert(source_id, target_id, amount))

    @transactional
    async def list_all(self) -> list[LedgerView]:
        return [_ledger_view(entry) for entry in await self.entries.find_all()]


class BankService:
    def __init__(self) -> None:
        self.accounts = AccountDAO()
        self.ledger = LedgerService()

    @transactional
    async def open_account(self, owner: str, initial_balance: Decimal) -> AccountView:
        _check_money(initial_balance)
        if initial_balance < 0:
            raise InvalidAmount("initial balance cannot be negative")
        return _account_view(await self.accounts.insert(owner, initial_balance))

    @transactional
    async def list_accounts(self) -> list[AccountView]:
        return [_account_view(account) for account in await self.accounts.find_all()]

    @transactional
    async def get_account(self, account_id: int) -> AccountView:
        account = await self.accounts.find(account_id)
        if account is None:
            raise AccountNotFound(f"account {account_id} does not exist")
        return _account_view(account)

    @transactional
    async def deposit(self, account_id: int, amount: Decimal) -> AccountView:
        self._check_amount(amount)
        account = await self.lock_account(account_id)
        return _account_view(
            await self.accounts.update_balance(account, account.balance + amount)
        )

    @transactional
    async def withdraw(self, account_id: int, amount: Decimal) -> AccountView:
        self._check_amount(amount)
        account = await self.lock_account(account_id)
        if account.balance < amount:
            raise InsufficientFunds(
                f"account {account_id} has {account.balance}, cannot withdraw {amount}"
            )
        return _account_view(
            await self.accounts.update_balance(account, account.balance - amount)
        )

    @transactional
    async def transfer(
        self, source_id: int, target_id: int, amount: Decimal
    ) -> LedgerView:
        if source_id == target_id:
            raise InvalidTransfer("source and target must be different accounts")
        self._check_amount(amount)
        await self.lock_accounts(source_id, target_id)
        entry = await self.ledger.record(source_id, target_id, amount)
        await self.withdraw(source_id, amount)
        await self.deposit(target_id, amount)
        return entry

    @transactional
    async def list_ledger(self) -> list[LedgerView]:
        return await self.ledger.list_all()

    async def lock_account(self, account_id: int) -> Account:
        account = await self.accounts.find_for_update(account_id)
        if account is None:
            raise AccountNotFound(f"account {account_id} does not exist")
        return account

    async def lock_accounts(self, *account_ids: int) -> list[Account]:
        accounts = await self.accounts.find_all_for_update(account_ids)
        locked = {account.id for account in accounts}
        for account_id in account_ids:
            if account_id not in locked:
                raise AccountNotFound(f"account {account_id} does not exist")
        return accounts

    def _check_amount(self, amount: Decimal) -> None:
        _check_money(amount)
        if amount <= 0:
            raise InvalidAmount("amount must be greater than zero")
