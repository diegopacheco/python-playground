from decimal import Decimal

from dao import AccountDAO, LedgerDAO
from models import Account, LedgerEntry
from tx import transactional


class AccountNotFound(Exception):
    pass


class InsufficientFunds(Exception):
    pass


class InvalidAmount(Exception):
    pass


class LedgerService:
    def __init__(self) -> None:
        self.entries = LedgerDAO()

    @transactional
    async def record(
        self, source_id: int, target_id: int, amount: Decimal
    ) -> LedgerEntry:
        return await self.entries.insert(source_id, target_id, amount)

    @transactional
    async def list_all(self) -> list[LedgerEntry]:
        return await self.entries.find_all()


class BankService:
    def __init__(self) -> None:
        self.accounts = AccountDAO()
        self.ledger = LedgerService()

    @transactional
    async def open_account(self, owner: str, initial_balance: Decimal) -> Account:
        if initial_balance < 0:
            raise InvalidAmount("initial balance cannot be negative")
        return await self.accounts.insert(owner, initial_balance)

    @transactional
    async def list_accounts(self) -> list[Account]:
        return await self.accounts.find_all()

    @transactional
    async def get_account(self, account_id: int) -> Account:
        account = await self.accounts.find(account_id)
        if account is None:
            raise AccountNotFound(f"account {account_id} does not exist")
        return account

    @transactional
    async def deposit(self, account_id: int, amount: Decimal) -> Account:
        self._check_amount(amount)
        account = await self.lock_account(account_id)
        return await self.accounts.update_balance(account, account.balance + amount)

    @transactional
    async def withdraw(self, account_id: int, amount: Decimal) -> Account:
        self._check_amount(amount)
        account = await self.lock_account(account_id)
        if account.balance < amount:
            raise InsufficientFunds(
                f"account {account_id} has {account.balance}, cannot withdraw {amount}"
            )
        return await self.accounts.update_balance(account, account.balance - amount)

    @transactional
    async def transfer(
        self, source_id: int, target_id: int, amount: Decimal
    ) -> LedgerEntry:
        self._check_amount(amount)
        entry = await self.ledger.record(source_id, target_id, amount)
        for account_id in sorted({source_id, target_id}):
            await self.lock_account(account_id)
        await self.withdraw(source_id, amount)
        await self.deposit(target_id, amount)
        return entry

    @transactional
    async def list_ledger(self) -> list[LedgerEntry]:
        return await self.ledger.list_all()

    @transactional
    async def lock_account(self, account_id: int) -> Account:
        account = await self.accounts.find_for_update(account_id)
        if account is None:
            raise AccountNotFound(f"account {account_id} does not exist")
        return account

    def _check_amount(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidAmount("amount must be greater than zero")
