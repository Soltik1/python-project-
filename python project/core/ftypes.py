# core/ftypes.py
# Лабораторная работа #4: Функциональные паттерны Maybe/Either
from typing import TypeVar, Generic, Callable, Union, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')

# === Maybe (Option) Pattern ===

class Maybe(Generic[T], ABC):
    """Базовый класс для Maybe паттерна"""
    
    @abstractmethod
    def is_some(self) -> bool:
        """Проверяет, содержит ли Maybe значение"""
        pass
    
    @abstractmethod
    def is_none(self) -> bool:
        """Проверяет, пустой ли Maybe"""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[T], U]) -> 'Maybe[U]':
        """Применяет функцию к значению, если оно есть"""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        """Применяет функцию, возвращающую Maybe, если значение есть"""
        pass
    
    @abstractmethod
    def get_or_else(self, default: T) -> T:
        """Возвращает значение или значение по умолчанию"""
        pass

class Some(Generic[T], Maybe[T]):
    """Контейнер для существующего значения"""
    
    def __init__(self, value: T):
        self._value = value
    
    def is_some(self) -> bool:
        return True
    
    def is_none(self) -> bool:
        return False
    
    def map(self, f: Callable[[T], U]) -> 'Maybe[U]':
        return Some(f(self._value))
    
    def flat_map(self, f: Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        return f(self._value)
    
    def get_or_else(self, default: T) -> T:
        return self._value
    
    def __repr__(self) -> str:
        return f"Some({self._value})"

class Nothing(Generic[T], Maybe[T]):
    """Контейнер для отсутствующего значения"""
    
    def is_some(self) -> bool:
        return False
    
    def is_none(self) -> bool:
        return True
    
    def map(self, f: Callable[[T], U]) -> 'Maybe[U]':
        return Nothing()
    
    def flat_map(self, f: Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        return Nothing()
    
    def get_or_else(self, default: T) -> T:
        return default
    
    def __repr__(self) -> str:
        return "Nothing()"

# === Either Pattern ===

class Either(Generic[E, T], ABC):
    """Базовый класс для Either паттерна"""
    
    @abstractmethod
    def is_left(self) -> bool:
        """Проверяет, является ли Either Left (ошибкой)"""
        pass
    
    @abstractmethod
    def is_right(self) -> bool:
        """Проверяет, является ли Either Right (успехом)"""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[T], U]) -> 'Either[E, U]':
        """Применяет функцию к значению, если Either содержит Right"""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[T], 'Either[E, U]']) -> 'Either[E, U]':
        """Применяет функцию, возвращающую Either, если Either содержит Right"""
        pass
    
    @abstractmethod
    def map_left(self, f: Callable[[E], E]) -> 'Either[E, T]':
        """Применяет функцию к ошибке, если Either содержит Left"""
        pass

    @abstractmethod
    def get_or_else(self, default: T) -> T:
        """Возвращает значение Right или default, если Left"""
        pass

class Left(Generic[E, T], Either[E, T]):
    """Контейнер для ошибки"""
    
    def __init__(self, error: E):
        self._error = error
    
    def is_left(self) -> bool:
        return True
    
    def is_right(self) -> bool:
        return False
    
    def map(self, f: Callable[[T], U]) -> 'Either[E, U]':
        return Left(self._error)
    
    def flat_map(self, f: Callable[[T], 'Either[E, U]']) -> 'Either[E, U]':
        return Left(self._error)
    
    def map_left(self, f: Callable[[E], E]) -> 'Either[E, T]':
        return Left(f(self._error))
    
    def get_or_else(self, default: T) -> T:
        return default
    
    def __repr__(self) -> str:
        return f"Left({self._error})"

class Right(Generic[E, T], Either[E, T]):
    """Контейнер для успешного значения"""
    
    def __init__(self, value: T):
        self._value = value
    
    def is_left(self) -> bool:
        return False
    
    def is_right(self) -> bool:
        return True
    
    def map(self, f: Callable[[T], U]) -> 'Either[E, U]':
        return Right(f(self._value))
    
    def flat_map(self, f: Callable[[T], 'Either[E, U]']) -> 'Either[E, U]':
        return f(self._value)
    
    def map_left(self, f: Callable[[E], E]) -> 'Either[E, T]':
        return Right(self._value)
    
    def get_or_else(self, default: T) -> T:
        return self._value
    
    def __repr__(self) -> str:
        return f"Right({self._value})"

# === Utility Functions ===

def maybe_from_optional(value: Optional[T]) -> Maybe[T]:
    """Создает Maybe из Optional значения"""
    return Some(value) if value is not None else Nothing()


def either_from_exception(func: Callable[[], T]) -> Either[str, T]:
    """Выполняет функцию и возвращает Either с результатом или ошибкой"""
    try:
        result = func()
        return Right(result)
    except Exception as e:
        return Left(str(e))


def safe_divide(a: float, b: float) -> Either[str, float]:
    """Безопасное деление с Either"""
    if b == 0:
        return Left("Division by zero")
    return Right(a / b)
