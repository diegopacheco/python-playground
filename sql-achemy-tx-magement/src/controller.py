from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi import Path as PathParam
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import (
    DataError,
    IntegrityError,
    OperationalError,
    TimeoutError as PoolTimeout,
)

from db import create_schema
from service import (
    AccountNotFound,
    AccountView,
    BankService,
    InsufficientFunds,
    InvalidAmount,
    InvalidTransfer,
    LedgerView,
)
from tx import (
    CrossTaskTransaction,
    NoActiveTransaction,
    TransactionNotYours,
    UnexpectedRollback,
)


MAX_ID = 2_147_483_647
AccountId = Annotated[int, PathParam(ge=1, le=MAX_ID)]


class OpenAccountRequest(BaseModel):
    owner: str = Field(min_length=1, max_length=80)
    initial_balance: Decimal = Decimal("0.00")


class AmountRequest(BaseModel):
    amount: Decimal


class TransferRequest(BaseModel):
    source_id: int = Field(ge=1, le=MAX_ID)
    target_id: int = Field(ge=1, le=MAX_ID)
    amount: Decimal


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_schema()
    yield


app = FastAPI(title="Bank Transaction Boundary", lifespan=lifespan)
service = BankService()
INDEX = Path(__file__).parent / "index.html"


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(INDEX)


def as_account(account: AccountView) -> dict:
    return {"id": account.id, "owner": account.owner, "balance": str(account.balance)}


def as_entry(entry: LedgerView) -> dict:
    return {
        "id": entry.id,
        "source_id": entry.source_id,
        "target_id": entry.target_id,
        "amount": str(entry.amount),
        "created_at": entry.created_at.isoformat(),
    }


@app.exception_handler(AccountNotFound)
async def handle_account_not_found(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(InsufficientFunds)
async def handle_insufficient_funds(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.exception_handler(InvalidAmount)
async def handle_invalid_amount(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(InvalidTransfer)
async def handle_invalid_transfer(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(IntegrityError)
async def handle_conflict(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"error": "the write conflicts with a row that already exists"},
    )


@app.exception_handler(DataError)
async def handle_out_of_range(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": "a value in the request is out of range for the schema"},
    )


@app.exception_handler(OperationalError)
@app.exception_handler(PoolTimeout)
async def handle_database_unavailable(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "the database refused to wait for a lock, ran out of connections "
            "or was unreachable"
        },
    )


@app.exception_handler(UnexpectedRollback)
@app.exception_handler(NoActiveTransaction)
@app.exception_handler(CrossTaskTransaction)
@app.exception_handler(TransactionNotYours)
async def handle_transaction_misuse(request: Request, exc: Exception) -> JSONResponse:
    cause = exc.__cause__
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "cause": None if cause is None else f"{type(cause).__name__}: {cause}",
        },
    )


@app.post("/api/accounts", status_code=201)
async def open_account(body: OpenAccountRequest) -> dict:
    return as_account(await service.open_account(body.owner, body.initial_balance))


@app.get("/api/accounts")
async def list_accounts() -> list[dict]:
    return [as_account(account) for account in await service.list_accounts()]


@app.get("/api/accounts/{account_id}")
async def get_account(account_id: AccountId) -> dict:
    return as_account(await service.get_account(account_id))


@app.post("/api/accounts/{account_id}/deposit")
async def deposit(account_id: AccountId, body: AmountRequest) -> dict:
    return as_account(await service.deposit(account_id, body.amount))


@app.post("/api/accounts/{account_id}/withdraw")
async def withdraw(account_id: AccountId, body: AmountRequest) -> dict:
    return as_account(await service.withdraw(account_id, body.amount))


@app.post("/api/transfers", status_code=201)
async def transfer(body: TransferRequest) -> dict:
    return as_entry(
        await service.transfer(body.source_id, body.target_id, body.amount)
    )


@app.get("/api/ledger")
async def list_ledger() -> list[dict]:
    return [as_entry(entry) for entry in await service.list_ledger()]
