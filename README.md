# storeframe

Frame raw app captures for the App Store and Google Play: a gradient background,
the capture inside a **drawn** device body (no mockup PNGs), a fitted two-line
headline, and optional decorations that run across the whole gallery.

> Working name. `frameapp` is already taken on PyPI; renaming is one
> search-and-replace of `storeframe`.

## Install

```sh
pip install storeframe            # once published
pip install -e '.[dev]'           # from this checkout
```

## Use

```sh
# frame a fastlane-style tree: captures/<locale>/*.png -> framed/<locale>/*.png
storeframe frame design.json --platform android --captured fastlane/screenshots --out fastlane/framed
storeframe frame design.json --platform ios     --captured fastlane/screenshots --out fastlane/framed --locale en-US

# Play's 1024x500 feature graphic, from the first screen's phone capture
storeframe frame design.json --platform android --captured ... --out ... --feature-graphic

# one picture
storeframe one design.json capture.png out.png --screen 01-path --platform ios

storeframe devices                # list devices, platforms, styles
```

```python
from PIL import Image
import storeframe

design = storeframe.Design.load("design.json")
picture = storeframe.screenshot(Image.open("phone-01-path.png"), design, "01-path",
                                kind="phone", device="pixel-pro", canvas_size=(1440, 2560))
```

## Platforms and devices

| Platform | Kind | Device | Output canvas |
|---|---|---|---|
| `android` | `phone` | `pixel-pro` | 1440×2560 (Play refuses > 2:1) |
| `android` | `tablet` | `pixel-tablet` | 1600×2560 |
| `ios` | `iphone` | `iphone-pro-max` | capture size (App Store wants the device size) |
| `ios` | `ipad` | `ipad-pro-13` | capture size |

A capture named `<kind>-<screen>.png` says its kind; otherwise (fastlane
snapshot names like `iPhone 17 Pro Max-01-path.png`) the kind is picked by
aspect ratio. The screen is the design screen whose name (or alias) the file
name ends with.

Device geometry is expressed as fractions of the *screen* width, so a device
looks the same however large it is drawn.

## Styles

- `plain` – centred device, headline above.
- `arc` – a dashed parabola spanning the whole gallery, sun in the first picture, moon in the last.
- `tabs` – device off-centre, coloured tabs running off the left edge, a dashed line
  that crosses every picture (each one picks it up where the previous one left it)
  and a second line hanging off the tabs.

## The design file

```json
{
  "style": "arc",
  "font": "Nunito[wght].ttf",
  "backgrounds": { "evening": ["#f2a65a", "#c9655b"] },
  "chips": { "odt": "#4bb3e8" },
  "screens": [
    {
      "name": "01-path",
      "background": "evening",
      "headline": { "en-US": ["See when the sun", "is where."] },
      "chips": [],
      "aliases": ["01-path-lite"]
    }
  ],
  "layouts": { "phone": { "screen_top": 0.22 } },
  "params":  { "phone": { "arc_peak": 0.15 } },
  "options": { "moon": false }
}
```

- `font` is optional and relative to the design file; the bundled Nunito
  (SIL OFL) is the default. Hindi, Japanese and Chinese headlines use a system
  font (Noto on Linux, the system fonts on macOS).
- `headline` falls back from `de-AT` to `de`/`de-DE`, then to `fallback_locale` (`en-US`).
- `layouts` / `params` override a style's numbers per device kind (`phone`,
  `tablet`, `iphone`, `ipad`, `feature`). See `src/storeframe/layout.py` and the
  style modules for what each number means.
- Existing `frames.json` files from OpenDocument.ios/.droid and almucantar load
  unchanged (`"arc": true` → `arc`, a `chips` palette → `tabs`). The
  OpenDocument "lite" capture needs `"aliases": ["04-edit-lite"]` on its screen.

## Development

```sh
uv venv && uv pip install -e '.[dev]'
.venv/bin/pytest
```

## License

MIT. The bundled Nunito font is under the SIL Open Font License 1.1 (`src/storeframe/fonts/OFL.txt`).
