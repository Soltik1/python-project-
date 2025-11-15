# core/transforms.py
# Лабораторная работа #1: Чистые функции + иммутабельность + HOF
from typing import Tuple, Callable, Dict, TYPE_CHECKING
from .domain import Task, Comment, Project, User
from functools import lru_cache, reduce
from datetime import datetime
import operator

if TYPE_CHECKING:
    from .ftypes import Maybe, Either











# === Лаба1: Чистые функции + иммутабельность + HOF ===

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
    Использует функциональный подход с reduce и именованной функцией.

    1. Извлекаем всех исполнителей задач
    2. Используем reduce для подсчета задач по пользователям через именованную функцию
    3. Вычисляем среднее количество задач на пользователя
    """
    assigned = [t.assignee for t in tasks if t.assignee]
    if not assigned:
        return 0.0
    
    def count_assignee(acc: Dict[str, int], assignee: str) -> Dict[str, int]:
        """Именованная функция для подсчета задач по исполнителям"""
        return {**acc, assignee: acc.get(assignee, 0) + 1}
    
    # Используем reduce для подсчета задач по пользователям
    user_counts = reduce(count_assignee, assigned, {})
    
    # Используем reduce для вычисления среднего
    total_tasks = reduce(operator.add, user_counts.values(), 0)
    return total_tasks / len(user_counts) if user_counts else 0.0
    













# === Лаба2: Лямбда и замыкания + рекурсия ===

# Замыкания-фильтры
def by_priority(priority: str) -> Callable[[Task], bool]:
    """
    Замыкание для фильтрации задач по приоритету.
    Возвращает лямбда-функцию-предикат.

    1. Функция принимает параметр (например high)
    2. Возвращает лямбда-функцию, которая запоминает значение priority
    3. Лямбда проверяет, совпадает ли приоритет задачи с заданным
    """
    return lambda task: task.priority == priority


def by_assignee(user_id: str) -> Callable[[Task], bool]:
    """
    Замыкание для фильтрации задач по исполнителю.
    Возвращает лямбда-функцию-предикат.
    
    1. Функция принимает user_id (например "u1")
    2. Возвращает лямбда-функцию, которая запоминает значение user_id
    3. Лямбда проверяет, совпадает ли исполнитель задачи с заданным
    """
    return lambda task: task.assignee == user_id


def by_date_range(start_iso: str, end_iso: str) -> Callable[[Task], bool]:
    """
    Замыкание для фильтрации задач по диапазону дат.
    Возвращает лямбда-функцию-предикат.

    1. Функция принимает даты в ISO формате ("2024-01-01T00:00:00")
    2. Преобразует строки в объекты datetime
    3. Возвращает лямбда-функцию, которая запоминает значения start и end
    4. Лямбда проверяет, попадает ли дата создания задачи в диапазон
    """
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    
    return lambda task: start <= datetime.fromisoformat(task.created) <= end


# Рекурсивные функции
def walk_comments(comments: Tuple[Comment, ...], task_id: str, idx: int = 0) -> Tuple[Comment, ...]:
    """
    Рекурсивная функция для поиска комментариев по ID задачи.
    Использует рекурсию с индексом для обхода кортежа.
    Демонстрирует использование лямбды для проверки условия.

    1. Базовый случай: Если idx >= len(comments) - возвращаем пустой кортеж
    2. Рекурсивный случай:
        Берем текущий элемент: head = comments[idx]
        Рекурсивно обрабатываем остальные элементы: tail = walk_comments(comments, task_id, idx + 1)
        Используем лямбду для проверки условия: lambda c: c.task_id == task_id
        Если текущий комментарий принадлежит нужной задаче: return (head,) + tail
        Иначе: return tail
    """
    if idx >= len(comments):
        return tuple()
    
    head = comments[idx]
    tail = walk_comments(comments, task_id, idx + 1)
    
    # Используем лямбду для проверки условия
    is_target_task = lambda comment: comment.task_id == task_id
    
    if is_target_task(head):
        return (head,) + tail
    return tail


def traverse_tasks(tasks: Tuple[Task, ...], status_order: Tuple[str, ...], idx: int = 0) -> Tuple[str, ...]:
    """
    Рекурсивная функция для обхода задач в определенном порядке статусов.
    Возвращает кортеж ID задач в указанном порядке статусов.
    Демонстрирует использование лямбды для проверки статуса.

    1. Базовый случай: Если idx >= len(tasks) - возвращаем пустой кортеж
    2. Рекурсивный случай:
        Берем текущую задачу: head = tasks[idx]
        Рекурсивно обрабатываем остальные: tail = traverse_tasks(tasks, status_order, idx + 1)
        Используем лямбду для проверки статуса: lambda s: s in status_order
        Если статус задачи входит в status_order: return (head.id,) + tail
        Иначе: return tail
    """
    if idx >= len(tasks):
        return tuple()
    
    head = tasks[idx]
    tail = traverse_tasks(tasks, status_order, idx + 1)
    
    # Используем лямбду для проверки статуса
    is_valid_status = lambda status: status in status_order
    
    if is_valid_status(head.status):
        return (head.id,) + tail
    return tail

    """UI: Фильтры задач в Streamlit находятся в app/main.py в функции show_lab2_filters_page (517)"""














# === Лаба3: Продвинутая рекурсия + мемоизация ===

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

















# === Лаба4: Функциональные паттерны Maybe/Either ===

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
