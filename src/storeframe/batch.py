"""Frame a directory of captures laid out the fastlane way: ``<dir>/<locale>/*.png``."""

from __future__ import annotations

import shutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from . import platforms, render
from .design import Design


@dataclass
class Report:
    written: list[Path] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    missing_locales: list[str] = field(default_factory=list)


def frame_directory(
    design: Design,
    platform: str,
    captured: str | Path,
    out: str | Path,
    *,
    locales: Iterable[str] | None = None,
    feature_graphic: bool = False,
    clean: bool = True,
    progress: Callable[[Path], None] | None = None,
) -> Report:
    """Frame every capture under ``captured/<locale>/`` into ``out/<locale>/``.

    Each locale's output folder is emptied first (``clean``), so a renamed screen
    does not leave a stale picture behind for the upload to find. Files that match
    no screen of the design are skipped and reported.
    """
    captured, out = Path(captured), Path(out)
    platforms.get(platform)
    report = Report()

    if locales is None:
        locales = sorted(p.name for p in captured.iterdir() if p.is_dir()) if captured.is_dir() else []

    for locale in locales:
        folder = captured / locale
        if not folder.is_dir():
            report.missing_locales.append(locale)
            continue
        target = out / locale
        if clean:
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)

        feature_source: Path | None = None
        for path in sorted(folder.glob("*.png")):
            screen = design.match(path.stem)
            if screen is None:
                report.skipped.append((path, "matches no screen of the design"))
                continue
            with Image.open(path) as shot:
                shot = shot.convert("RGB")
                where = platforms.detect(platform, path.stem, shot.size)
                picture = render.screenshot(shot, design, screen, kind=where.kind, device=where.device,
                                            locale=locale, canvas_size=where.canvas)
            destination = target / path.name
            picture.save(destination, optimize=True)
            report.written.append(destination)
            if progress:
                progress(destination)
            if (feature_graphic and screen is design.screens[0] and screen.name in path.stem
                    and where.kind == next(iter(platforms.get(platform)))):
                feature_source = path

        if feature_graphic and feature_source is not None:
            with Image.open(feature_source) as shot:
                picture = render.feature_graphic(shot.convert("RGB"), design, design.screens[0],
                                                 locale=locale)
            destination = target / f"{platforms.FEATURE_GRAPHIC_NAME}.png"
            picture.save(destination, optimize=True)
            report.written.append(destination)
            if progress:
                progress(destination)

    return report
