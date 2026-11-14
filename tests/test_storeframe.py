from pathlib import Path

import pytest
from PIL import Image

import storeframe
from storeframe import cli, devices, platforms
from storeframe.design import Design

SCREENS = [
    {"name": "01-home", "background": "day", "chips": ["odt"],
     "headline": {"en-US": ["First line", "second line."], "de-DE": ["Erste Zeile", "zweite Zeile."]}},
    {"name": "02-detail", "background": "night", "chips": [], "aliases": ["02-detail-lite"],
     "headline": {"en-US": ["Another", "screen."]}},
]


def design(style: str, **extra) -> Design:
    return Design.from_dict({
        "style": style,
        "backgrounds": {"day": ["#5b9be0", "#3a6fb8"], "night": ["#25365e", "#0b1429"]},
        "chips": {"odt": "#4bb3e8"},
        "screens": SCREENS,
        **extra,
    })


def capture(size=(1344 // 4, 2992 // 4)) -> Image.Image:
    return Image.new("RGB", size, "#e0e0e0")


@pytest.mark.parametrize("style", ["plain", "arc", "tabs"])
@pytest.mark.parametrize("kind,device,canvas", [
    ("phone", "pixel-pro", (360, 640)),
    ("tablet", "pixel-tablet", (400, 640)),
    ("iphone", "iphone-pro-max", None),
    ("ipad", "ipad-pro-13", None),
])
def test_screenshot_every_style_and_device(style, kind, device, canvas):
    shot = capture((round(devices.DEVICES[device].aspect * 700), 700))
    for screen in ("01-home", "02-detail"):
        out = storeframe.screenshot(shot, design(style), screen, kind=kind, device=device,
                                    canvas_size=canvas)
        assert out.mode == "RGB"
        assert out.size == (canvas or shot.size)


def test_feature_graphic_size():
    out = storeframe.feature_graphic(capture(), design("tabs"), "01-home")
    assert out.size == platforms.FEATURE_GRAPHIC


def test_device_fits_inside_canvas():
    layout = storeframe.Layout(screen_top=0.2, screen_width=0.9, foot=0.05)
    for device in devices.DEVICES.values():
        placed = devices.place((1000, 1600), (round(device.aspect * 1000), 1000), device, layout)
        assert placed.body[3] <= 1600 * (1 - 0.05) + 1e-6
        assert placed.body[0] >= 0 and placed.body[2] <= 1000


def test_legacy_design_files_pick_their_style():
    base = {"backgrounds": {"a": ["#000", "#111"]}, "screens": []}
    assert Design.from_dict({**base, "arc": True}).style == "arc"
    assert Design.from_dict({**base, "chips": {"odt": "#fff"}}).style == "tabs"
    assert Design.from_dict(base).style == "plain"
    assert Design.from_dict({**base, "_comment": ["x"], "style": "arc"}).style == "arc"


def test_unknown_background_or_chip_is_an_error():
    with pytest.raises(ValueError):
        Design.from_dict({"screens": [{"name": "x", "background": "nope"}]})
    with pytest.raises(ValueError):
        Design.from_dict({"screens": [{"name": "x", "background": ["#000", "#000"], "chips": ["odt"]}]})


def test_screen_matching():
    d = design("plain")
    assert d.match("phone-01-home").name == "01-home"
    assert d.match("iPhone 17 Pro Max-01-home").name == "01-home"
    assert d.match("phone-02-detail-lite").name == "02-detail"
    assert d.match("phone-03-other") is None
    assert d.match("phone-101-home") is None


def test_headline_locale_fallback():
    d = design("plain")
    home = d.screen("01-home")
    assert d.lines(home, "de-DE")[0] == "Erste Zeile"
    assert d.lines(home, "de-AT")[0] == "Erste Zeile"
    assert d.lines(home, "fr-FR")[0] == "First line"


def test_detect_kind():
    assert platforms.detect("android", "tablet-01-home", (10, 10)).kind == "tablet"
    assert platforms.detect("ios", "iPhone 17 Pro Max-01", (1320, 2868)).kind == "iphone"
    assert platforms.detect("ios", "iPad Pro 13-inch (M5)-01", (2064, 2752)).kind == "ipad"


def test_layout_overrides():
    d = design("plain", layouts={"phone": {"screen_top": 0.3}})
    with pytest.raises(ValueError):
        storeframe.Layout().updated({"nonsense": 1})
    from storeframe import render, styles
    layout, _ = render.resolve(d, styles.get("plain"), "phone")
    assert layout.screen_top == 0.3


def test_frame_directory(tmp_path: Path):
    captured = tmp_path / "captured" / "en-US"
    captured.mkdir(parents=True)
    capture().save(captured / "phone-01-home.png")
    capture().save(captured / "phone-02-detail.png")
    capture().save(captured / "phone-99-unknown.png")
    out = tmp_path / "framed"
    (out / "en-US").mkdir(parents=True)
    (out / "en-US" / "stale.png").write_bytes(b"")

    report = storeframe.frame_directory(design("tabs"), "android", tmp_path / "captured", out,
                                        feature_graphic=True)
    names = sorted(p.name for p in (out / "en-US").iterdir())
    assert names == ["featureGraphic.png", "phone-01-home.png", "phone-02-detail.png"]
    assert len(report.skipped) == 1
    with Image.open(out / "en-US" / "phone-01-home.png") as picture:
        assert picture.size == (1440, 2560)


def test_cli(tmp_path: Path, capsys):
    import json
    spec = tmp_path / "design.json"
    spec.write_text(json.dumps({"backgrounds": {"day": ["#5b9be0", "#3a6fb8"],
                                                "night": ["#000", "#111"]},
                                "chips": {"odt": "#4bb3e8"}, "screens": SCREENS, "arc": True}))
    source = tmp_path / "shot.png"
    capture((330, 717)).save(source)
    target = tmp_path / "out.png"
    assert cli.main(["one", str(spec), str(source), str(target), "--screen", "01-home",
                     "--platform", "ios"]) == 0
    assert Image.open(target).size == (330, 717)
    assert cli.main(["devices"]) == 0
    assert cli.main(["one", str(spec), str(source), str(target), "--screen", "missing"]) == 2


def test_folders_without_captures_are_not_locales(tmp_path: Path):
    # another app's captures nest beside the locale folders, as in almucantar
    captured = tmp_path / "captured"
    (captured / "en-US").mkdir(parents=True)
    capture().save(captured / "en-US" / "phone-01-home.png")
    (captured / "otherapp" / "en-US").mkdir(parents=True)
    capture().save(captured / "otherapp" / "en-US" / "phone-01-home.png")
    out = tmp_path / "framed"
    kept = out / "otherapp" / "en-US" / "framed-before.png"
    kept.parent.mkdir(parents=True)
    kept.write_bytes(b"")

    report = storeframe.frame_directory(design("plain"), "android", captured, out)
    assert [p.relative_to(out).as_posix() for p in report.written] == ["en-US/phone-01-home.png"]
    assert kept.exists()
