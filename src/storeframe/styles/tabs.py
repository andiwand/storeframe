"""The device off-centre to the right, coloured tabs ("chips") running off the
left edge, and two dashed lines: one crossing every picture in the gallery
(each picture takes it in at the height the previous one let it out at), and a
lower one hanging off the tabs or entering from the edge.

Design keys used: ``chips`` (name -> colour) at the top level and ``chips``
(list of names) on each screen.
"""

from __future__ import annotations

from typing import ClassVar

from PIL import Image, ImageDraw

from ..geometry import path_length, rounded_path
from ..layout import FEATURE_GRAPHIC, Layout
from ..paint import dashed
from ..text import font
from .base import Context, Style

# Lower decorations: points (x, y) in canvas fractions; values past 0..1 are off
# the edge on purpose. "chips" anchors to the middle of the tab stack, so the line
# runs behind however many tabs there are and comes out underneath.
_PHONE_DECORATIONS = [
    [("chips", "chips"), ("chips", 0.930), (0.55, 0.930)],
    [(-0.2, 0.700), (0.155, 0.700), (0.155, 0.930), (0.62, 0.930)],
    [("chips", "chips"), ("chips", 0.880), (-0.2, 0.880)],
    [(-0.2, 0.845), (0.185, 0.845), (0.185, 0.640), (0.58, 0.640)],
]
_TABLET_DECORATIONS = [
    [("chips", "chips"), ("chips", 0.930), (0.52, 0.930)],
    [(-0.2, 0.620), (0.105, 0.620), (0.105, 0.930), (0.58, 0.930)],
    [("chips", "chips"), ("chips", 0.880), (-0.2, 0.880)],
    [(-0.2, 0.810), (0.125, 0.810), (0.125, 0.520), (0.54, 0.520)],
]


class TabsStyle(Style):
    name = "tabs"
    layouts: ClassVar[dict[str, Layout]] = {
        "phone": Layout(headline_top=0.048, headline_size=0.058, headline_width=0.86, headline_leading=1.06,
                        screen_left=0.308, screen_top=0.200, screen_width=0.600, foot=0.036),
        "tablet": Layout(headline_top=0.060, headline_size=0.052, headline_width=0.80, headline_leading=1.06,
                         screen_left=0.235, screen_top=0.240, screen_width=0.700, foot=0.036),
        "iphone": Layout(headline_top=0.068, headline_size=0.070, headline_width=0.86, headline_leading=1.06,
                         screen_left=0.278, screen_top=0.265, screen_width=0.650, foot=0.045),
        "ipad": Layout(headline_top=0.068, headline_size=0.050, headline_width=0.80, headline_leading=1.06,
                       screen_left=0.215, screen_top=0.250, screen_width=0.720, foot=0.055),
    }
    params: ClassVar[dict[str, dict]] = {
        "phone": {
            "chip_top": 0.430, "chip_size": (0.230, 0.140), "chip_step": 0.157, "chip_text": 0.107,
            "dash_stroke": 0.0056, "dash_on": 0.0236, "dash_off": 0.0098,
            # One seam height per picture boundary, all in the free band between
            # the headline and the top of the device.
            "seams": [0.148, 0.176, 0.158, 0.180, 0.152, 0.172, 0.164],
            # What the line does between its "in" and "out" seams; a number is a
            # height of its own. Dips must come back up left of the device body.
            "routes": [
                [(0.34, "in"), (0.34, "out")],
                [(0.17, "in"), (0.17, "out")],
                [(0.52, "in"), (0.52, "out")],
                [(0.10, "in"), (0.10, 0.245), (0.21, 0.245), (0.21, "out")],
                [(0.26, "in"), (0.26, "out"), (0.60, "out")],
                [(0.13, "in"), (0.13, 0.235), (0.23, 0.235), (0.23, "out")],
            ],
            "radii": [0.078, 0.066, 0.086, 0.062, 0.072, 0.070],
            "decorations": _PHONE_DECORATIONS,
        },
        "tablet": {
            "chip_top": 0.430, "chip_size": (0.170, 0.0900), "chip_step": 0.1010, "chip_text": 0.080,
            "dash_stroke": 0.0040, "dash_on": 0.0147, "dash_off": 0.0061,
            "seams": [0.152, 0.186, 0.166, 0.192, 0.156, 0.180, 0.170],
            "routes": [
                [(0.30, "in"), (0.30, "out")],
                [(0.115, "in"), (0.115, "out")],
                [(0.46, "in"), (0.46, "out")],
                [(0.06, "in"), (0.06, 0.250), (0.15, 0.250), (0.15, "out")],
                [(0.20, "in"), (0.20, "out"), (0.54, "out")],
                [(0.08, "in"), (0.08, 0.240), (0.16, 0.240), (0.16, "out")],
            ],
            "radii": [0.060, 0.052, 0.068, 0.050, 0.056, 0.054],
            "decorations": _TABLET_DECORATIONS,
        },
        "iphone": {
            "chip_top": 0.440, "chip_size": (0.240, 0.147), "chip_step": 0.165, "chip_text": 0.113,
            "dash_stroke": 0.0056, "dash_on": 0.0236, "dash_off": 0.0098,
            "seams": [0.150, 0.200, 0.170, 0.215, 0.158, 0.195, 0.176],
            "routes": [
                [(0.34, "in"), (0.34, "out")],
                [(0.17, "in"), (0.17, "out")],
                [(0.52, "in"), (0.52, "out")],
                [(0.12, "in"), (0.12, 0.248), (0.28, 0.248), (0.28, "out")],
                [(0.26, "in"), (0.26, "out"), (0.60, "out")],
                [(0.15, "in"), (0.15, 0.238), (0.33, 0.238), (0.33, "out")],
            ],
            "radii": [0.078, 0.066, 0.086, 0.062, 0.072, 0.070],
            "decorations": _PHONE_DECORATIONS,
        },
        "ipad": {
            "chip_top": 0.440, "chip_size": (0.170, 0.0828), "chip_step": 0.0935, "chip_text": 0.080,
            "dash_stroke": 0.0040, "dash_on": 0.0147, "dash_off": 0.0061,
            "seams": [0.162, 0.208, 0.180, 0.224, 0.170, 0.202, 0.186],
            "routes": [
                [(0.30, "in"), (0.30, "out")],
                [(0.115, "in"), (0.115, "out")],
                [(0.46, "in"), (0.46, "out")],
                [(0.08, "in"), (0.08, 0.248), (0.19, 0.248), (0.19, "out")],
                [(0.18, "in"), (0.18, "out"), (0.54, "out")],
                [(0.10, "in"), (0.10, 0.238), (0.225, 0.238), (0.225, "out")],
            ],
            "radii": [0.060, 0.052, 0.068, 0.050, 0.056, 0.054],
            "decorations": _TABLET_DECORATIONS,
        },
    }
    feature_layout = FEATURE_GRAPHIC
    feature_params: ClassVar[dict] = {
        "chip_top": 0.470, "chip_size": (0.140, 0.070), "chip_step": 0.080, "chip_text": 0.041,
        "dash_stroke": 0.0040, "dash_on": 0.0166, "dash_off": 0.0069,
        # drawn once: in from the left between copy and tabs, down the gap before
        # the phone, and out along the foot behind the device
        "decoration": [(-0.2, 0.395), (0.600, 0.395), (0.600, 0.900), (1.2, 0.900)],
        "radius": 0.040,
    }

    # -- screenshots ---------------------------------------------------------

    def under(self, canvas: Image.Image, ctx: Context) -> None:
        p = ctx.params
        width, height = canvas.size
        on, off, stroke = p["dash_on"] * width, p["dash_off"] * width, p["dash_stroke"] * width
        radius = p["radii"][ctx.order % len(p["radii"])] * width

        # the crossing line, its dashes picking up where the previous pictures left off
        before = sum(path_length(crossing(p, index, canvas.size)) for index in range(ctx.order))
        dashed(canvas, rounded_path(crossing(p, ctx.order, canvas.size), radius), stroke, on, off,
               phase=before)

        lower = p["decorations"][ctx.order % len(p["decorations"])]
        # a line hanging off tabs that are not there starts in mid air
        if not ctx.screen.chips and _uses_chips(lower):
            lower = next((d for d in p["decorations"] if not _uses_chips(d)), None)
        if lower:
            placed = [(p["chip_size"][0] / 2 if x == "chips" else x,
                       p["chip_top"] if y == "chips" else y) for x, y in lower]
            dashed(canvas, rounded_path([(x * width, y * height) for x, y in placed], radius),
                   stroke, on, off)

    def over(self, canvas: Image.Image, ctx: Context) -> None:
        chips(canvas, ctx.screen.chips, ctx.design.chips, ctx.params, ctx.design.font)

    # -- feature graphic -----------------------------------------------------

    def feature_under(self, canvas: Image.Image, ctx: Context) -> None:
        p = ctx.params
        width, height = canvas.size
        dashed(canvas,
               rounded_path([(x * width, y * height) for x, y in p["decoration"]], p["radius"] * width),
               p["dash_stroke"] * width, p["dash_on"] * width, p["dash_off"] * width)

    def feature_over(self, canvas: Image.Image, ctx: Context) -> None:
        chips(canvas, ctx.screen.chips, ctx.design.chips, ctx.params, ctx.design.font)


def _uses_chips(points) -> bool:
    return any("chips" in point for point in points)


def crossing(p: dict, order: int, size: tuple[int, int]) -> list[tuple[float, float]]:
    """The line this picture hands on: in at one seam height, out at the next."""
    width, height = size
    seams = p["seams"]
    enters = seams[order % len(seams)] * height
    leaves = seams[(order + 1) % len(seams)] * height
    route = p["routes"][order % len(p["routes"])]

    def down(y):
        return enters if y == "in" else leaves if y == "out" else y * height

    return ([(-0.2 * width, enters)] + [(x * width, down(y)) for x, y in route]
            + [(1.2 * width, leaves)])


def chips(canvas: Image.Image, names, palette: dict[str, str], p: dict, font_path) -> float:
    """Coloured tabs running off the left edge, one per name.

    All tabs are as wide as the longest name in the whole palette needs, so they
    stay one length through the gallery.
    """
    if not names:
        return 0.0
    width, height = canvas.size
    least, chip_height = (share * width for share in p["chip_size"])
    face = font(font_path, round(p["chip_text"] * width), "Bold")
    draw = ImageDraw.Draw(canvas)
    padding = p["chip_text"] * width * 0.42
    chip_width = max([least] + [draw.textlength(name, font=face) + 2 * padding for name in palette])

    for index, name in enumerate(names):
        top = p["chip_top"] * height + p["chip_step"] * width * index
        draw.rectangle((-2, top, chip_width, top + chip_height), fill=palette[name])
        draw.text((chip_width / 2, top + chip_height / 2), name, font=face, fill="white", anchor="mm")

    return chip_width
