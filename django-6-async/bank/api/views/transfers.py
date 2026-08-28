from ...domain.money import parse_amount
from ...services import ledger
from ..http import endpoint, json_response, read_body, require
from ..presenters import transaction_json


@endpoint("POST")
async def create(request):
    source, target, amount = require(
        read_body(request), "source_account_id", "target_account_id", "amount"
    )
    sent, received = await ledger.transfer(
        int(source), int(target), parse_amount(amount)
    )
    return json_response(
        {"sent": transaction_json(sent), "received": transaction_json(received)},
        status=201,
    )
