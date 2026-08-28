from ..domain.errors import NotFound
from ..models import Account


async def get_account(account_id):
    account = await Account.objects.select_related("profile").filter(pk=account_id).afirst()
    if account is None:
        raise NotFound(f"account {account_id} not found")
    return account


async def get_account_by_number(number):
    account = await Account.objects.select_related("profile").filter(number=number).afirst()
    if account is None:
        raise NotFound(f"account {number} not found")
    return account


async def list_accounts():
    query = Account.objects.select_related("profile").order_by("profile__full_name")
    return [account async for account in query]
