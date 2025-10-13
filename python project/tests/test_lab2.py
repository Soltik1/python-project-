import pytest
from datetime import datetime
from core.domain import Task, Comment, User
from core.transforms import (
    by_priority,
    by_assignee,
    by_date_range,
    walk_comments,
    traverse_tasks,
)
from core.report import filtered_tasks_report, user_workload_report


def make_task(idx: int, status: str = "todo", assignee: str | None = None, priority: str = "medium", created: str = "2024-01-01T00:00:00") -> Task:
    return Task(
        id=f"t{idx}",
        project_id="p1",
        title=f"Task {idx}",
        desc="Desc",
        status=status,
        priority=priority,
        assignee=assignee,
        created=created,
        updated=created,
    )


def make_comment(idx: int, task_id: str) -> Comment:
    return Comment(
        id=f"c{idx}", task_id=task_id, author="u1", text="Hi", ts="2024-01-01T00:00:00"
    )


def test_by_priority_filters_correctly():
    tasks = (
        make_task(1, priority="low"),
        make_task(2, priority="high"),
        make_task(3, priority="high"),
    )
    pred = by_priority("high")
    result = tuple(t for t in tasks if pred(t))
    assert [t.id for t in result] == ["t2", "t3"]


def test_by_assignee_filters_correctly():
    tasks = (
        make_task(1, assignee="u1"),
        make_task(2, assignee="u2"),
        make_task(3, assignee="u1"),
    )
    pred = by_assignee("u1")
    result = tuple(t for t in tasks if pred(t))
    assert [t.id for t in result] == ["t1", "t3"]


def test_by_date_range_is_inclusive():
    tasks = (
        make_task(1, created="2024-01-01T00:00:00"),
        make_task(2, created="2024-01-05T00:00:00"),
        make_task(3, created="2024-01-10T00:00:00"),
    )
    pred = by_date_range("2024-01-05T00:00:00", "2024-01-10T00:00:00")
    result = tuple(t for t in tasks if pred(t))
    assert [t.id for t in result] == ["t2", "t3"]


def test_walk_comments_collects_only_for_task():
    comments = (
        make_comment(1, "t1"),
        make_comment(2, "t2"),
        make_comment(3, "t1"),
        make_comment(4, "t3"),
    )
    result = walk_comments(comments, "t1")
    assert [c.id for c in result] == ["c1", "c3"]


def test_traverse_tasks_respects_status_order():
    tasks = (
        make_task(1, status="review"),
        make_task(2, status="in_progress"),
        make_task(3, status="todo"),
        make_task(4, status="done"),
    )
    order = ("todo", "in_progress")
    ids = traverse_tasks(tasks, order)
    assert ids == ("t2", "t3")  # only those in order


def test_filtered_tasks_report_combines_filters():
    tasks = (
        make_task(1, status="todo", priority="high", assignee="u1", created="2024-01-02T00:00:00"),
        make_task(2, status="todo", priority="high", assignee="u2", created="2024-01-03T00:00:00"),
        make_task(3, status="todo", priority="low", assignee="u1", created="2024-01-04T00:00:00"),
    )
    filters = {
        "priority": "high",
        "assignee": "u1",
        "date_range": {"start": "2024-01-01T00:00:00", "end": "2024-01-03T23:59:59"},
    }
    result = filtered_tasks_report(tasks, filters)
    assert [t.id for t in result] == ["t1"]


def test_user_workload_report_counts_by_status():
    tasks = (
        make_task(1, status="todo", assignee="u1"),
        make_task(2, status="in_progress", assignee="u1"),
        make_task(3, status="done", assignee="u1"),
        make_task(4, status="review", assignee="u2"),
    )
    users = (
        User(id="u1", name="Alice", role="dev"),
        User(id="u2", name="Bob", role="qa"),
    )
    report = user_workload_report(tasks, users)
    assert report["Alice"]["total"] == 3
    assert report["Alice"]["todo"] == 1
    assert report["Alice"]["in_progress"] == 1
    assert report["Alice"]["done"] == 1
    assert report["Bob"]["review"] == 1
