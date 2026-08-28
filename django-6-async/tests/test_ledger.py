import asyncio
from decimal import Decimal

from django.test import TestCase

from bank.domain.errors import InsufficientFunds, NotFound, ValidationError
from bank.models import Account, Kind
from bank.services import ledger, profiles


class LedgerTest(TestCase):
    async def open(self, name, email, opening="0"):
        profile = await profiles.create_profile(name, email)
        if Decimal(opening) > 0:
            await ledger.deposit(profile.account.id, Decimal(opening))
        return profile.account.id

    async def balance(self, account_id):
        return (await Account.objects.aget(pk=account_id)).balance

    async def test_deposit_raises_balance_and_records_the_new_balance(self):
        account = await self.open("Ada Lovelace", "ada@bank.dev")
        entry = await ledger.deposit(account, Decimal("100.00"))
        self.assertEqual(entry.kind, Kind.DEPOSIT)
        self.assertEqual(entry.balance_after, Decimal("100.00"))
        self.assertEqual(await self.balance(account), Decimal("100.00"))

    async def test_withdraw_lowers_balance_and_records_the_new_balance(self):
        account = await self.open("Ada Lovelace", "ada@bank.dev", "100.00")
        entry = await ledger.withdraw(account, Decimal("40.00"))
        self.assertEqual(entry.balance_after, Decimal("60.00"))
        self.assertEqual(await self.balance(account), Decimal("60.00"))

    async def test_withdraw_beyond_balance_is_refused_so_accounts_never_go_negative(self):
        account = await self.open("Ada Lovelace", "ada@bank.dev", "50.00")
        with self.assertRaises(InsufficientFunds):
            await ledger.withdraw(account, Decimal("50.01"))
        self.assertEqual(await self.balance(account), Decimal("50.00"))

    async def test_transfer_moves_money_without_creating_or_destroying_any(self):
        source = await self.open("Ada Lovelace", "ada@bank.dev", "100.00")
        target = await self.open("Alan Turing", "alan@bank.dev", "10.00")
        sent, received = await ledger.transfer(source, target, Decimal("30.00"))
        self.assertEqual(sent.kind, Kind.TRANSFER_OUT)
        self.assertEqual(received.kind, Kind.TRANSFER_IN)
        self.assertEqual(await self.balance(source), Decimal("70.00"))
        self.assertEqual(await self.balance(target), Decimal("40.00"))

    async def test_failed_transfer_leaves_both_sides_untouched(self):
        source = await self.open("Ada Lovelace", "ada@bank.dev", "10.00")
        target = await self.open("Alan Turing", "alan@bank.dev", "10.00")
        with self.assertRaises(InsufficientFunds):
            await ledger.transfer(source, target, Decimal("11.00"))
        self.assertEqual(await self.balance(source), Decimal("10.00"))
        self.assertEqual(await self.balance(target), Decimal("10.00"))

    async def test_transfer_to_self_is_refused_so_the_statement_stays_meaningful(self):
        account = await self.open("Ada Lovelace", "ada@bank.dev", "10.00")
        with self.assertRaises(ValidationError):
            await ledger.transfer(account, account, Decimal("1.00"))

    async def test_unknown_account_is_reported_as_not_found(self):
        with self.assertRaises(NotFound):
            await ledger.deposit(999, Decimal("1.00"))

    async def test_concurrent_withdrawals_never_overdraw_the_account(self):
        account = await self.open("Ada Lovelace", "ada@bank.dev", "100.00")
        results = await asyncio.gather(
            *(ledger.withdraw(account, Decimal("10.00")) for _ in range(20)),
            return_exceptions=True,
        )
        settled = [r for r in results if not isinstance(r, Exception)]
        self.assertEqual(len(settled), 10)
        self.assertEqual(await self.balance(account), Decimal("0.00"))

    async def test_statement_returns_newest_first_and_honours_the_limit(self):
        account = await self.open("Ada Lovelace", "ada@bank.dev")
        for amount in ["1.00", "2.00", "3.00"]:
            await ledger.deposit(account, Decimal(amount))
        entries = await ledger.statement(account, limit=2)
        self.assertEqual([e.amount for e in entries], [Decimal("3.00"), Decimal("2.00")])


class ProfileServiceTest(TestCase):
    async def test_new_profile_gets_an_account_with_a_zero_balance(self):
        profile = await profiles.create_profile("Ada Lovelace", "ada@bank.dev")
        self.assertEqual(profile.account.balance, Decimal("0"))
        self.assertEqual(len(profile.account.number), 12)

    async def test_duplicate_email_is_refused_so_one_person_has_one_account(self):
        await profiles.create_profile("Ada Lovelace", "ada@bank.dev")
        with self.assertRaises(Exception):
            await profiles.create_profile("Ada L.", "ADA@bank.dev")
