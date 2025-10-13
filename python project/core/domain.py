# core/domain.py
"""Доменные сущности приложения (неизменяемые dataclass)."""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class Project:
    """Проект: идентификатор, название и владелец."""
    id: str
    name: str
    owner: str

@dataclass(frozen=True)
class User:
    """Пользователь с ролью (для отчетов/назначений)."""
    id: str
    name: str
    role: str

@dataclass(frozen=True)
class Task:
    """Задача в рамках проекта.

    Статус: todo | in_progress | review | done
    Приоритет: low | medium | high | critical
    """
    id: str
    project_id: str
    title: str
    desc: str
    status: str  # todo / in_progress / review / done
    priority: str  # low / medium / high / critical
    assignee: Optional[str]
    created: str
    updated: str

@dataclass(frozen=True)
class Comment:
    """Комментарий пользователя к задаче."""
    id: str
    task_id: str
    author: str
    text: str
    ts: str

@dataclass(frozen=True)
class Event:
    """Событие EventBus с произвольной нагрузкой (payload)."""
    id: str
    ts: str
    name: str
    payload: Dict[str, Any]
