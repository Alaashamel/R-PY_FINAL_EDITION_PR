from __future__ import annotations

from glob import glob
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.core.redis_client import redis_client
from app.database.session import get_db
from app.models.user import User

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
def monitoring_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    database_status = "healthy"
    redis_status = "healthy"

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database_status = f"unhealthy: {exc.__class__.__name__}"

    try:
        redis_client.client.ping()
    except Exception as exc:
        redis_status = f"unhealthy: {exc.__class__.__name__}"

    overall = "healthy" if database_status == "healthy" and redis_status == "healthy" else "degraded"
    return {
        "status": overall,
        "api": "healthy",
        "database": database_status,
        "redis": redis_status,
        "metrics_endpoint": "/metrics",
    }


@router.get("/recent-errors")
def recent_error_logs(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parents[2]
    log_files = sorted(glob(str(project_root / "logs" / "error_*.log")))
    if not log_files:
        return {"errors": [], "message": "No error log file found yet."}

    latest_file = Path(log_files[-1])
    lines = latest_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {"file": str(latest_file), "errors": lines[-limit:]}


@router.get("/dashboard-summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    return {
        "health": monitoring_health(db),
        "recent_errors": recent_error_logs(limit=10, current_user=current_user),
        "grafana": "http://localhost:3000",
        "prometheus": "http://localhost:9090",
        "metrics": "http://localhost:8000/metrics",
    }
