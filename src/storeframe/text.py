"""Headline fonts and fitting.

The bundled font is Nunito (SIL Open Font License), a variable font covering
Latin and Cyrillic. Scripts it cannot set are looked up on the system instead
of bundled, since a CJK font is 10-16 MB per language.
"""

from __future__ import annotations

import functools
from collections.abc import Sequence
from importlib import resources
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .layout import Layout

BUNDLED_FONT = "Nunito[wght].ttf"

# A candidate is (regular, bold, marker). The marker picks a face out of a .ttc
# collection by family name, since face order in the Noto CJK collections is not fixed.
NOTO_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"
# The last resort on macOS: Hiragino and PingFang are downloadable rather than
# installed, while this one has been in /Library/Fonts forever. One weight only.
ARIAL_UNICODE = "/Library/Fonts/Arial Unicode.ttf"

SCRIPTS: dict[str, tuple[str, list[tuple[str, str, str | None]]]] = {
    "devanagari": (
        "fonts-noto-core on Debian/Ubuntu, or Devanagari Sangam MN on macOS",
        [
            ("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
             "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf", None),
            ("/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
             "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc", None),
            ("/System/Library/Fonts/Kohinoor.ttc", "/System/Library/Fonts/Kohinoor.ttc", None),
        ],
    ),
    "japanese": (
        "fonts-noto-cjk on Debian/Ubuntu, or Hiragino Sans on macOS",
        [
            (NOTO_CJK % "Regular", NOTO_CJK % "Bold", "JP"),
            ("/System/Library/Fonts/Hiragino Sans W4.ttc",
             "/System/Library/Fonts/Hiragino Sans W7.ttc", None),
            (ARIAL_UNICODE, ARIAL_UNICODE, None),
        ],
    ),
    "chinese": (
        "fonts-noto-cjk on Debian/Ubuntu, or PingFang on macOS",
        [
            (NOTO_CJK % "Regular", NOTO_CJK % "Bold", "SC"),
            ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/PingFang.ttc", "SC"),
            ("/System/Library/Fonts/Hiragino Sans GB.ttc",
             "/System/Library/Fonts/Hiragino Sans GB.ttc", None),
            (ARIAL_UNICODE, ARIAL_UNICODE, None),
        ],
    ),
}

# Language subtag -> script that needs a system font.
WRITTEN_IN = {"hi": "devanagari", "ja": "japanese", "zh": "chinese"}


class MissingFont(RuntimeError):
    pass


def bundled_font() -> Path:
    return Path(str(resources.files("storeframe") / "fonts" / BUNDLED_FONT))


def script_of(locale: str | None) -> str | None:
    if not locale:
        return None
    return WRITTEN_IN.get(locale.replace("_", "-").split("-")[0].lower())


def _face_in(path: str, size: int, marker: str | None) -> ImageFont.FreeTypeFont:
    if marker is None:
        return ImageFont.truetype(path, size)
    for index in range(12):
        try:
            found = ImageFont.truetype(path, size, index=index)
        except (OSError, ValueError):
            break
        if marker in "".join(part or "" for part in found.getname()):
            return found
    raise OSError(f"{path} holds no {marker} face")


@functools.cache
def font(path: str | None, size: int, weight: str, locale: str | None = None) -> ImageFont.FreeTypeFont:
    """A font at a size and named weight, switching to a system font for scripts
    the design font cannot set.

    ``weight`` is a named instance of a variable font ("Regular", "Bold"...); a
    static font ignores it.
    """
    script = script_of(locale)
    if script is None:
        found = ImageFont.truetype(str(path or bundled_font()), size)
    else:
        wanted, candidates = SCRIPTS[script]
        found = None
        for regular, bold, marker in candidates:
            candidate = bold if weight.lower() in ("bold", "black", "extrabold") else regular
            if not Path(candidate).exists():
                continue
            try:
                found = _face_in(candidate, size, marker)
                break
            except OSError:
                continue
        if found is None:
            raise MissingFont(
                f"no font on this machine can set {script} for {locale}; install {wanted}"
            )

    try:
        found.set_variation_by_name(weight)
    except (OSError, ValueError, AttributeError):
        pass  # not a variable font: it is already the weight its file says

    return found


def headline(
    canvas: Image.Image,
    lines: Sequence[str],
    layout: Layout,
    *,
    font_path: str | None = None,
    weights: Sequence[str] = ("Regular", "Bold"),
    locale: str | None = None,
    colour="white",
) -> None:
    """Draw centred headline lines, shrinking them until the widest fits.

    Line *i* uses ``weights[i]`` (the last weight repeats). Fitted rather than set
    at a fixed size, since the same sentence is a third longer in German.
    """
    if not lines:
        return
    width, height = canvas.size
    size = round(layout.headline_size * width)
    allowed = layout.headline_width * width
    line_weights = [weights[min(i, len(weights) - 1)] for i in range(len(lines))]
    draw = ImageDraw.Draw(canvas)

    def faces_at(points: int) -> list[ImageFont.FreeTypeFont]:
        return [font(font_path, points, weight, locale) for weight in line_weights]

    faces = faces_at(size)
    while size > 8 and max(draw.textlength(line, font=face) for line, face in zip(lines, faces)) > allowed:
        size -= 2
        faces = faces_at(size)

    middle = layout.headline_middle * width
    y = layout.headline_top * height
    for line, face in zip(lines, faces):
        draw.text((middle, y), line, font=face, fill=colour, anchor="ma")
        y += size * layout.headline_leading
