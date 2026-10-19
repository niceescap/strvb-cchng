import os
import secrets
import logging
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel

KEY = os.environ["BRIDGE_KEY"]
log = logging.getLogger("bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app = FastAPI(title="coach-bridge-test")


@app.middleware("http")
async def log_headers(request: Request, call_next):
    hdrs = {k: ("***" if k.lower() == "authorization" else v)
            for k, v in request.headers.items()}
    log.info("%s %s headers=%s", request.method, request.url.path, hdrs)
    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True}


class PingIn(BaseModel):
    value: str


@app.post("/v1/ping", operation_id="ping")
def ping(body: PingIn, authorization: str | None = Header(default=None)):
    expected = f"Bearer {KEY}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"echo": body.value, "service": "coach-bridge-test"}
