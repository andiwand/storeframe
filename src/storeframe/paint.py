"""Fills and strokes: backgrounds, dashed lines, glowing discs."""

from __future__ import annotations

import bisect
import itertools
import math
from collections.abc import Sequence

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from .geometry import Point

Colour = str | tuple[int, ...]


def rgb(colour: Colour) -> tuple[int, int, int]:
    if isinstance(colour, str):
        return ImageColor.getrgb(colour)[:3]
    return tuple(colour[:3])


def gradient(size: tuple[int, int], top: Colour, bottom: Colour) -> Image.Image:
    """A vertical linear gradient, as RGBA."""
    width, height = size
    start, end = rgb(top), rgb(bottom)
    strip = Image.new("RGB", (1, height))
    for y in range(height):
        share = y / max(1, height - 1)
        strip.putpixel((0, y), tuple(round(start[i] + (end[i] - start[i]) * share) for i in range(3)))

    return strip.resize((width, height)).convert("RGBA")


def dashed(
    canvas: Image.Image,
    points: Sequence[Point],
    stroke: float,
    on: float,
    off: float,
    colour: Colour = (255, 255, 255, 255),
    phase: float = 0.0,
) -> None:
    """Lay dashes along a polyline, so a dash carries on around a corner.

    Distances are counted from the start of the path rather than accumulated,
    so rounding never drifts. ``phase`` continues the pattern of an earlier path,
    which is how a line keeps its rhythm across a gallery of images.
    """
    reached = [0.0]
    for before, after in itertools.pairwise(points):
        reached.append(reached[-1] + math.hypot(after[0] - before[0], after[1] - before[1]))
    total = reached[-1]
    if not total:
        return

    def at(distance: float) -> Point:
        index = max(1, min(len(reached) - 1, bisect.bisect_left(reached, distance)))
        span = reached[index] - reached[index - 1]
        share = 0.0 if not span else (distance - reached[index - 1]) / span
        before, after = points[index - 1], points[index]
        return (before[0] + (after[0] - before[0]) * share,
                before[1] + (after[1] - before[1]) * share)

    draw = ImageDraw.Draw(canvas)
    width = max(1, round(stroke))
    period = on + off
    phase = phase % period
    for number in range(int((total + phase) // period) + 2):
        start = number * period - phase
        end = min(start + on, total)
        if start >= total:
            break
        start = max(start, 0.0)
        if start >= end:
            continue
        # the path's own corners inside this dash, so a dash on a bend is drawn bent
        run = [at(start)]
        run += [point for point, so_far in zip(points, reached) if start < so_far < end]
        run.append(at(end))
        draw.line(run, fill=colour, width=width, joint="curve")


def glowing_disc(
    canvas: Image.Image, at: Point, radius: float, colour: Colour, glow: Colour
) -> None:
    """A filled disc with a soft halo, like a sun or moon."""
    x, y = at
    halo = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse(
        (x - radius * 2.6, y - radius * 2.6, x + radius * 2.6, y + radius * 2.6), fill=glow
    )
    canvas.alpha_composite(halo.filter(ImageFilter.GaussianBlur(radius * 1.2)))
    ImageDraw.Draw(canvas).ellipse((x - radius, y - radius, x + radius, y + radius), fill=colour)


def horizontal_bands(size: tuple[int, int], colours: Sequence[Colour]) -> Image.Image:
    """An image whose colour varies smoothly across its width through ``colours``."""
    width, height = size
    strip = Image.new("RGB", (len(colours), 1))
    for index, colour in enumerate(colours):
        strip.putpixel((index, 0), rgb(colour))

    return strip.resize((width, height), Image.BICUBIC)
