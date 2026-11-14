"""A dashed arc across the whole gallery, with a sun rising in the first picture
and the moon up in the last. Each picture shows its slice of one large parabola,
so the gallery reads as one continuous image when swiped.

Options (design ``"options"``): ``sun`` and ``moon`` (true/false, default true).
"""

from __future__ import annotations

from typing import ClassVar

from PIL import Image

from ..geometry import Point, path_length
from ..paint import dashed, glowing_disc
from .base import Context, Style

SUN = ((255, 214, 102), (255, 200, 80, 150))
MOON = ((232, 238, 250), (210, 225, 255, 110))
LINE = (255, 255, 255, 220)

_PHONE = {"arc_peak": 0.165, "arc_base": 0.97, "dash_stroke": 0.0060, "dash_on": 0.0240,
          "dash_off": 0.0110, "body_radius": 0.030}
_TABLET = {"arc_peak": 0.180, "arc_base": 0.97, "dash_stroke": 0.0045, "dash_on": 0.0170,
           "dash_off": 0.0075, "body_radius": 0.022}


def arc(params: dict, size: tuple[int, int], order: int, count: int, samples: int = 240) -> list[Point]:
    """Picture ``order`` of ``count``'s slice of the gallery arc, in picture coordinates.

    The parabola is low at the outer edges of the first and last pictures and
    peaks in the middle of the gallery, in the band below the headline.
    """
    width, height = size
    gallery = width * count
    base, peak = params["arc_base"] * height, params["arc_peak"] * height
    points = []
    for step in range(samples + 1):
        x = order * width + width * step / samples
        u = (x - gallery / 2) / (gallery / 2)
        points.append((x - order * width, base - (base - peak) * (1 - u * u)))
    return points


class ArcStyle(Style):
    name = "arc"
    params: ClassVar[dict[str, dict]] = {
        "phone": _PHONE,
        "tablet": _TABLET,
        "iphone": {**_PHONE, "arc_peak": 0.195},
        "ipad": {**_TABLET, "arc_peak": 0.190},
    }

    def under(self, canvas: Image.Image, ctx: Context) -> None:
        params, size = ctx.params, canvas.size
        width = size[0]
        before = sum(path_length(arc(params, size, index, ctx.count)) for index in range(ctx.order))
        points = arc(params, size, ctx.order, ctx.count)
        dashed(canvas, points, params["dash_stroke"] * width, params["dash_on"] * width,
               params["dash_off"] * width, colour=LINE, phase=before)

        options = ctx.design.options
        radius = params["body_radius"] * width
        if ctx.order == 0 and options.get("sun", True):
            glowing_disc(canvas, points[len(points) * 8 // 100], radius, *SUN)
        if ctx.order == ctx.count - 1 and options.get("moon", True):
            glowing_disc(canvas, points[len(points) * 92 // 100], radius * 0.8, *MOON)
