"""Which devices a store platform has, what canvas each is drawn on, and how to
tell which device a capture came from."""

from __future__ import annotations

from dataclasses import dataclass

from . import devices


@dataclass(frozen=True)
class Target:
    kind: str                         # layout key, e.g. "phone"
    device: str                       # devices.DEVICES key
    canvas: tuple[int, int] | None    # None: the capture's own size


PLATFORMS: dict[str, dict[str, Target]] = {
    # Google Play refuses a screenshot whose long side is more than twice the
    # short one, and a Pixel Pro XL capture is already 2.23:1, so Play images get
    # canvases of their own: 9:16 for phones, 10:16 for tablets.
    "android": {
        "phone": Target("phone", "pixel-pro", (1440, 2560)),
        "tablet": Target("tablet", "pixel-tablet", (1600, 2560)),
    },
    # The App Store wants exactly the size of the device, so iOS keeps the capture's.
    "ios": {
        "iphone": Target("iphone", "iphone-pro-max", None),
        "ipad": Target("ipad", "ipad-pro-13", None),
    },
}

# Play's feature graphic, which is refused unless it is exactly this size.
FEATURE_GRAPHIC = (1024, 500)
FEATURE_GRAPHIC_NAME = "featureGraphic"


def get(platform: str) -> dict[str, Target]:
    try:
        return PLATFORMS[platform]
    except KeyError:
        raise ValueError(f"unknown platform {platform!r}; one of {', '.join(PLATFORMS)}") from None


def detect(platform: str, stem: str, size: tuple[int, int]) -> Target:
    """The target a capture is for.

    A file named ``<kind>-...`` (``phone-01-path.png``) says so itself; anything
    else (fastlane snapshot names such as ``iPhone 17 Pro Max-01-path.png``) is
    matched by aspect ratio to the closest device of the platform.
    """
    targets = get(platform)
    prefix = stem.split("-", 1)[0].lower()
    if prefix in targets:
        return targets[prefix]
    aspect = size[0] / size[1]
    return min(targets.values(), key=lambda t: abs(devices.get(t.device).aspect - aspect))
