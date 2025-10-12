# core/transforms.py
# Лабораторная работа #1: Чистые функции + иммутабельность + HOF
from typing import Tuple, Callable, TYPE_CHECKING
from .domain import Task, Comment, Project, User
from functools import lru_cache, reduce
from datetime import datetime
import operator

if TYPE_CHECKING:
    from .ftypes import Maybe, Either

# === Лаба #1: Чистые функции + иммутабельность + HOF ===

def add_task(tasks: Tuple[Task, ...], t: Task) -> Tuple[Task, ...]:
    """
    Чистая функция для добавления задачи в иммутабельный кортеж задач.
    Возвращает новый кортеж без изменения исходного.
    """
    return tasks + (t,)

def filter_by_status(tasks: Tuple[Task, ...], status: str) -> Tuple[Task, ...]:
    """
    Чистая функция для фильтрации задач по статусу.
    Возвращает новый кортеж с отфильтрованными задачами.
    """
    return tuple(t for t in tasks if t.status == status)

def avg_tasks_per_user(tasks: Tuple[Task, ...]) -> float:
    """
    Чистая функция для вычисления среднего количества задач на пользователя.
    Использует функциональный подход с reduce.
    """
    assigned = [t.assignee for t in tasks if t.assignee]
    if not assigned:
        return 0.0
    
    # Используем reduce для подсчета задач по пользователям
    user_counts = reduce(
        lambda acc, assignee: {**acc, assignee: acc.get(assignee, 0) + 1},
        assigned,
        {}
    )
    
    # Используем reduce для вычисления среднего
    total_tasks = reduce(operator.add, user_counts.values(), 0)
    return total_tasks / len(user_counts) if user_counts else 0.0
    
# === Лаба #2: Лямбда и замыкания + рекурсия ===

# Замыкания-фильтры
def by_priority(priority: str) -> Callable[[Task], bool]:
    """
    Замыкание для фильтрации задач по приоритету.
    Возвращает функцию-предикат.
    """
    def _pred(task: Task) -> bool:
        return task.priority == priority
    return _pred

def by_assignee(user_id: str) -> Callable[[Task], bool]:
    """
    Замыкание для фильтрации задач по исполнителю.
    Возвращает функцию-предикат.
    """
    def _pred(task: Task) -> bool:
        return task.assignee == user_id
    return _pred

def by_date_range(start_iso: str, end_iso: str) -> Callable[[Task], bool]:
    """
    Замыкание для фильтрации задач по диапазону дат.
    Возвращает функцию-предикат.
    """
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    
    def _pred(task: Task) -> bool:
        created = datetime.fromisoformat(task.created)
        return start <= created <= end
    return _pred

# Рекурсивные функции
def walk_comments(comments: Tuple[Comment, ...], task_id: str, idx: int = 0) -> Tuple[Comment, ...]:
    """
    Рекурсивная функция для поиска комментариев по ID задачи.
    Использует рекурсию с индексом для обхода кортежа.
    """
    if idx >= len(comments):
        return tuple()
    
    head = comments[idx]
    tail = walk_comments(comments, task_id, idx + 1)
    
    if head.task_id == task_id:
        return (head,) + tail
    return tail

def traverse_tasks(tasks: Tuple[Task, ...], status_order: Tuple[str, ...], idx: int = 0) -> Tuple[str, ...]:
    """
    Рекурсивная функция для обхода задач в определенном порядке статусов.
    Возвращает кортеж ID задач в указанном порядке статусов.
    """
    if idx >= len(tasks):
        return tuple()
    
    head = tasks[idx]
    tail = traverse_tasks(tasks, status_order, idx + 1)
    
    # Проверяем, есть ли текущий статус в порядке статусов
    if head.status in status_order:
        return (head.id,) + tail
    return tail

# === Лаба #3: Продвинутая рекурсия + мемоизация ===

# Дорогая функция с кэшированием
@lru_cache(maxsize=128)
def overdue_tasks(tasks: Tuple[Task, ...], rules: Tuple[str, ...]) -> Tuple[Task, ...]:
    """
    Дорогая функция для подсчета просроченных задач по SLA.
    Использует мемоизацию для кэширования результатов.
    """
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    overdue = []
    
    for task in tasks:
        try:
            created = datetime.fromisoformat(task.created)
            days_passed = (now - created).days
            
            # Проверяем правила SLA
            for rule in rules:
                if rule == "overdue_7_days" and days_passed > 7 and task.status != "done":
                    overdue.append(task)
                    break
                elif rule == "overdue_14_days" and days_passed > 14 and task.status != "done":
                    overdue.append(task)
                    break
                elif rule == "critical_overdue" and task.priority == "critical" and days_passed > 3:
                    overdue.append(task)
                    break
        except Exception:
            continue
    
    return tuple(overdue)

def measure_cache_performance():
    """
    Функция для замера производительности до/после кэша.
    """
    import time
    
    def time_function(func, *args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, end - start
    
    return time_function

# === Лаба #4: Функциональные паттерны Maybe/Either ===

def safe_task(tasks: Tuple[Task, ...], tid: str) -> 'Maybe[Task]':
    """
    Безопасное получение задачи по ID с использованием Maybe.
    Возвращает Some(task) если задача найдена, иначе Nothing().
    """
    from .ftypes import Some, Nothing
    
    for task in tasks:
        if task.id == tid:
            return Some(task)
    return Nothing()

def validate_task(t: Task, rules: Tuple[str, ...]) -> 'Either[dict, Task]':
    """
    Валидация задачи по правилам с использованием Either.
    Возвращает Right(task) если валидация прошла, иначе Left(ошибки).
    """
    from .ftypes import Right, Left
    
    errors = []
    
    # Проверка обязательных полей
    if not t.title or t.title.strip() == "":
        errors.append("Title is required")
    
    if not t.desc or t.desc.strip() == "":
        errors.append("Description is required")
    
    # Проверка статуса
    valid_statuses = ("todo", "in_progress", "review", "done")
    if t.status not in valid_statuses:
        errors.append(f"Invalid status: {t.status}. Must be one of {valid_statuses}")
    
    # Проверка приоритета
    valid_priorities = ("low", "medium", "high", "critical")
    if t.priority not in valid_priorities:
        errors.append(f"Invalid priority: {t.priority}. Must be one of {valid_priorities}")
    
    # Дополнительные правила валидации
    for rule in rules:
        if rule == "title_min_length" and len(t.title) < 3:
            errors.append("Title must be at least 3 characters long")
        elif rule == "desc_min_length" and len(t.desc) < 10:
            errors.append("Description must be at least 10 characters long")
        elif rule == "assignee_required" and t.status == "in_progress" and not t.assignee:
            errors.append("Assignee is required for tasks in progress")
    
    if errors:
        return Left({"errors": errors, "task_id": t.id})
    
    return Right(t)

def create_task_pipeline(tasks: Tuple[Task, ...], new_task: Task, rules: Tuple[str, ...]) -> 'Either[dict, Tuple[Task, ...]]':
    """
    Пайплайн для создания задачи: создать задачу → проверить правила → сохранить.
    Использует функциональные паттерны Maybe/Either.
    """
    from .ftypes import Right, Left
    
    # Шаг 1: Валидация задачи
    validation_result = validate_task(new_task, rules)
    
    # Шаг 2: Если валидация прошла, добавляем задачу
    def add_validated_task(task: Task) -> Tuple[Task, ...]:
        return add_task(tasks, task)
    
    return validation_result.map(add_validated_task)
