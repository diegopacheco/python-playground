import asyncio

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import F

from ..domain.errors import InsufficientFunds, ValidationError
from ..models import Account, Kind, Transaction
from .accounts import get_account, load_account

_lock = asyncio.Lock()


def _credit(account, amount):
    Account.objects.filter(pk=account.pk).update(balance=F("balance") + amount)
    return load_account(account.pk)


def _debit(account, amount):
    changed = Account.objects.filter(pk=account.pk, balance__gte=amount).update(
        balance=F("balance") - amount
    )
    if changed == 0:
        raise InsufficientFunds(
            f"account {account.number} has {account.balance}, cannot withdraw {amount}"
        )
    return load_account(account.pk)


def _record(account, kind, amount, counterparty=None):
    return Transaction.objects.create(
        account=account,
        counterparty=counterparty,
        kind=kind,
        amount=amount,
        balance_after=account.balance,
    )


@transaction.atomic
def _deposit(account_id, amount):
    account = _credit(load_account(account_id), amount)
    return _record(account, Kind.DEPOSIT, amount)


@transaction.atomic
def _withdraw(account_id, amount):
    account = _debit(load_account(account_id), amount)
    return _record(account, Kind.WITHDRAW, amount)


@transaction.atomic
def _transfer(source_id, target_id, amount):
    source = load_account(source_id)
    target = load_account(target_id)
    source = _debit(source, amount)
    target = _credit(target, amount)
    return (
        _record(source, Kind.TRANSFER_OUT, amount, counterparty=target),
        _record(target, Kind.TRANSFER_IN, amount, counterparty=source),
    )


async def deposit(account_id, amount):
    async with _lock:
        return await sync_to_async(_deposit)(account_id, amount)


async def withdraw(account_id, amount):
    async with _lock:
        return await sync_to_async(_withdraw)(account_id, amount)


async def transfer(source_id, target_id, amount):
    if source_id == target_id:
        raise ValidationError("source and target accounts must be different")
    async with _lock:
        return await sync_to_async(_transfer)(source_id, target_id, amount)


async def statement(account_id, limit=25):
    await get_account(account_id)
    query = Transaction.objects.filter(account_id=account_id).select_related(
        "counterparty", "counterparty__profile"
    )[:limit]
    return [entry async for entry in query]
