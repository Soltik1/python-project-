# core/data_loader.py
import json
import os
from typing import Tuple
from .domain import Project, User, Task, Comment

BASE = os.path.join(os.path.dirname(__file__), "..")
SEED = os.path.join(BASE, "data", "seed.json")

def load_seed() -> Tuple[Tuple[Project, ...], Tuple[User, ...], Tuple[Task, ...], Tuple[Comment, ...]]:
    """
    Загружает seed.json и возвращает кортежи (projects, users, tasks, comments).
    """
    if not os.path.exists(SEED):
        raise FileNotFoundError(f"seed.json not found: {SEED}. Сначала сгенерируй его через scripts/generate_seed.py")

    with open(SEED, "r", encoding="utf-8") as f:
        data = json.load(f)

    projects = tuple(Project(**p) for p in data.get("projects", []))
    users = tuple(User(**u) for u in data.get("users", []))
    tasks = tuple(Task(**t) for t in data.get("tasks", []))
    comments = tuple(Comment(**c) for c in data.get("comments", []))

    return projects, users, tasks, comments