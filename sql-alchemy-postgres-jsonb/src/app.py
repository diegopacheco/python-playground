import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from db import Document, Session, create_schema

STATIC_DIR = Path(__file__).parent / "static"



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_schema()
    yield


app = FastAPI(title="SQLAlchemy Postgres JSONB", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class DocumentPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data: dict[str, Any]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/documents")
def list_documents(contains: str | None = None) -> list[dict[str, Any]]:
    with Session() as session:
        query = session.query(Document)
        if contains:
            try:
                filter_obj = json.loads(contains)
            except json.JSONDecodeError as error:
                raise HTTPException(400, f"contains is not valid JSON: {error}")
            if not isinstance(filter_obj, dict):
                raise HTTPException(400, "contains must be a JSON object")
            query = query.filter(Document.data.contains(filter_obj))
        return [row.as_dict() for row in query.order_by(Document.id.desc()).all()]


@app.post("/api/documents", status_code=201)
def create_document(payload: DocumentPayload) -> dict[str, Any]:
    with Session() as session:
        document = Document(name=payload.name, data=payload.data)
        session.add(document)
        session.commit()
        return document.as_dict()


@app.put("/api/documents/{document_id}")
def update_document(document_id: int, payload: DocumentPayload) -> dict[str, Any]:
    with Session() as session:
        document = session.get(Document, document_id)
        if document is None:
            raise HTTPException(404, "document not found")
        document.name = payload.name
        document.data = payload.data
        session.commit()
        return document.as_dict()


@app.delete("/api/documents/{document_id}", status_code=204)
def delete_document(document_id: int) -> None:
    with Session() as session:
        document = session.get(Document, document_id)
        if document is None:
            raise HTTPException(404, "document not found")
        session.delete(document)
        session.commit()
