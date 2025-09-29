# core/domain.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class Project:
    id: str
    name: str
    owner: str

@dataclass(frozen=True)
class User:
    id: str
    name: str
    role: str

@dataclass(frozen=True)
class Task:
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
    id: str
    task_id: str
    author: str
    text: str
    ts: str

@dataclass(frozen=True)
class Event:
    id: str
    ts: str
    name: str
    payload: Dict[str, Any]
