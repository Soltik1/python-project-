import pytest
import time
from datetime import datetime, timedelta
from core.domain import Task
from core.transforms import overdue_tasks, measure_cache_performance
from core.report import overdue_tasks_report_cached, performance_comparison_report


def make_task(idx: int, status: str = "todo", priority: str = "medium", created_dt: datetime | None = None) -> Task:
    dt = created_dt or datetime.utcnow() - timedelta(days=10)
    iso = dt.isoformat()
    return Task(
        id=f"t{idx}",
        project_id="p1",
        title=f"Task {idx}",
        desc="Desc",
        status=status,
        priority=priority,
        assignee=None,
        created=iso,
        updated=iso,
    )


def test_overdue_tasks_applies_rules():
    now = datetime.utcnow()
    tasks = (
        make_task(1, status="todo", created_dt=now - timedelta(days=8)),
        make_task(2, status="done", created_dt=now - timedelta(days=20)),
        make_task(3, status="todo", priority="critical", created_dt=now - timedelta(days=4)),
        make_task(4, status="todo", created_dt=now - timedelta(days=2)),
    )
    rules = ("overdue_7_days", "critical_overdue")
    result = overdue_tasks(tasks, rules)
    assert set(t.id for t in result) == {"t1", "t3"}


def test_overdue_tasks_cached_same_result_second_call_is_fast():
    now = datetime.utcnow()
    tasks = (
        make_task(1, status="todo", created_dt=now - timedelta(days=9)),
        make_task(2, status="todo", created_dt=now - timedelta(days=1)),
    )
    rules = ("overdue_7_days",)

    # первый вызов
    start = time.time()
    r1 = overdue_tasks(tasks, rules)
    t1 = time.time() - start

    # второй вызов (должен быть быстрее за счет кэша)
    start = time.time()
    r2 = overdue_tasks(tasks, rules)
    t2 = time.time() - start

    assert r1 == r2
    assert t2 <= t1  # должно быть не медленнее


def test_measure_cache_performance_helper_times_function():
    timer = measure_cache_performance()

    def slow_add(a, b):
        time.sleep(0.01)
        return a + b

    (res, elapsed) = timer(slow_add, 2, 3)
    assert res == 5
    assert elapsed >= 0.01


def test_overdue_tasks_report_cached_delegates_to_function():
    tasks = (
        make_task(1),
        make_task(2, status="done"),
    )
    rules = ("overdue_7_days",)
    result = overdue_tasks_report_cached(tasks, rules)
    # не должно падать и возвращать кортеж
    assert isinstance(result, tuple)


def test_performance_comparison_report_has_better_second_call():
    tasks = (
        make_task(1),
        make_task(2),
    )
    rules = ("overdue_7_days",)
    report = performance_comparison_report(tasks, rules)
    assert report["results_identical"] is True
    # второй вызов обычно быстрее (может быть равным в среде CI)
    assert report["second_call_time"] <= report["first_call_time"]
