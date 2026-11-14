"""Drawn device bodies.

The device is drawn rather than pasted from a mockup image, so it takes the
shape of whatever was captured: a downloaded frame is the wrong shape for the
next device. Every proportion here is a fraction of the *screen* (or of the
body), never of the canvas, so a device looks the same at any size.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .geometry import Box, outset, squircle, stencil
from .layout import Layout
from .paint import horizontal_bands

# (how far down the body, how long), both fractions of the body's height
Key = tuple[float, float]


@dataclass(frozen=True)
class Device:
    name: str
    title: str
    aspect: float                    # nominal screen width / height, for telling captures apart
    bezel: float                     # screen edge to outside of the body, of the screen width
    rim: float                       # how much of the bezel is the black border (the rest is metal)
    corner: float                    # screen corner radius, of the screen width
    corner_easing: float = 2.2       # superellipse exponent: ~2.2 circular, ~5 continuous
    buttons_left: tuple[Key, ...] = ()
    buttons_right: tuple[Key, ...] = ()
    tray: Key | None = None          # a flush SIM tray seam on the left edge
    hole: float | None = None        # punch-hole camera diameter, of the screen width
    hole_top: float = 0.0
    island: tuple[float, float] | None = None   # Dynamic Island (width, height), of the screen width
    island_top: float = 0.0


DEVICES: dict[str, Device] = {
    device.name: device
    for device in (
        # A Pixel 9/10 Pro XL: a 70.2mm screen in a 76.6mm body leaves 3.2mm of
        # aluminium and black border each side; less than half of that is black.
        # Near-circular display corners, a punch hole, both keys on the right and
        # the SIM tray low on the left.
        Device(
            name="pixel-pro",
            title="Google Pixel Pro (XL)",
            aspect=1344 / 2992,
            bezel=0.045,
            rim=0.42,
            corner=0.122,
            corner_easing=2.2,
            hole=0.046,
            hole_top=0.028,
            buttons_right=((0.175, 0.055), (0.250, 0.105)),
            tray=(0.620, 0.075),
        ),
        # A Pixel Tablet: a wide border that is mostly black mask, with a thin
        # bright edge. Its keys are on the top edge in portrait, so none show.
        Device(
            name="pixel-tablet",
            title="Google Pixel Tablet",
            aspect=1600 / 2560,
            bezel=0.068,
            rim=0.86,
            corner=0.030,
            corner_easing=2.2,
        ),
        # An iPhone Pro Max: continuous corners, the Dynamic Island, action and
        # volume keys on the left, the side key on the right.
        Device(
            name="iphone-pro-max",
            title="Apple iPhone Pro Max",
            aspect=1320 / 2868,
            bezel=0.042,
            rim=0.57,
            corner=0.141,
            corner_easing=5.0,
            island=(0.2826, 0.0811),
            island_top=0.0334,
            buttons_left=((0.189, 0.0423), (0.262, 0.0686), (0.349, 0.0686)),
            buttons_right=((0.286, 0.1082),),
        ),
        # An iPad Pro 13-inch: a uniform black border and a small corner.
        Device(
            name="ipad-pro-13",
            title="Apple iPad Pro 13-inch",
            aspect=2064 / 2752,
            bezel=0.052,
            rim=0.86,
            corner=0.0174,
            corner_easing=5.0,
        ),
    )
}


def get(name: str | Device) -> Device:
    if isinstance(name, Device):
        return name
    try:
        return DEVICES[name]
    except KeyError:
        raise ValueError(f"unknown device {name!r}; one of {', '.join(DEVICES)}") from None


# Finish. The body is near-black; the metal is a warm grey (a multiplier per
# channel, small on purpose: past about 5% aluminium turns into gold).
BODY = "#08080a"
ALUMINIUM = (1.035, 1.0, 0.955)
BUTTON = ("#d8d8d6", "#a9a9a7", "#c4c4c2")
TRAY = ("#9a9a98", "#7c7c7a", "#909090")
GLASS = 96                       # how brightly the screen edge catches the light, of 255
SHADOW = (0, 0, 0, 105)
SHADOW_OFFSET = (0.30, 0.65)     # of the bezel, across and down
SHADOW_BLUR = 0.85               # of the bezel
KEY_STAND = 0.0061               # how far a key stands proud, of the screen width


def chamfer(share: float) -> tuple[int, int, int]:
    """The polished metal's colour that far across the band, outside edge to black.

    A narrow specular at the outer edge, a hard drop, a weaker sheen where the
    flat turns down to the glass, and dark where it meets the black surround.
    """
    stops = ((0.00, 150), (0.10, 240), (0.22, 208), (0.42, 138), (0.66, 192), (0.85, 164), (1.00, 96))
    place = bisect.bisect_right([at for at, _ in stops], share)
    if place == 0:
        level = stops[0][1]
    elif place == len(stops):
        level = stops[-1][1]
    else:
        (before, low), (after, high) = stops[place - 1], stops[place]
        level = low + (high - low) * (share - before) / (after - before)

    return tuple(min(255, round(level * warm)) for warm in ALUMINIUM)


@dataclass(frozen=True)
class Placed:
    """Where a device ended up on the canvas, in pixels."""
    screen: Box
    body: Box


def place(canvas_size: tuple[int, int], capture_size: tuple[int, int], device: Device,
          layout: Layout) -> Placed:
    """Fit the screen into the layout: as wide as allowed, leaving the foot free."""
    width, height = canvas_size
    aspect = capture_size[0] / capture_size[1]
    top = layout.screen_top * height
    # top + screen height + bottom bezel must stay above the foot
    standing = height - layout.foot * height - top
    screen_width = min(layout.screen_width * width, standing / (1 / aspect + device.bezel))
    screen_height = screen_width / aspect
    if layout.screen_left is None:
        left = (width - screen_width) / 2
    else:
        left = layout.screen_left * width
    bezel = device.bezel * screen_width
    screen = (left, top, left + screen_width, top + screen_height)
    body = (screen[0] - bezel, screen[1] - bezel, screen[2] + bezel, screen[3] + bezel)

    return Placed(screen=screen, body=body)


def draw(canvas: Image.Image, capture: Image.Image, device: Device | str, layout: Layout) -> Placed:
    """Composite the capture behind glass in a drawn body, with keys and a shadow.

    ``canvas`` must be RGBA. Returns where the device was placed.
    """
    device = get(device)
    placed = place(canvas.size, capture.size, device, layout)
    screen, body = placed.screen, placed.body
    screen_width, screen_height = screen[2] - screen[0], screen[3] - screen[1]
    bezel = device.bezel * screen_width
    rim = bezel * device.rim
    corner = device.corner * screen_width

    # Built on its own transparent layer with room for the keys, composited once,
    # so parts can be masked against each other without the ground showing through.
    margin = round(bezel * 3)
    origin = (round(body[0]) - margin, round(body[1]) - margin)
    size = (round(body[2]) - origin[0] + margin, round(body[3]) - origin[1] + margin)

    def here(box: Box) -> Box:
        return tuple(v - origin[i % 2] for i, v in enumerate(box))

    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    local_body = here(body)
    tall_as = body[3] - body[1]
    stand = screen_width * KEY_STAND

    def along(edge: float, keys: tuple[Key, ...], proud: float) -> Image.Image:
        marks = Image.new("L", size, 0)
        pen = ImageDraw.Draw(marks)
        for at_height, tall in keys:
            y = local_body[1] + tall_as * at_height
            pen.rounded_rectangle((edge - proud, y, edge + proud, y + tall_as * tall),
                                  radius=proud * 0.55, fill=255)
        return marks

    # keys first, so the body's own edge covers where they meet it
    keys = ImageChops.lighter(along(local_body[0], device.buttons_left, stand),
                              along(local_body[2], device.buttons_right, stand))
    layer.paste(horizontal_bands(size, BUTTON), (0, 0), keys)
    if device.tray:
        layer.paste(horizontal_bands(size, TRAY), (0, 0),
                    along(local_body[0], (device.tray,), stand * 0.45))

    # Every edge is the screen outline moved out, so border and metal keep their
    # width all the way round.
    face = squircle(here(screen), corner, device.corner_easing)
    outline = outset(face, bezel)

    # The metal band, filled as rings shaded by how far in they sit.
    band = bezel - rim
    lit = Image.new("RGB", size, chamfer(1.0))
    rings = ImageDraw.Draw(lit)
    steps = max(8, round(band))
    for step in range(steps + 1):
        share = step / steps
        rings.polygon(outset(face, bezel - band * share), fill=chamfer(share))
    layer.paste(lit, (0, 0), stencil(size, outline))

    # the black surround, then the glass
    layer.paste(Image.new("RGB", size, BODY), (0, 0), stencil(size, outset(face, rim)))
    fitted = capture.convert("RGB").resize(
        (round(screen_width), round(screen_height)), Image.LANCZOS).convert("RGBA")
    inside = here(screen)
    at = (round(inside[0]), round(inside[1]))
    layer.paste(fitted, at, stencil(size, face).crop(
        (at[0], at[1], at[0] + fitted.width, at[1] + fitted.height)))

    # A hairline where the glass meets the surround, so a dark screen doesn't
    # merge with the black border.
    hair = max(1.0, screen_width * 0.0012)
    halo = ImageChops.subtract(stencil(size, face), stencil(size, outset(face, -hair)))
    layer.paste(Image.new("RGB", size, "white"), (0, 0),
                halo.point(lambda level: level * GLASS // 255))

    middle = (inside[0] + inside[2]) / 2
    pen = ImageDraw.Draw(layer)
    if device.hole:
        across = device.hole * screen_width
        top = inside[1] + device.hole_top * screen_width
        pen.ellipse((middle - across / 2, top, middle + across / 2, top + across), fill=BODY)
    if device.island:
        island_width, island_height = (share * screen_width for share in device.island)
        top = inside[1] + device.island_top * screen_width
        pen.rounded_rectangle(
            (middle - island_width / 2, top, middle + island_width / 2, top + island_height),
            radius=island_height / 2, fill=BODY)

    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow.paste(Image.new("RGB", size, SHADOW[:3]), (0, 0),
                 stencil(size, outline).point(lambda v: v * SHADOW[3] // 255))
    canvas.alpha_composite(
        shadow.filter(ImageFilter.GaussianBlur(bezel * SHADOW_BLUR)),
        (origin[0] + round(bezel * SHADOW_OFFSET[0]), origin[1] + round(bezel * SHADOW_OFFSET[1])))
    canvas.alpha_composite(layer, origin)

    return placed
