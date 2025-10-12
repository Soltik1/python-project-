# core/report.py
# Отчеты и аналитика для всех лабораторных работ
from typing import Tuple, Dict, List, Any
from .domain import Task, Project, User, Comment
from .transforms import (
    avg_tasks_per_user, 
    filter_by_status, 
    overdue_tasks,
    by_priority,
    by_assignee,
    by_date_range
)
from .ftypes import Maybe, Some, Nothing, Either, Right, Left

# === Лаба #1: Overview отчеты ===

def overview_stats(projects: Tuple[Project, ...], users: Tuple[User, ...], tasks: Tuple[Task, ...]) -> Dict[str, Any]:
    """
    Основная статистика: количество проектов, задач, пользователей и распределение по статусам.
    """
    status_counts = {}
    for status in ("todo", "in_progress", "review", "done"):
        status_counts[status] = len(filter_by_status(tasks, status))
    
    return {
        "projects_count": len(projects),
        "users_count": len(users),
        "tasks_count": len(tasks),
        "status_distribution": status_counts,
        "avg_tasks_per_user": avg_tasks_per_user(tasks)
    }

def project_overview_report(tasks: Tuple[Task, ...], project_id: str) -> Dict[str, int]:
    """
    Детальный отчет по проекту.
    """
    tasks_in_project = tuple(t for t in tasks if t.project_id == project_id)
    
    counts = {
        "total": len(tasks_in_project),
        "todo": len(filter_by_status(tasks_in_project, "todo")),
        "in_progress": len(filter_by_status(tasks_in_project, "in_progress")),
        "review": len(filter_by_status(tasks_in_project, "review")),
        "done": len(filter_by_status(tasks_in_project, "done"))
    }
    
    return counts

# === Лаба #2: Фильтры и отчеты ===

def filtered_tasks_report(tasks: Tuple[Task, ...], filters: Dict[str, Any]) -> Tuple[Task, ...]:
    """
    Отчет с применением фильтров через замыкания.
    """
    filtered = tasks
    
    # Применяем фильтры последовательно
    if "priority" in filters:
        priority_filter = by_priority(filters["priority"])
        filtered = tuple(t for t in filtered if priority_filter(t))
    
    if "assignee" in filters:
        assignee_filter = by_assignee(filters["assignee"])
        filtered = tuple(t for t in filtered if assignee_filter(t))
    
    if "date_range" in filters:
        start_date = filters["date_range"]["start"]
        end_date = filters["date_range"]["end"]
        date_filter = by_date_range(start_date, end_date)
        filtered = tuple(t for t in filtered if date_filter(t))
    
    return filtered

def user_workload_report(tasks: Tuple[Task, ...], users: Tuple[User, ...]) -> Dict[str, Dict[str, int]]:
    """
    Отчет по загрузке пользователей.
    """
    workload = {}
    
    for user in users:
        user_tasks = tuple(t for t in tasks if t.assignee == user.id)
        workload[user.name] = {
            "total": len(user_tasks),
            "todo": len(filter_by_status(user_tasks, "todo")),
            "in_progress": len(filter_by_status(user_tasks, "in_progress")),
            "review": len(filter_by_status(user_tasks, "review")),
            "done": len(filter_by_status(user_tasks, "done"))
        }
    
    return workload

# === Лаба #3: Кэшированные отчеты ===

def overdue_tasks_report_cached(tasks: Tuple[Task, ...], rules: Tuple[str, ...]) -> Tuple[Task, ...]:
    """
    Кэшированный отчет просроченных задач.
    Использует мемоизацию для повышения производительности.
    """
    return overdue_tasks(tasks, rules)

def performance_comparison_report(tasks: Tuple[Task, ...], rules: Tuple[str, ...]) -> Dict[str, Any]:
    """
    Сравнение производительности с кэшем и без.
    """
    import time
    
    # Первый вызов (без кэша)
    start_time = time.time()
    result1 = overdue_tasks(tasks, rules)
    first_call_time = time.time() - start_time
    
    # Второй вызов (с кэшем)
    start_time = time.time()
    result2 = overdue_tasks(tasks, rules)
    second_call_time = time.time() - start_time
    
    return {
        "first_call_time": first_call_time,
        "second_call_time": second_call_time,
        "cache_improvement": first_call_time / second_call_time if second_call_time > 0 else float('inf'),
        "overdue_tasks_count": len(result1),
        "results_identical": result1 == result2
    }

# === Лаба #4: Отчеты с Maybe/Either ===

def safe_task_report(tasks: Tuple[Task, ...], task_ids: List[str]) -> Dict[str, Maybe[Task]]:
    """
    Безопасный отчет по задачам с использованием Maybe.
    """
    from .transforms import safe_task
    
    report = {}
    for task_id in task_ids:
        report[task_id] = safe_task(tasks, task_id)
    
    return report

def validation_report(tasks: Tuple[Task, ...], rules: Tuple[str, ...]) -> Dict[str, Either[dict, Task]]:
    """
    Отчет валидации задач с использованием Either.
    """
    from .transforms import validate_task
    
    report = {}
    for task in tasks:
        report[task.id] = validate_task(task, rules)
    
    return report

def pipeline_report(tasks: Tuple[Task, ...], new_tasks: List[Task], rules: Tuple[str, ...]) -> List[Either[dict, Tuple[Task, ...]]]:
    """
    Отчет по пайплайну создания задач.
    """
    from .transforms import create_task_pipeline
    
    results = []
    current_tasks = tasks
    
    for new_task in new_tasks:
        result = create_task_pipeline(current_tasks, new_task, rules)
        results.append(result)
        
        # Если задача успешно добавлена, обновляем текущий список
        if result.is_right():
            current_tasks = result.get_or_else(tasks)
    
    return results

# === Общие утилиты для отчетов ===

def generate_summary_report(projects: Tuple[Project, ...], users: Tuple[User, ...], tasks: Tuple[Task, ...]) -> Dict[str, Any]:
    """
    Генерирует сводный отчет по всем данным.
    """
    overview = overview_stats(projects, users, tasks)
    
    # Добавляем информацию о проектах
    project_stats = {}
    for project in projects:
        project_stats[project.name] = project_overview_report(tasks, project.id)
    
    # Добавляем информацию о пользователях
    user_workload = user_workload_report(tasks, users)
    
    # Добавляем информацию о просроченных задачах
    overdue_rules = ("overdue_7_days", "critical_overdue")
    overdue = overdue_tasks_report_cached(tasks, overdue_rules)
    
    return {
        "overview": overview,
        "project_stats": project_stats,
        "user_workload": user_workload,
        "overdue_tasks": {
            "count": len(overdue),
            "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in overdue]
        }
    }
