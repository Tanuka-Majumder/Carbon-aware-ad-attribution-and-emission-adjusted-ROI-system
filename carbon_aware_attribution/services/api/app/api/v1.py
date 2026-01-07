from fastapi import APIRouter
from app.api.routes_health import router as health
from app.api.routes_attribution import router as attrib

router = APIRouter(prefix="/v1")
router.include_router(health, tags=["health"])
router.include_router(attrib, tags=["attribution"])