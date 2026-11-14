"""Where things sit on the canvas.

All values are fractions of the canvas, so one layout serves any canvas size:
positions *down* are fractions of the height; sizes and positions *across* are
fractions of the width. A taller canvas gives everything more room without
stretching any of it.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Layout:
    # The headline: shrunk from ``headline_size`` until every line fits ``headline_width``.
    headline_top: float = 0.05
    headline_size: float = 0.064
    headline_width: float = 0.86
    headline_leading: float = 1.06
    headline_middle: float = 0.5        # horizontal centre of the headline
    # The device's screen. ``screen_width`` is as wide as it may be; ``foot`` (the
    # ground left under the device body) is the other limit. ``screen_left`` of
    # None centres the device.
    screen_top: float = 0.205
    screen_width: float = 0.64
    foot: float = 0.04
    screen_left: float | None = None

    def updated(self, overrides: dict[str, Any] | None) -> Layout:
        """A copy with some fields replaced; unknown keys are an error."""
        if not overrides:
            return self
        names = {field.name for field in dataclasses.fields(self)}
        unknown = set(overrides) - names
        if unknown:
            raise ValueError(f"unknown layout keys: {', '.join(sorted(unknown))}")
        return dataclasses.replace(self, **overrides)


# The landscape Google Play feature graphic: copy on the left, the phone on the right.
FEATURE_GRAPHIC = Layout(
    headline_top=0.105,
    headline_size=0.046,
    headline_width=0.42,
    headline_leading=1.18,
    headline_middle=0.315,
    screen_left=0.700,
    screen_top=0.100,
    screen_width=0.175,
    foot=0.070,
)
