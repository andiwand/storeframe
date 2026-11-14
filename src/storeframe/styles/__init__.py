"""Gallery styles: layouts plus the decorations around the device."""

from __future__ import annotations

from .arc import ArcStyle
from .base import CENTRED, Context, Style
from .tabs import TabsStyle

STYLES: dict[str, type[Style]] = {
    "plain": Style,
    "arc": ArcStyle,
    "tabs": TabsStyle,
}


def get(name: str) -> Style:
    try:
        return STYLES[name]()
    except KeyError:
        raise ValueError(f"unknown style {name!r}; one of {', '.join(STYLES)}") from None


__all__ = ["CENTRED", "STYLES", "ArcStyle", "Context", "Style", "TabsStyle", "get"]
