from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from inspect import getdoc
from typing import Callable, Iterable


@dataclass(frozen=True)
class ValidatorInfo:
    name: str
    callable: Callable
    description: str
    layer: str
    examples: tuple[str, ...]


_REGISTRY: "OrderedDict[str, ValidatorInfo]" = OrderedDict()


def register(
    name: str,
    *,
    description: str | None = None,
    layer: str = "field",
    examples: Iterable[str] = (),
):
    def decorator(func):
        info = ValidatorInfo(
            name=name,
            callable=func,
            description=description or getdoc(func) or "No description supplied.",
            layer=layer,
            examples=tuple(examples),
        )
        _REGISTRY[name] = info
        func.validator_name = name
        return func

    return decorator


def register_callable(
    name: str,
    callable_obj: Callable,
    *,
    description: str | None = None,
    layer: str = "field",
    examples: Iterable[str] = (),
):
    info = ValidatorInfo(
        name=name,
        callable=callable_obj,
        description=description or getdoc(callable_obj) or "No description supplied.",
        layer=layer,
        examples=tuple(examples),
    )
    _REGISTRY[name] = info
    callable_obj.validator_name = name
    return callable_obj


def get(name: str):
    return _REGISTRY[name].callable


def info(name: str) -> ValidatorInfo:
    return _REGISTRY[name]


def all_validators() -> list[ValidatorInfo]:
    return list(_REGISTRY.values())


def describe(names: Iterable[str]) -> list[ValidatorInfo]:
    return [info(name) for name in names]
