from ..domain.money import format_amount


def account_json(account):
    return {
        "id": account.pk,
        "number": account.number,
        "balance": format_amount(account.balance),
        "owner": account.profile.full_name,
    }


def profile_json(profile):
    return {
        "id": profile.pk,
        "full_name": profile.full_name,
        "email": profile.email,
        "created_at": profile.created_at.isoformat(),
        "account": account_json(profile.account),
    }


def transaction_json(entry):
    return {
        "id": entry.pk,
        "kind": entry.kind,
        "amount": format_amount(entry.amount),
        "balance_after": format_amount(entry.balance_after),
        "counterparty": (
            entry.counterparty.profile.full_name if entry.counterparty else None
        ),
        "created_at": entry.created_at.isoformat(),
    }
