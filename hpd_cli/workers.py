"""Simple background task worker using threading + optional Redis queue.

Usage:
    from hpd_cli.workers import async_task, get_task_status

    @async_task
    def my_long_task(param1, param2):
        # ... do work ...
        return result

    # Task runs in background thread
    task_id = my_long_task.delay("value1", "value2")
    status = get_task_status(task_id)  # {"status": "running|done|failed", "result": ...}
"""
import os
import json
import uuid
import time
import threading
import functools
from enum import Enum
from typing import Any, Callable, Optional

from hpd_cli.cache import cache


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# === In-memory task store ==================================

_task_store: dict[str, dict] = {}
_store_lock = threading.Lock()


def _store_result(task_id: str, data: dict):
    """Store task result in Redis (if available) or memory."""
    cache_key = f"task:{task_id}"
    cache.set(cache_key, data, ttl=3600)  # 1h TTL
    # Also keep in memory for fast access
    with _store_lock:
        _task_store[task_id] = data


def _get_result(task_id: str) -> Optional[dict]:
    """Get task result from cache or memory."""
    result = cache.get(f"task:{task_id}")
    if result:
        return result
    with _store_lock:
        return _task_store.get(task_id)


# === Background task decorator =============================

class AsyncTask:
    """Wrapper around a function that can run in background."""

    def __init__(self, func: Callable):
        self.func = func
        functools.update_wrapper(self, func)

    def delay(self, *args, **kwargs) -> str:
        """Execute the function in a background thread."""
        task_id = str(uuid.uuid4())[:8]
        _store_result(task_id, {
            "task_id": task_id,
            "name": self.func.__name__,
            "status": TaskStatus.PENDING,
            "created_at": time.time(),
        })

        thread = threading.Thread(
            target=self._run,
            args=(task_id, args, kwargs),
            daemon=True,
        )
        thread.start()
        return task_id

    def _run(self, task_id: str, args: tuple, kwargs: dict):
        current = _get_result(task_id) or {}
        current["status"] = TaskStatus.RUNNING
        _store_result(task_id, current)
        try:
            result = self.func(*args, **kwargs)
            current = _get_result(task_id) or {}
            current["status"] = TaskStatus.DONE
            current["result"] = result
            current["completed_at"] = time.time()
            _store_result(task_id, current)
        except Exception as e:
            current = _get_result(task_id) or {}
            current["status"] = TaskStatus.FAILED
            current["error"] = str(e)
            current["completed_at"] = time.time()
            _store_result(task_id, current)


def async_task(func: Callable) -> AsyncTask:
    """Decorator to make a function run asynchronously in background."""
    return AsyncTask(func)


# === Status helpers ========================================

def get_task_status(task_id: str) -> Optional[dict]:
    """Get the current status of a background task."""
    return _get_result(task_id)


def list_tasks(limit: int = 10) -> list[dict]:
    """List recent tasks from store."""
    with _store_lock:
        tasks = sorted(
            _task_store.values(),
            key=lambda x: x.get("created_at", 0),
            reverse=True,
        )
        return tasks[:limit]


# === Background health check worker ========================

@async_task
def background_health_check():
    """Run a comprehensive health check in background."""
    from hpd_cli.api.system_checks import (
        is_postgres_active,
        is_docker_running,
        is_deepseek_key_set,
        is_ollama_fallback,
    )
    return {
        "postgres": is_postgres_active(),
        "docker": is_docker_running(),
        "deepseek": is_deepseek_key_set(),
        "ollama": is_ollama_fallback(),
        "timestamp": time.time(),
    }
