# core/frp.py
from typing import Callable, Dict, List, Any
from .domain import Event
import uuid
import datetime

class EventBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable[[Event], Any]]] = {}

    def subscribe(self, name: str, handler: Callable[[Event], Any]):
        """Подписка на событие"""
        self._subs.setdefault(name, []).append(handler)

    def publish(self, name: str, payload: dict) -> Event:
        """Публикация события"""
        ev = Event(
            id=str(uuid.uuid4()),
            ts=datetime.datetime.utcnow().isoformat(),
            name=name,
            payload=payload
        )
        handlers = self._subs.get(name, [])
        for h in handlers:
            try:
                h(ev)
            except Exception as e:
                print("Handler error:", e)
        return ev
