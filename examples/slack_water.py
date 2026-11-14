"""Slack water and maximum current in a pass over a day.

A pass has one axis the water runs along. This finds it from the model's own
M2 constants, projects the current onto it, and reports each turn (the
along-axis current crossing zero) and each maximum between turns.

    python examples/slack_water.py                              # Dodd Narrows, today
    python examples/slack_water.py -125.350 50.1333 2025-07-04   # Seymour Narrows
"""
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from salish_tides import KNOTS_PER_M_S, Pyramid

root = Path(__file__).resolve().parent.parent
lon, lat = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (-123.8171, 49.1344)
day = (datetime.fromisoformat(sys.argv[3]) if len(sys.argv) == 4 else datetime.now(timezone.utc)).replace(
    hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

model = Pyramid(root / "weights" / "pyramid")
grid = model.grid_at(lon, lat)
if grid is None:
    sys.exit("no water in the model there")

# The axis: the direction of the M2 current when it is strongest.
(a_east, g_east), (a_north, g_north) = grid.constants(lon, lat)["M2"]
best = max(range(360), key=lambda d: math.hypot(a_east * math.cos(math.radians(d - g_east)),
                                                  a_north * math.cos(math.radians(d - g_north))))
ax_e = a_east * math.cos(math.radians(best - g_east))
ax_n = a_north * math.cos(math.radians(best - g_north))
norm = math.hypot(ax_e, ax_n)
ax_e, ax_n = ax_e / norm, ax_n / norm
bearing = math.degrees(math.atan2(ax_e, ax_n)) % 360
print(f"{grid.name} grid ({grid.cell_metres[0]:.0f} m cells); axis {bearing:.0f} / {(bearing + 180) % 360:.0f} deg true; times UTC")

step = timedelta(minutes=1)
along = []
for minute in range(24 * 60 + 1):
    east, north = model.current(lon, lat, day + minute * step)
    along.append(east * ax_e + north * ax_n)

last_turn = 0
for i in range(1, len(along)):
    if along[i - 1] * along[i] < 0:
        peak = max(range(last_turn, i), key=lambda j: abs(along[j]))
        if last_turn:
            toward = bearing if along[peak] > 0 else (bearing + 180) % 360
            print(f"  {day + peak * step:%H:%M}  max   {abs(along[peak]) * KNOTS_PER_M_S:4.1f} kn toward {toward:3.0f} deg")
        print(f"  {day + i * step:%H:%M}  slack")
        last_turn = i
