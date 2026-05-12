from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from reconagent.api.routes import router
from reconagent.database import create_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db()
    yield


app = FastAPI(
    title="ReconAgent",
    version="0.1.0",
    description="AI finance operations backend for invoice, payment, and ledger reconciliation.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
