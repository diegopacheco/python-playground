from asgiref.sync import sync_to_async

from ..domain.errors import NotFound
from ..models import Account


def load_account(account_id):
    account = Account.objects.select_related("profile").filter(pk=account_id).first()
    if account is None:
        raise NotFound(f"account {account_id} not found")
    return account


async def get_account(account_id):
    return await sync_to_async(load_account)(account_id)


async def list_accounts():
    query = Account.objects.select_related("profile").order_by("profile__full_name")
    return [account async for account in query]
