"""A small chart: the coastline with the current drawn as arrows, as an SVG.

    python examples/chart_svg.py                          # Active Pass, now
    python examples/chart_svg.py -123.75 49.10 -123.60 49.20 2025-07-04T17:00 out.svg

Arguments: west south east north [time, UTC] [output file].
"""
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tidal_atlas import KNOTS_PER_M_S, Coast, Pyramid

root = Path(__file__).resolve().parent.parent / "weights"
args = sys.argv[1:]
west, south, east, north = (float(v) for v in args[:4]) if len(args) >= 4 else (-123.36, 48.84, -123.27, 48.89)
when = (datetime.fromisoformat(args[4]).replace(tzinfo=timezone.utc) if len(args) >= 5
        else datetime.now(timezone.utc))
out = Path(args[5] if len(args) >= 6 else "chart.svg")

# A plain equirectangular drawing, squared up at the box's latitude.
width = 900
aspect = math.cos(math.radians((south + north) / 2))
height = round(width * (north - south) / ((east - west) * aspect))
x = lambda lon: (lon - west) / (east - west) * width
y = lambda lat: (north - lat) / (north - south) * height

coast = Coast(root / "coast.pack")
metres_per_pixel = (east - west) * 111_320 * aspect / width
level = max(i for i, t in enumerate(coast.TOLERANCES_M) if t <= max(metres_per_pixel, 1))
path = []
for ring in coast.rings(level):
    lon, lat = ring[:, 0], ring[:, 1]
    if lon.max() < west or lon.min() > east or lat.max() < south or lat.min() > north:
        continue
    path.append("M" + "L".join(f"{x(a):.1f},{y(b):.1f}" for a, b in ring) + "Z")

model = Pyramid(root / "pyramid")
arrows = []
step = 30  # pixels between arrows
for py in range(step // 2, height, step):
    for px in range(step // 2, width, step):
        lon = west + px / width * (east - west)
        lat = north - py / height * (north - south)
        current = model.current(lon, lat, when)
        if current is None:
            continue
        knots = math.hypot(*current) * KNOTS_PER_M_S
        if knots < 0.1:
            continue
        length = min(step * 0.9, 6 + 5 * knots)
        angle = math.degrees(math.atan2(current[0], current[1]))  # clockwise from north
        arrows.append(f'<g transform="translate({px},{py}) rotate({angle:.0f})">'
                      f'<path d="M0,{length / 2:.1f}V{-length / 2:.1f}m-3,5l3,-5l3,5"/></g>')

out.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
<rect width="{width}" height="{height}" fill="#dbe9f4"/>
<path d="{"".join(path)}" fill="#e9e4d4" stroke="#8a8370" stroke-width="0.6" fill-rule="nonzero"/>
<g fill="none" stroke="#1d4e89" stroke-width="1.3" stroke-linecap="round">{"".join(arrows)}</g>
<text x="8" y="{height - 8}" font-family="sans-serif" font-size="12" fill="#333">{when:%Y-%m-%d %H:%M} UTC; coastline (c) OpenStreetMap contributors</text>
</svg>
''')
print(f"wrote {out}: {len(path)} coastline rings at the {coast.TOLERANCES_M[level]} m level, {len(arrows)} arrows")
