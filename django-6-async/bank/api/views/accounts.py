from ...domain.money import parse_amount
from ...services import accounts, ledger
from ..http import endpoint, json_response, read_body, require
from ..presenters import account_json, transaction_json


@endpoint("GET")
async def collection(request):
    found = await accounts.list_accounts()
    return json_response({"accounts": [account_json(a) for a in found]})


@endpoint("GET")
async def detail(request, account_id):
    account = await accounts.get_account(account_id)
    return json_response(account_json(account))


@endpoint("POST")
async def deposit(request, account_id):
    (amount,) = require(read_body(request), "amount")
    entry = await ledger.deposit(account_id, parse_amount(amount))
    return json_response(transaction_json(entry), status=201)


@endpoint("POST")
async def withdraw(request, account_id):
    (amount,) = require(read_body(request), "amount")
    entry = await ledger.withdraw(account_id, parse_amount(amount))
    return json_response(transaction_json(entry), status=201)


@endpoint("GET")
async def statement(request, account_id):
    limit = min(int(request.GET.get("limit", 25)), 100)
    entries = await ledger.statement(account_id, limit)
    return json_response({"transactions": [transaction_json(e) for e in entries]})
