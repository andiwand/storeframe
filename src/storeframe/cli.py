"""Command line: ``storeframe frame``, ``storeframe one``, ``storeframe devices``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, devices, platforms, render, styles
from .batch import frame_directory
from .design import Design
from .text import MissingFont


def _frame(args: argparse.Namespace) -> int:
    design = Design.load(args.design)
    report = frame_directory(
        design, args.platform, args.captured, args.out,
        locales=args.locale, feature_graphic=args.feature_graphic, clean=not args.keep,
        progress=(lambda path: print(path)) if args.verbose else None,
    )
    for locale in report.missing_locales:
        print(f"{locale}: no captures in {Path(args.captured) / locale}", file=sys.stderr)
    for path, why in report.skipped:
        print(f"skipped {path}: {why}", file=sys.stderr)
    print(f"framed {len(report.written)} pictures into {args.out}")
    return 0 if report.written else 1


def _one(args: argparse.Namespace) -> int:
    from PIL import Image

    design = Design.load(args.design)
    with Image.open(args.capture) as shot:
        shot = shot.convert("RGB")
        if args.feature_graphic:
            picture = render.feature_graphic(shot, design, args.screen, locale=args.locale,
                                             device=args.device or "pixel-pro")
        else:
            where = platforms.detect(args.platform, Path(args.capture).stem, shot.size)
            if args.kind:
                where = platforms.get(args.platform).get(args.kind) or platforms.Target(
                    args.kind, args.device or where.device, where.canvas)
            canvas = tuple(args.canvas) if args.canvas else where.canvas
            picture = render.screenshot(shot, design, args.screen, kind=where.kind,
                                        device=args.device or where.device, locale=args.locale,
                                        canvas_size=canvas)
    picture.save(args.output, optimize=True)
    print(args.output)
    return 0


def _devices(args: argparse.Namespace) -> int:
    for device in devices.DEVICES.values():
        print(f"{device.name:16} {device.title}")
    print()
    for name, targets in platforms.PLATFORMS.items():
        for target in targets.values():
            canvas = "x".join(map(str, target.canvas)) if target.canvas else "capture size"
            print(f"{name:8} {target.kind:8} {target.device:16} {canvas}")
    print()
    print("styles:", ", ".join(styles.STYLES))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="storeframe", description="Frame app screenshots for the stores.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    frame = commands.add_parser("frame", help="frame a fastlane-style directory of captures")
    frame.add_argument("design", type=Path, help="the design JSON")
    frame.add_argument("--platform", required=True, choices=sorted(platforms.PLATFORMS))
    frame.add_argument("--captured", required=True, type=Path, help="captures, one folder per locale")
    frame.add_argument("--out", required=True, type=Path, help="framed output, one folder per locale")
    frame.add_argument("--locale", action="append", help="only this locale (repeatable)")
    frame.add_argument("--feature-graphic", action="store_true",
                       help="also draw Play's feature graphic from the first screen's phone capture")
    frame.add_argument("--keep", action="store_true", help="don't empty the output locale folders first")
    frame.add_argument("-v", "--verbose", action="store_true")
    frame.set_defaults(run=_frame)

    one = commands.add_parser("one", help="frame a single capture")
    one.add_argument("design", type=Path)
    one.add_argument("capture", type=Path)
    one.add_argument("output", type=Path)
    one.add_argument("--screen", required=True, help="screen name in the design")
    one.add_argument("--platform", default="android", choices=sorted(platforms.PLATFORMS))
    one.add_argument("--kind", help="layout kind (default: detected from file name / aspect)")
    one.add_argument("--device", choices=sorted(devices.DEVICES), help="device body (default: platform's)")
    one.add_argument("--canvas", type=int, nargs=2, metavar=("W", "H"), help="output size")
    one.add_argument("--locale")
    one.add_argument("--feature-graphic", action="store_true")
    one.set_defaults(run=_one)

    listing = commands.add_parser("devices", help="list devices, platforms and styles")
    listing.set_defaults(run=_devices)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except (MissingFont, ValueError, KeyError, FileNotFoundError) as error:
        print(f"storeframe: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
