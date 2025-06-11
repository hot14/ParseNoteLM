from fastapi import APIRouter, Response
from app.services.monitoring_service import performance_monitor, CONTENT_TYPE_LATEST

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/stats")
async def get_stats():
    return performance_monitor.get_performance_stats()

@router.get("/metrics")
async def get_metrics():
    metrics_data = performance_monitor.get_prometheus_metrics()
    return Response(metrics_data, media_type=CONTENT_TYPE_LATEST)
