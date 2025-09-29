# core/service.py
from core.domain import Task, Project, User
from typing import Tuple, Optional, List, Dict
from datetime import datetime
from .transforms import add_task, filter_by_status, avg_tasks_per_user

def create_task(tasks: Tuple[Task, ...], new_task: Task) -> Tuple[Task, ...]:
    return add_task(tasks, new_task)

def change_status(tasks: Tuple[Task, ...], task_id: str, new_status: str) -> Tuple[Task, ...]:
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
    tasks_in = [t for t in tasks if t.project_id == project_id]
    counts = {"total": len(tasks_in)}
    for s in ("todo", "in_progress", "review", "done"):
        counts[s] = len([t for t in tasks_in if t.status == s])
    return counts

def avg_tasks_per_user_report(tasks: Tuple[Task, ...]) -> float:
    return avg_tasks_per_user(tasks)
