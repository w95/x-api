import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes import router
from .sessions import load_sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("x-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    added = await load_sessions()
    log.info("sessions registered this run: %d", added)
    yield


app = FastAPI(title="x-api", lifespan=lifespan)
app.include_router(router, prefix="/api")


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}
