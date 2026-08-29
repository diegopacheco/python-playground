from collections.abc import Iterable
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


class InvalidOwner(Exception):
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
    if value.copy_abs() >= MAX_MONEY:
        raise InvalidAmount("amount is too large to store")
    if value != value.quantize(CENTS):
        raise InvalidAmount("amount cannot be finer than one cent")


def _check_amount(value: Decimal) -> None:
    _check_money(value)
    if value <= 0:
        raise InvalidAmount("amount must be greater than zero")


def _check_transfer(source_id: int, target_id: int, amount: Decimal) -> None:
    if source_id == target_id:
        raise InvalidTransfer("source and target must be different accounts")
    _check_amount(amount)


def _check_owner(value: str) -> None:
    if not value.strip():
        raise InvalidOwner("owner must not be blank")


def _check_balance(value: Decimal) -> None:
    if value >= MAX_MONEY:
        raise InvalidAmount(f"a balance of {value} is too large to store")


async def _lock_accounts(
    accounts: AccountDAO, account_ids: Iterable[int]
) -> list[Account]:
    wanted = tuple(account_ids)
    locked = await accounts.find_all_for_update(wanted)
    found = {account.id for account in locked}
    for account_id in wanted:
        if account_id not in found:
            raise AccountNotFound(f"account {account_id} does not exist")
    return locked


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
        _check_transfer(source_id, target_id, amount)
        await _lock_accounts(self.accounts, (source_id, target_id))
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
        _check_owner(owner)
        _check_money(initial_balance)
        if initial_balance.is_signed():
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
        _check_amount(amount)
        account = await self.lock_account(account_id)
        balance = account.balance + amount
        _check_balance(balance)
        return _account_view(await self.accounts.update_balance(account, balance))

    @transactional
    async def withdraw(self, account_id: int, amount: Decimal) -> AccountView:
        _check_amount(amount)
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
        _check_transfer(source_id, target_id, amount)
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
        return await _lock_accounts(self.accounts, account_ids)
