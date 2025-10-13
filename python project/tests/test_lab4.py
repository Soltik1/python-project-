import pytest
from core.domain import Task
from core.ftypes import Some, Nothing, Left, Right, maybe_from_optional, either_from_exception, safe_divide
from core.transforms import safe_task, validate_task, create_task_pipeline, add_task
from core.report import safe_task_report, validation_report, pipeline_report


def make_task(idx: int, title: str = "Ok title", desc: str = "Long enough desc", status: str = "todo", priority: str = "medium", assignee: str | None = None):
    return Task(
        id=f"t{idx}",
        project_id="p1",
        title=title,
        desc=desc,
        status=status,
        priority=priority,
        assignee=assignee,
        created="2024-01-01T00:00:00",
        updated="2024-01-01T00:00:00",
    )


def test_maybe_basic_some_nothing():
    s = Some(10)
    n = Nothing()
    assert s.is_some() and not s.is_none()
    assert not n.is_some() and n.is_none()
    assert s.map(lambda x: x + 1).get_or_else(0) == 11
    assert n.map(lambda x: x).get_or_else(42) == 42


def test_either_basic_left_right():
    r = Right(5)
    l = Left({"err": "boom"})
    assert r.is_right() and not r.is_left()
    assert l.is_left() and not l.is_right()
    assert isinstance(r.map(lambda x: x * 2), Right)
    assert isinstance(l.map(lambda x: x * 2), Left)


def test_safe_helpers_maybe_and_either():
    assert isinstance(maybe_from_optional(1), Some)
    assert isinstance(maybe_from_optional(None), Nothing)

    ok = either_from_exception(lambda: 2 + 2)
    bad = either_from_exception(lambda: (_ for _ in ()).throw(ValueError("x")))
    assert ok.is_right()
    assert bad.is_left()

    assert safe_divide(4, 2).is_right()
    assert safe_divide(1, 0).is_left()


def test_safe_task_returns_some_or_nothing():
    tasks = (make_task(1), make_task(2))
    assert safe_task(tasks, "t2").is_some()
    assert safe_task(tasks, "t404").is_none()


def test_validate_task_rules_and_errors():
    t_invalid = make_task(1, title="", desc="short", status="bad", priority="weird")
    rules = ("title_min_length", "desc_min_length", "assignee_required")
    result = validate_task(t_invalid, rules)
    assert result.is_left()
    err = result.map_left(lambda e: e).map(lambda x: x)  # keep Either shape
    assert result.is_left()

    t_valid = make_task(2, title="ABC", desc="0123456789X", status="todo", priority="low")
    result_ok = validate_task(t_valid, rules)
    assert result_ok.is_right()


def test_create_task_pipeline_adds_only_valid():
    tasks = (make_task(1),)
    rules = ("title_min_length", "desc_min_length", "assignee_required")

    invalid = make_task(2, title="No", desc="short", status="in_progress", assignee=None)
    valid = make_task(3, title="Good", desc="0123456789X", status="todo")

    r1 = create_task_pipeline(tasks, invalid, rules)
    r2 = create_task_pipeline(tasks, valid, rules)

    assert r1.is_left()
    assert r2.is_right()
    new_tasks = r2.get_or_else(())
    assert len(new_tasks) == 2 and any(t.id == "t3" for t in new_tasks)


def test_safe_task_report_mix_some_and_nothing():
    tasks = (make_task(1), make_task(2))
    report = safe_task_report(tasks, ["t1", "tX"])
    assert report["t1"].is_some()
    assert report["tX"].is_none()


def test_validation_report_collects_eithers():
    tasks = (
        make_task(1, title="Okay", desc="0123456789X", status="todo", priority="low"),
        make_task(2, title="", desc="bad", status="bad", priority="bad"),
    )
    rules = ("title_min_length", "desc_min_length")
    report = validation_report(tasks, rules)
    assert report["t1"].is_right()
    assert report["t2"].is_left()


def test_pipeline_report_accumulates_results_and_updates_state():
    tasks = (make_task(1),)
    new_tasks = [
        make_task(2, title="No", desc="short", status="in_progress", assignee=None),  # invalid
        make_task(3, title="Good", desc="0123456789X", status="todo"),  # valid
        make_task(4, title="Good2", desc="0123456789Y", status="todo"),  # valid
    ]
    rules = ("title_min_length", "desc_min_length", "assignee_required")

    results = pipeline_report(tasks, new_tasks, rules)
    assert len(results) == 3
    assert results[0].is_left()
    assert results[1].is_right()
    assert results[2].is_right()
