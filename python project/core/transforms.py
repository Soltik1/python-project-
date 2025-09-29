# core/transforms.py
from typing import Tuple
from .domain import Task, Comment
from functools import lru_cache
from datetime import datetime

def add_task(tasks: Tuple[Task, ...], t: Task) -> Tuple[Task, ...]:
    return tasks + (t,)

def filter_by_status(tasks: Tuple[Task, ...], status: str) -> Tuple[Task, ...]:
    return tuple(t for t in tasks if t.status == status)

def avg_tasks_per_user(tasks: Tuple[Task, ...]) -> float:
    assigned = [t.assignee for t in tasks if t.assignee]
    if not assigned:
        return 0.0
    user_counts = {}
    for a in assigned:
        user_counts[a] = user_counts.get(a, 0) + 1
    return sum(user_counts.values()) / len(user_counts)
    
# closures
def by_priority(priority: str):
    def _pred(task: Task) -> bool:
        return task.priority == priority
    return _pred

def by_assignee(user_id: str):
    def _pred(task: Task) -> bool:
        return task.assignee == user_id
    return _pred

def by_date_range(start_iso: str, end_iso: str):
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    def _pred(task: Task) -> bool:
        created = datetime.fromisoformat(task.created)
        return start <= created <= end
    return _pred

# recursion for comments
def walk_comments(comments: Tuple[Comment, ...], task_id: str, idx: int = 0) -> Tuple[Comment, ...]:
    if idx >= len(comments):
        return tuple()
    head = comments[idx]
    tail = walk_comments(comments, task_id, idx + 1)
    if head.task_id == task_id:
        return (head,) + tail
    return tail

# expensive function with caching example
@lru_cache(maxsize=128)
def overdue_tasks_tuple(tasks_tuple, days_threshold: int = 7):
    # tasks_tuple is expected to be a tuple of task dict-like items (simple usage)
    from datetime import datetime, timedelta
    res = []
    now = datetime.utcnow()
    for t in tasks_tuple:
        try:
            created = datetime.fromisoformat(t.created)
        except Exception:
            continue
        if (now - created).days > days_threshold and t.status != "done":
            res.append(t)
    return tuple(res)
