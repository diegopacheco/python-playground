import asyncio

from django.db.models import F

from ..domain.errors import InsufficientFunds, ValidationError
from ..models import Account, Kind, Transaction
from .accounts import get_account

_lock = asyncio.Lock()


async def _credit(account, amount):
    await Account.objects.filter(pk=account.pk).aupdate(
        balance=F("balance") + amount
    )
    return await get_account(account.pk)


async def _debit(account, amount):
    changed = await Account.objects.filter(
        pk=account.pk, balance__gte=amount
    ).aupdate(balance=F("balance") - amount)
    if changed == 0:
        raise InsufficientFunds(
            f"account {account.number} has {account.balance}, cannot withdraw {amount}"
        )
    return await get_account(account.pk)


async def _record(account, kind, amount, counterparty=None):
    return await Transaction.objects.acreate(
        account=account,
        counterparty=counterparty,
        kind=kind,
        amount=amount,
        balance_after=account.balance,
    )


async def deposit(account_id, amount):
    async with _lock:
        account = await _credit(await get_account(account_id), amount)
        return await _record(account, Kind.DEPOSIT, amount)


async def withdraw(account_id, amount):
    async with _lock:
        account = await _debit(await get_account(account_id), amount)
        return await _record(account, Kind.WITHDRAW, amount)


async def transfer(source_id, target_id, amount):
    if source_id == target_id:
        raise ValidationError("source and target accounts must be different")
    async with _lock:
        source = await get_account(source_id)
        target = await get_account(target_id)
        source = await _debit(source, amount)
        target = await _credit(target, amount)
        return (
            await _record(source, Kind.TRANSFER_OUT, amount, counterparty=target),
            await _record(target, Kind.TRANSFER_IN, amount, counterparty=source),
        )


async def statement(account_id, limit=25):
    await get_account(account_id)
    query = Transaction.objects.filter(account_id=account_id).select_related(
        "counterparty", "counterparty__profile"
    )[:limit]
    return [entry async for entry in query]
