"""Shapes as point lists: rounded device outlines, parallel offsets, rounded polylines."""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

from PIL import Image, ImageDraw

Point = tuple[float, float]
Box = tuple[float, float, float, float]


def squircle(box: Box, radius: float, exponent: float = 2.2, per_corner: int = 40) -> list[Point]:
    """A rounded rectangle whose corners are superellipse quadrants.

    The exponent is the shape of the device's corner: about 2-2.2 is near a
    circular arc (a Pixel), about 5 is a continuous curve easing into the
    straight edge (an iPhone or iPad).
    """
    x0, y0, x1, y1 = box
    r = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
    points = []

    # Each corner as (centre, x sign, y sign), clockwise from bottom right. Two of
    # the four are walked backwards so each quadrant ends where the next starts.
    for (cx, cy), sx, sy in (
        ((x1 - r, y1 - r), 1, 1),
        ((x0 + r, y1 - r), -1, 1),
        ((x0 + r, y0 + r), -1, -1),
        ((x1 - r, y0 + r), 1, -1),
    ):
        for step in range(per_corner + 1):
            share = step / per_corner if sx * sy > 0 else 1 - step / per_corner
            angle = math.pi / 2 * share
            points.append((
                cx + sx * r * math.cos(angle) ** (2 / exponent),
                cy + sy * r * math.sin(angle) ** (2 / exponent),
            ))

    return points


def outset(points: Sequence[Point], distance: float) -> list[Point]:
    """The same closed outline moved out (or in, if negative) along its normals.

    A squircle grown by raising its radius is not parallel to the original, so a
    border drawn that way is fatter at the corners. This keeps it even.
    """
    pairs = list(zip(points, list(points[1:]) + list(points[:1])))
    facing = 1.0 if sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in pairs) > 0 else -1.0
    moved = []
    for index, (x, y) in enumerate(points):
        (ax, ay), (bx, by) = points[index - 1], points[(index + 1) % len(points)]
        run, rise = bx - ax, by - ay
        length = math.hypot(run, rise) or 1.0
        moved.append((x + facing * rise / length * distance, y - facing * run / length * distance))

    return moved


def rounded_path(points: Sequence[Point], radius: float, per_corner: int = 24) -> list[Point]:
    """An open polyline with its corners rounded off by quadratic bends."""
    walk = [points[0]]
    for before, corner, after in zip(points, points[1:], points[2:]):
        into = math.hypot(corner[0] - before[0], corner[1] - before[1])
        out = math.hypot(after[0] - corner[0], after[1] - corner[1])
        if not into or not out:
            walk.append(corner)
            continue
        r = min(radius, into / 2, out / 2)
        start = (corner[0] + (before[0] - corner[0]) * r / into,
                 corner[1] + (before[1] - corner[1]) * r / into)
        end = (corner[0] + (after[0] - corner[0]) * r / out,
               corner[1] + (after[1] - corner[1]) * r / out)
        walk.append(start)
        for i in range(1, per_corner):
            t = i / per_corner
            walk.append((
                (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * corner[0] + t ** 2 * end[0],
                (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * corner[1] + t ** 2 * end[1],
            ))
        walk.append(end)
    walk.append(points[-1])

    return walk


def path_length(points: Sequence[Point]) -> float:
    """How far a polyline runs."""
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in itertools.pairwise(points))


def stencil(size: tuple[int, int], points: Sequence[Point], supersample: int = 3) -> Image.Image:
    """An antialiased mask of one polygon: drawn large and shrunk."""
    big = Image.new("L", (size[0] * supersample, size[1] * supersample), 0)
    ImageDraw.Draw(big).polygon([(x * supersample, y * supersample) for x, y in points], fill=255)

    return big.resize(size, Image.LANCZOS)
