from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api.v1 import router as v1
from app.core.logging import configure_logging
from app.core.metrics import REQS, LAT

configure_logging()
app = FastAPI(title="Carbon-Aware Attribution API", version="0.1.0")
app.include_router(v1)

@app.middleware("http")
async def metrics_mw(request: Request, call_next):
    route = request.url.path
    method = request.method
    with LAT.labels(route=route).time():
        resp = await call_next(request)
    REQS.labels(route=route, method=method, status=str(resp.status_code)).inc()
    return resp

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)