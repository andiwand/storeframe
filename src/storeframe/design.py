"""The design file: one JSON per app describing its gallery.

    {
      "style": "plain" | "arc" | "tabs",
      "font": "Nunito[wght].ttf",          # optional, relative to this file; default bundled Nunito
      "weights": ["Regular", "Bold"],      # optional, per headline line
      "fallback_locale": "en-US",          # optional
      "backgrounds": {"evening": ["#f2a65a", "#c9655b"]},
      "chips": {"odt": "#4bb3e8"},         # tabs style: tab colours
      "options": {},                       # style options, e.g. {"sun": false}
      "layouts": {"phone": {"screen_top": 0.22}},   # optional per-device-kind overrides
      "params": {"phone": {"arc_peak": 0.15}},      # optional per-kind style-parameter overrides
      "screens": [
        {"name": "01-path", "background": "evening",
         "headline": {"en-US": ["See when the sun", "is where."]},
         "chips": ["odt"], "aliases": ["01-path-lite"]}
      ]
    }

The ``frames.json`` files of OpenDocument.ios/.droid and almucantar load
unchanged: ``"arc": true`` means the arc style, a top-level ``chips`` palette
means the tabs style, ``_comment`` is ignored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paint import Colour


@dataclass
class Screen:
    name: str
    background: tuple[Colour, Colour]
    headline: dict[str, list[str]] = field(default_factory=dict)
    chips: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def names(self) -> list[str]:
        return [self.name, *self.aliases]


@dataclass
class Design:
    screens: list[Screen]
    style: str = "plain"
    font: str | None = None
    weights: tuple[str, ...] = ("Regular", "Bold")
    fallback_locale: str = "en-US"
    chips: dict[str, str] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    layouts: dict[str, dict[str, Any]] = field(default_factory=dict)
    params: dict[str, dict[str, Any]] = field(default_factory=dict)
    path: Path | None = None

    @classmethod
    def load(cls, path: str | Path) -> Design:
        path = Path(path)
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")), root=path.parent, path=path)

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: Path | None = None, path: Path | None = None) -> Design:
        data = {k: v for k, v in data.items() if not k.startswith("_")}
        backgrounds = data.get("backgrounds", {})
        palette = data.get("chips", {})

        style = data.get("style")
        if style is None:
            style = "arc" if data.get("arc") else "tabs" if palette else "plain"

        font = data.get("font")
        if font is not None:
            candidate = Path(font)
            if not candidate.is_absolute() and root is not None:
                candidate = root / candidate
            font = str(candidate)

        screens = []
        for entry in data.get("screens", []):
            background = entry.get("background", ["#5b9be0", "#3a6fb8"])
            if isinstance(background, str):
                if background not in backgrounds:
                    raise ValueError(f"screen {entry['name']}: no background named {background!r}")
                background = backgrounds[background]
            chips = list(entry.get("chips", []))
            missing = [name for name in chips if name not in palette]
            if missing:
                raise ValueError(f"screen {entry['name']}: no chip colour for {', '.join(missing)}")
            known = {"name", "background", "headline", "chips", "aliases"}
            screens.append(Screen(
                name=entry["name"],
                background=tuple(background),
                headline={locale: list(lines) for locale, lines in entry.get("headline", {}).items()},
                chips=chips,
                aliases=list(entry.get("aliases", [])),
                extra={k: v for k, v in entry.items() if k not in known},
            ))

        return cls(
            screens=screens,
            style=style,
            font=font,
            weights=tuple(data.get("weights", ("Regular", "Bold"))),
            fallback_locale=data.get("fallback_locale", "en-US"),
            chips=dict(palette),
            options=dict(data.get("options", {})),
            layouts=dict(data.get("layouts", {})),
            params=dict(data.get("params", {})),
            path=path,
        )

    def screen(self, name: str) -> Screen:
        for screen in self.screens:
            if name in screen.names:
                return screen
        raise KeyError(name)

    def match(self, stem: str) -> Screen | None:
        """The screen a capture file belongs to: the longest screen name or alias
        that the file stem ends with (so ``phone-01-path`` and
        ``iPhone 17 Pro Max-01-path`` both match ``01-path``)."""
        best: tuple[int, Screen] | None = None
        for screen in self.screens:
            for name in screen.names:
                matches = stem == name or stem.endswith(("-" + name, "_" + name))
                if matches and (best is None or len(name) > best[0]):
                    best = (len(name), screen)
        return best[1] if best else None

    def order(self, screen: Screen) -> int:
        return self.screens.index(screen)

    def lines(self, screen: Screen, locale: str) -> list[str]:
        """The headline in that locale, falling back on its language, then the fallback locale."""
        if locale in screen.headline:
            return screen.headline[locale]
        language = locale.replace("_", "-").split("-")[0]
        for key, lines in screen.headline.items():
            if key == language or key.split("-")[0] == language:
                return lines
        return screen.headline.get(self.fallback_locale, [])
