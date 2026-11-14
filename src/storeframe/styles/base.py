"""What a style is: a set of layouts plus decorations drawn under and over the device."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from PIL import Image

from ..devices import Placed
from ..layout import FEATURE_GRAPHIC, Layout

if TYPE_CHECKING:
    from ..design import Design, Screen


@dataclass
class Context:
    """Everything a style needs to decorate one picture."""
    design: Design
    screen: Screen
    kind: str                 # device kind key, e.g. "phone", "iphone"
    locale: str
    order: int                # position of this screen in the gallery
    count: int                # how many screens the gallery has
    layout: Layout
    params: dict[str, Any] = field(default_factory=dict)
    placed: Placed | None = None   # set before ``over`` is called


# Centred device, headline above. Tuned for current flagship phones and tablets.
CENTRED: dict[str, Layout] = {
    "phone": Layout(headline_top=0.045, headline_size=0.064, headline_width=0.86, headline_leading=1.08,
                    screen_top=0.205, screen_width=0.640, foot=0.040),
    "tablet": Layout(headline_top=0.055, headline_size=0.056, headline_width=0.80, headline_leading=1.08,
                     screen_top=0.230, screen_width=0.760, foot=0.040),
    "iphone": Layout(headline_top=0.060, headline_size=0.072, headline_width=0.86, headline_leading=1.08,
                     screen_top=0.235, screen_width=0.660, foot=0.045),
    "ipad": Layout(headline_top=0.060, headline_size=0.054, headline_width=0.80, headline_leading=1.08,
                   screen_top=0.235, screen_width=0.760, foot=0.050),
}


class Style:
    name = "plain"
    layouts: ClassVar[dict[str, Layout]] = CENTRED
    feature_layout: ClassVar[Layout] = FEATURE_GRAPHIC
    # per device kind, numbers the decorations use (fractions of the canvas)
    params: ClassVar[dict[str, dict[str, Any]]] = {}
    feature_params: ClassVar[dict[str, Any]] = {}

    def layout_for(self, kind: str) -> Layout:
        if kind in self.layouts:
            return self.layouts[kind]
        return self.layouts.get("phone") or next(iter(self.layouts.values()))

    def params_for(self, kind: str) -> dict[str, Any]:
        if kind in self.params:
            return dict(self.params[kind])
        return dict(self.params.get("phone", {}))

    def under(self, canvas: Image.Image, ctx: Context) -> None:
        """Draw behind the device (after the background)."""

    def over(self, canvas: Image.Image, ctx: Context) -> None:
        """Draw in front of the device (before the headline)."""

    def feature_under(self, canvas: Image.Image, ctx: Context) -> None:
        """Feature graphic: draw behind the device."""

    def feature_over(self, canvas: Image.Image, ctx: Context) -> None:
        """Feature graphic: draw in front of the device."""
