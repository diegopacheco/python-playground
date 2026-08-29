from decimal import Decimal

import pytest

from service import BankService, InvalidAmount, InvalidTransfer, LedgerService


async def total_balance(bank: BankService) -> Decimal:
    return sum((a.balance for a in await bank.list_accounts()), Decimal("0.00"))


async def test_a_sub_cent_transfer_cannot_invent_money(bank: BankService):
    """Numeric(18, 2) rounds each leg on its own, so a debit of 0.125 and a credit of
    0.125 land as 0.12 and 0.13. Refusing the amount is what keeps the total constant."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("50.00"))
    before = await total_balance(bank)

    with pytest.raises(InvalidAmount):
        await bank.transfer(source.id, target.id, Decimal("0.125"))

    assert await total_balance(bank) == before
    assert await bank.list_ledger() == []


async def test_a_sub_cent_deposit_is_refused(bank: BankService):
    """0.005 rounds up to a cent the depositor never paid."""
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("0.005"))

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_sub_cent_opening_balance_is_refused(bank: BankService):
    with pytest.raises(InvalidAmount):
        await bank.open_account("alice", Decimal("0.005"))

    assert await bank.list_accounts() == []


async def test_a_non_finite_amount_is_refused(bank: BankService):
    """Decimal('NaN') <= 0 raises InvalidOperation, so the guard has to run first or
    the caller gets a decimal error instead of a refusal."""
    account = await bank.open_account("alice", Decimal("100.00"))

    for amount in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
        with pytest.raises(InvalidAmount):
            await bank.deposit(account.id, amount)

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_an_amount_the_column_cannot_hold_is_refused(bank: BankService):
    """Numeric(18, 2) holds sixteen digits before the point; more is a DataError from
    Postgres, which is a 500 the caller cannot act on."""
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("1e30"))

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_the_returned_view_is_the_value_the_database_kept(bank: BankService):
    """The view is built from the flushed entity, not from a re-read, so an amount that
    Postgres would store differently has to be refused before it reaches the column."""
    account = await bank.open_account("alice", Decimal("100.00"))

    returned = await bank.deposit(account.id, Decimal("0.1"))
    stored = await bank.get_account(account.id)

    assert returned.balance == stored.balance
    assert str(returned.balance) == str(stored.balance) == "100.10"


async def test_trailing_zeros_are_not_finer_than_a_cent(bank: BankService):
    """10.00000 and 1E+1 are the same ten. Testing the exponent instead of the value
    refused one of them and accepted the other, which is a 400 on valid money."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    await bank.transfer(source.id, target.id, Decimal("10.00000"))
    await bank.deposit(target.id, Decimal("1E+1"))

    assert (await bank.get_account(target.id)).balance == Decimal("20.00")
    assert (await bank.get_account(source.id)).balance == Decimal("90.00")


async def test_a_deposit_that_would_overflow_the_column_is_refused(bank: BankService):
    """The amount fits and the balance does not. Checking only the amount let the sum
    reach Postgres as a numeric field overflow, which blames the request for a value
    that was fine."""
    account = await bank.open_account("alice", Decimal("9999999999999999.99"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("1.00"))

    assert (await bank.get_account(account.id)).balance == Decimal("9999999999999999.99")


async def test_the_ledger_refuses_an_amount_the_bank_would_refuse(bank: BankService):
    """record() is a boundary of its own and the README says so, so it cannot rely on
    transfer() having validated the amount first."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))
    ledger = LedgerService()

    for amount in (Decimal("0.001"), Decimal("0.00"), Decimal("-5.00")):
        with pytest.raises(InvalidAmount):
            await ledger.record(source.id, target.id, amount)

    assert await bank.list_ledger() == []


async def test_the_ledger_refuses_a_transfer_to_the_same_account(bank: BankService):
    """record() is a boundary of its own, so it re-runs the amount check rather than
    trusting transfer(). The same reasoning covers the ids: one account cannot pay
    itself, and set() collapses the pair to a single lock the foreign keys accept."""
    account = await bank.open_account("alice", Decimal("100.00"))
    ledger = LedgerService()

    with pytest.raises(InvalidTransfer):
        await ledger.record(account.id, account.id, Decimal("5.00"))

    assert await bank.list_ledger() == []


async def test_an_amount_past_the_decimal_contexts_exponent_limit_is_refused(
    bank: BankService,
):
    """abs() is a context operation, so it raises decimal.Overflow for any exponent
    above Emax instead of answering. _check_money() called it before the size check
    could refuse the value, so an amount the column obviously cannot hold left the
    service as an ArithmeticError nothing handles rather than as InvalidAmount.
    copy_abs() is the context-free spelling and answers for every finite Decimal."""
    account = await bank.open_account("alice", Decimal("10.00"))
    other = await bank.open_account("bob", Decimal("10.00"))
    past_emax = Decimal("1E+999999999")

    for amount in (past_emax, Decimal("-1E+999999999"), Decimal("1E+1000000")):
        with pytest.raises(InvalidAmount):
            await bank.deposit(account.id, amount)
        with pytest.raises(InvalidAmount):
            await bank.withdraw(account.id, amount)
        with pytest.raises(InvalidAmount):
            await bank.transfer(account.id, other.id, amount)

    with pytest.raises(InvalidAmount):
        await bank.open_account("carol", past_emax)

    assert await total_balance(bank) == Decimal("20.00")


async def test_a_zero_amount_is_refused(bank: BankService):
    """Zero is money the schema can hold and a transfer that means nothing: it writes a
    ledger row saying an account moved nothing, and it takes both row locks to do it.
    The check is `<= 0` and not `< 0` for exactly that reason."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    for call in (
        bank.deposit(source.id, Decimal("0.00")),
        bank.withdraw(source.id, Decimal("0.00")),
        bank.transfer(source.id, target.id, Decimal("0.00")),
        LedgerService().record(source.id, target.id, Decimal("0.00")),
    ):
        with pytest.raises(InvalidAmount):
            await call

    assert await total_balance(bank) == Decimal("100.00")
    assert await bank.list_ledger() == []


async def test_a_negative_amount_is_refused(bank: BankService):
    """A negative deposit is a withdrawal that skips the funds check, and a negative
    withdrawal is a deposit that skips the overflow check. Each route would be the other
    one with its guard removed, so the sign is refused before either can run."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    for call in (
        bank.deposit(source.id, Decimal("-1.00")),
        bank.withdraw(source.id, Decimal("-1.00")),
        bank.transfer(source.id, target.id, Decimal("-1.00")),
    ):
        with pytest.raises(InvalidAmount):
            await call

    assert await total_balance(bank) == Decimal("100.00")


async def test_negative_zero_is_not_a_way_past_the_sign_check(bank: BankService):
    """Decimal keeps the sign of a zero, so -0.00 is a distinct value that is neither
    greater than zero nor obviously negative. It has to fail the same check, or the one
    spelling of nothing that reads as signed gets through."""
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("-0.00"))

    assert await total_balance(bank) == Decimal("100.00")


async def test_an_amount_under_the_decimal_contexts_exponent_limit_is_refused(
    bank: BankService,
):
    """The mirror of the Emax case. An exponent far below Emin is finite, is nowhere
    near too large for the column, and has to be answered by the scale check rather than
    raise out of quantize(). It is money finer than a cent by an enormous margin, so the
    answer is a refusal and not an Underflow nobody handles."""
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("1E-999999999"))

    assert await total_balance(bank) == Decimal("100.00")


async def test_a_transfer_that_would_overflow_the_target_moves_nothing(
    bank: BankService,
):
    """Both legs fit the column on their own and the sum does not, and the credit is the
    last thing a transfer does. Without the balance check the debit would already be
    flushed when Postgres refused the credit, so the transfer has to fail as a refused
    amount rather than as a DataError with half the money in flight."""
    big = Decimal("9999999999999999.00")
    source = await bank.open_account("alice", big)
    target = await bank.open_account("bob", big)

    with pytest.raises(InvalidAmount):
        await bank.transfer(source.id, target.id, Decimal("1.00"))

    assert (await bank.get_account(source.id)).balance == big
    assert (await bank.get_account(target.id)).balance == big
    assert await bank.list_ledger() == []


async def test_a_transfer_of_the_whole_balance_leaves_the_account_at_zero(
    bank: BankService,
):
    """The boundary between a transfer that commits and one that raises
    InsufficientFunds is `balance < amount`, so the exact balance has to be the last
    amount that works. CHECK (balance >= 0) has to agree, because zero is the value it
    is written to allow."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    await bank.transfer(source.id, target.id, Decimal("100.00"))

    assert (await bank.get_account(source.id)).balance == Decimal("0.00")
    assert (await bank.get_account(target.id)).balance == Decimal("100.00")
    assert await total_balance(bank) == Decimal("100.00")


async def test_the_largest_amount_the_column_can_hold_is_accepted(bank: BankService):
    """The size check is `>=`, so the refusal starts one cent above what Numeric(18, 2)
    holds and the largest value that fits has to go in and come back unchanged. A check
    written with `>` instead would refuse a legal balance, and one written against the
    wrong power of ten would let Postgres refuse it as a DataError instead."""
    largest = Decimal("9999999999999999.99")

    account = await bank.open_account("alice", largest)

    assert (await bank.get_account(account.id)).balance == largest
    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("0.01"))
    assert (await bank.get_account(account.id)).balance == largest


async def test_negative_zero_is_not_an_opening_balance_either(bank: BankService):
    """The sign check on an opening balance was `< 0`, which -0.00 is not, so the one
    spelling of nothing that carries a sign got past the layer every other amount is
    refused at. It is not a rounding curiosity: Postgres normalises the sign away, so
    the account came back as 0.00 on every later read while the 201 that created it said
    -0.00. One account with two balances is worse than the value itself."""
    with pytest.raises(InvalidAmount):
        await bank.open_account("alice", Decimal("-0.00"))

    assert await bank.list_accounts() == []


async def test_an_opening_balance_reads_back_the_way_it_was_returned(bank: BankService):
    """The invariant the sign check exists for. What open_account() answers is built in
    Python before the commit and what get_account() answers comes back out of Postgres,
    so any value the column stores differently than the service holds it makes those two
    disagree about the same account."""
    for owner, opening in (("alice", "0.00"), ("bob", "0.01"), ("carol", "12.30")):
        created = await bank.open_account(owner, Decimal(opening))

        read = await bank.get_account(created.id)

        assert str(read.balance) == str(created.balance) == opening
