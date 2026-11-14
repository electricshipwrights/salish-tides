# Salish Sea tidal model: open weights

Tidal currents and tide heights for the Salish Sea, from Juan de Fuca to
Seymour Narrows, as harmonic constants on grids from 180 m down to 10 m in
the passes. Give it a place and a time and it returns the current and the
height of the tide. No network, no service, no expiry: the constants answer
for any date.

This repository is the production model of the Tidal Atlas apps and
nothing else: the weights, the coastline they are drawn against, one Python
file that reads them, and four examples. The model is the one labelled
**v2** in the project's calibration record, exported 2026-11-06 (see
Version below).

```python
from datetime import datetime, timezone
from tidal_atlas import Pyramid, speed_and_bearing

model = Pyramid("weights/pyramid")
when = datetime(2025, 7, 4, 17, 0, tzinfo=timezone.utc)

east, north = model.current(-123.8171, 49.1344, when)   # Dodd Narrows, m/s
speed, toward = speed_and_bearing(east, north)
height = model.tide(-123.254, 49.337, when)             # Point Atkinson, m about mean level
```

## What is here

| path | what | size |
|---|---|---:|
| `weights/pyramid/` | The full model: 14 grids of current and tide-height constants, with `manifest.json` | 50 MB |
| `weights/flow.pack` | Currents only, Canadian waters only, tiled for fast random access | 24 MB |
| `weights/tide.pack` | Tide heights only, one 730 m grid | 0.4 MB |
| `weights/coast.pack` | The coastline: land polygons at four levels of detail, from OpenStreetMap | 7 MB |
| `tidal_atlas.py` | The reader: `Pyramid`, `FlowPack`, `TidePack`, `Coast` | one file, numpy only |
| `examples/` | Current over the next 12 hours; slack water in a pass; a day's tide curve; a chart as SVG | |
| `check.py` | Verifies file hashes and the three readers against each other | |
| `FORMATS.md` | Byte-level description of each file | |
| `MODEL.md` | How the model was made, how it scores, where it is wrong | |

The three weight files hold the same model in three shapes. Use the pyramid
when you want everything or want to read the constants themselves; the flow
pack when you want currents fast from a small memory footprint, which is
what the apps do; the tide pack when you only want heights.

## Use

Python 3.9 or later and numpy.

```sh
python check.py                                   # hashes and self-consistency
python examples/current_now.py                    # Active Pass, next 12 hours
python examples/slack_water.py -123.8171 49.1344  # Dodd Narrows, today's turns
python examples/tide_curve.py -123.371 48.424     # Victoria, today's tide
python examples/chart_svg.py                      # Active Pass now, coastline and arrows
```

Every reader answers the same two questions:

- `current(lon, lat, when)` returns `(east, north)` in metres per second,
  the direction the water is going, or `None` where the model has no water.
- `tide(lon, lat, when)` returns metres about mean water level, or `None`.

`when` is a `datetime` (a naive one is taken as UTC) or Unix seconds.
Longitude is negative west. A question is answered from the finest grid
that covers the place and has water in that cell, at the nearest grid node;
nothing is interpolated in space or time.

`Grid.constants(lon, lat)` returns the amplitude and phase of each
constituent, for anyone who wants the harmonics rather than a value.

`Coast` is separate from the model: `rings(level)` gives the land polygons
as longitude and latitude, and `is_land(lon, lat)` tests a point. The model
has its own idea of where water is (a cell either has constants or does
not); the coastline is for drawing and is finer than the model's grids.

## Coverage

Longitude 126.40 W to 122.54 W, latitude 48.13 N to 50.20 N: Juan de Fuca
Strait, Haro and Rosario Straits and the San Juan and Gulf Islands, the
Strait of Georgia, Burrard Inlet, Howe Sound, Sechelt Inlet and Discovery
Passage to Brown Bay. Puget Sound south of Admiralty Inlet is outside it.

Eleven passes have their own 10 m grids: Seymour Narrows, Sechelt Rapids, Dodd
Narrows, Gabriola Passage, Porlier Pass, Active Pass, First and Second
Narrows, Calamity Point, Tillicum Bridge and Race Passage. Two regional
grids (about 60 m) cover the Active Pass and Sechelt areas. Everything else
is read from the full-domain grid at about 180 by 130 m.

`flow.pack` stops at the Canada-US boundary. The pyramid does not.

## What the numbers mean, and do not

- **The current is a near-surface current**, about the top five metres. The
  hydrodynamic model computes the depth-mean flow; each cell is scaled by a
  log-layer factor between 1.04 and 1.25 fitted to the model's own vertical
  profiles. `MODEL.md` says why and what it costs.
- **The tide is astronomical only.** No weather, no river. A real water
  level differs from it by storm surge and freshet, tens of centimetres on
  an ordinary day and more in a storm.
- **Heights are about mean water level**, not chart datum. To compare with
  a tide table, add the port's mean water level above chart datum.
- **Seven constituents, no nodal corrections.** The constants were fitted
  for 2025. Other years are off by the nodal modulation, a few per cent of
  amplitude.
- **It is a model.** `MODEL.md` gives the measured errors. The short
  version: tide timing in the Strait of Georgia is within a few degrees of
  phase (minutes); pass currents turn about ten minutes early on average and
  run from 15% fast to 40% slow against the published reference rates;
  diurnal tides are 10 to 15% small.

**Not for navigation.** This is a research model. It has known errors, it
has no warranty, and nobody should rely on it to transit a pass. Use the
Canadian Tide and Current Tables.

## Version

**v2**, exported 2026-11-06 from the 32-day run
`all7-south-closed-hom3d-admflux-dt30-day32-r96-v2`, with the current at the
near-surface level described in `MODEL.md`. The manifest records the fit and
the velocity export in full. "v2" is that run's own label: its first
attempt was stopped when a narrows ran dry, and v2 is the corrected rerun.
The two-dimensional model the apps shipped before it is not here.

## License

The model weights and the code: not yet chosen. Until a license file is
added, all rights are reserved.

`weights/coast.pack` is a database derived from OpenStreetMap and is made
available under the Open Database License 1.0, whatever is chosen for the
rest. Credit "(c) OpenStreetMap contributors" wherever it is used.
