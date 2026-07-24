"""Background task management routes."""
from fastapi import APIRouter, HTTPException
from hpd_cli.workers import get_task_status, list_tasks, background_health_check

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/health-check", summary="Ejecutar health check en background")
def run_health_check():
    """Inicia un health check completo en segundo plano."""
    task_id = background_health_check.delay()
    return {
        "task_id": task_id,
        "status": "started",
        "check_url": f"/api/v1/tasks/{task_id}",
    }


@router.get("/{task_id}", summary="Estado de una tarea")
def task_status(task_id: str):
    """Obtiene el estado de una tarea asincrona."""
    result = get_task_status(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return result


@router.get("", summary="Listar tareas recientes")
def list_recent_tasks():
    """Lista las tareas ejecutadas recientemente."""
    return {"tasks": list_tasks(limit=20)}
