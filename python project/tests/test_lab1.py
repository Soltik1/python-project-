import pytest
from core.domain import Task, Project, User
from core.transforms import add_task, filter_by_status, avg_tasks_per_user
from core.report import overview_stats, project_overview_report


def make_task(idx: int, status: str = "todo", assignee: str | None = None, priority: str = "medium") -> Task:
    return Task(
        id=f"t{idx}",
        project_id="p1",
        title=f"Task {idx}",
        desc="Desc",
        status=status,
        priority=priority,
        assignee=assignee,
        created="2024-01-01T00:00:00",
        updated="2024-01-01T00:00:00",
    )


def test_add_task_returns_new_tuple_immutability():
    tasks = (make_task(1),)
    t2 = make_task(2)
    new_tasks = add_task(tasks, t2)
    assert tasks is not new_tasks
    assert len(tasks) == 1
    assert len(new_tasks) == 2
    assert new_tasks[-1] == t2


def test_filter_by_status_only_matches_requested():
    tasks = (
        make_task(1, status="todo"),
        make_task(2, status="done"),
        make_task(3, status="in_progress"),
        make_task(4, status="todo"),
    )
    only_todo = filter_by_status(tasks, "todo")
    assert all(t.status == "todo" for t in only_todo)
    assert len(only_todo) == 2


def test_avg_tasks_per_user_no_assignees_is_zero():
    tasks = (make_task(1), make_task(2))
    assert avg_tasks_per_user(tasks) == 0.0


def test_avg_tasks_per_user_multiple_users():
    tasks = (
        make_task(1, assignee="u1"),
        make_task(2, assignee="u1"),
        make_task(3, assignee="u2"),
        make_task(4, assignee="u3"),
    )
    # counts: u1=2, u2=1, u3=1 -> avg = 4/3
    assert pytest.approx(avg_tasks_per_user(tasks), rel=1e-9) == 4 / 3


def test_overview_stats_counts_and_distribution():
    projects = (Project(id="p1", name="P1", owner="o1"),)
    users = (User(id="u1", name="U1", role="dev"), User(id="u2", name="U2", role="qa"))
    tasks = (
        make_task(1, status="todo"),
        make_task(2, status="in_progress"),
        make_task(3, status="review"),
        make_task(4, status="done"),
        make_task(5, status="todo"),
    )
    stats = overview_stats(projects, users, tasks)
    assert stats["projects_count"] == 1
    assert stats["users_count"] == 2
    assert stats["tasks_count"] == 5
    assert stats["status_distribution"] == {
        "todo": 2,
        "in_progress": 1,
        "review": 1,
        "done": 1,
    }


def test_project_overview_report_filters_by_project():
    tasks = (
        make_task(1, status="todo"),
        Task(id="t2", project_id="p2", title="x", desc="d", status="done", priority="low", assignee=None, created="2024-01-01T00:00:00", updated="2024-01-01T00:00:00"),
        make_task(3, status="done"),
    )
    report = project_overview_report(tasks, "p1")
    assert report["total"] == 2
    assert report["todo"] == 1
    assert report["done"] == 1


