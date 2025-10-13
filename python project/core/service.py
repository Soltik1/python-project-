# core/service.py
"""Сервисный слой домена для работы с неизменяемыми кортежами задач.

Функции ниже — это тонкие, намерение-объясняющие обёртки над чистыми
трансформациями из `core.transforms`, а также небольшие вспомогательные
операции, используемые отчетами и UI.
"""

from core.domain import Task, Project, User
from typing import Tuple, Optional, List, Dict
from datetime import datetime
from .transforms import add_task, filter_by_status, avg_tasks_per_user

def create_task(tasks: Tuple[Task, ...], new_task: Task) -> Tuple[Task, ...]:
    """Вернуть новый кортеж с добавленной задачей `new_task`, не изменяя вход."""
    return add_task(tasks, new_task)

def change_status(tasks: Tuple[Task, ...], task_id: str, new_status: str) -> Tuple[Task, ...]:
    """Неизменяемо изменить статус задачи с ID `task_id`.

    Если задача не найдена — исходный объект сохраняется без изменений.
    Поле `updated` обновляется у изменённой задачи.
    """
    updated = []
    for t in tasks:
        if t.id == task_id:
            updated.append(Task(
                id=t.id,
                project_id=t.project_id,
                title=t.title,
                desc=t.desc,
                status=new_status,
                priority=t.priority,
                assignee=t.assignee,
                created=t.created,
                updated=datetime.utcnow().isoformat()
            ))
        else:
            updated.append(t)
    return tuple(updated)

def project_overview(tasks: Tuple[Task, ...], project_id: str) -> Dict[str, int]:
    """Агрегировать количество задач по статусам для указанного проекта."""
    tasks_in = [t for t in tasks if t.project_id == project_id]
    counts = {"total": len(tasks_in)}
    for s in ("todo", "in_progress", "review", "done"):
        counts[s] = len([t for t in tasks_in if t.status == s])
    return counts

def avg_tasks_per_user_report(tasks: Tuple[Task, ...]) -> float:
    """Удобная обёртка: среднее количество задач на пользователя."""
    return avg_tasks_per_user(tasks)
