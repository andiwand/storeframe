"""Compose one store picture: background, decorations, device, headline."""

from __future__ import annotations

from PIL import Image

from . import devices, styles, text
from .design import Design, Screen
from .layout import Layout
from .paint import gradient
from .platforms import FEATURE_GRAPHIC


def resolve(design: Design, style: styles.Style, kind: str) -> tuple[Layout, dict]:
    """The layout and style parameters for a device kind, with the design's overrides."""
    layout = style.layout_for(kind).updated(design.layouts.get(kind))
    params = style.params_for(kind)
    params.update(design.params.get(kind, {}))
    return layout, params


def screenshot(
    capture: Image.Image,
    design: Design,
    screen: Screen | str,
    *,
    kind: str,
    device: devices.Device | str,
    locale: str | None = None,
    canvas_size: tuple[int, int] | None = None,
) -> Image.Image:
    """One framed store screenshot, as RGB.

    ``kind`` picks the layout (``phone``, ``tablet``, ``iphone``, ``ipad``),
    ``device`` the drawn body, and ``canvas_size`` the output size (default: the
    capture's own size).
    """
    if isinstance(screen, str):
        screen = design.screen(screen)
    locale = locale or design.fallback_locale
    style = styles.get(design.style)
    layout, params = resolve(design, style, kind)
    size = canvas_size or capture.size

    canvas = gradient(size, *screen.background)
    ctx = styles.Context(design=design, screen=screen, kind=kind, locale=locale,
                         order=design.order(screen), count=len(design.screens),
                         layout=layout, params=params)
    style.under(canvas, ctx)
    ctx.placed = devices.draw(canvas, capture, device, layout)
    style.over(canvas, ctx)
    text.headline(canvas, design.lines(screen, locale), layout, font_path=design.font,
                  weights=design.weights, locale=locale)

    return canvas.convert("RGB")


def feature_graphic(
    capture: Image.Image,
    design: Design,
    screen: Screen | str,
    *,
    device: devices.Device | str = "pixel-pro",
    locale: str | None = None,
    canvas_size: tuple[int, int] = FEATURE_GRAPHIC,
) -> Image.Image:
    """Google Play's landscape feature graphic: headline left, phone right."""
    if isinstance(screen, str):
        screen = design.screen(screen)
    locale = locale or design.fallback_locale
    style = styles.get(design.style)
    layout = style.feature_layout.updated(design.layouts.get("feature"))
    params = dict(style.feature_params)
    params.update(design.params.get("feature", {}))

    canvas = gradient(canvas_size, *screen.background)
    ctx = styles.Context(design=design, screen=screen, kind="feature", locale=locale,
                         order=design.order(screen), count=len(design.screens),
                         layout=layout, params=params)
    style.feature_under(canvas, ctx)
    ctx.placed = devices.draw(canvas, capture, device, layout)
    style.feature_over(canvas, ctx)
    text.headline(canvas, design.lines(screen, locale), layout, font_path=design.font,
                  weights=design.weights, locale=locale)

    return canvas.convert("RGB")
