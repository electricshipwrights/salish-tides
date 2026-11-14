"""The tide's height at a place through a day, as numbers and a small text plot.

    python examples/tide_curve.py                              # Point Atkinson, today
    python examples/tide_curve.py -123.371 48.424 2025-12-04   # Victoria
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from salish_tides import TidePack

lon, lat = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (-123.254, 49.337)
day = (datetime.fromisoformat(sys.argv[3]) if len(sys.argv) == 4 else datetime.now(timezone.utc)).replace(
    hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
tides = TidePack(Path(__file__).resolve().parent.parent / "weights" / "tide.pack")

print(f"tide at {lat:.3f} N, {-lon:.3f} W on {day:%Y-%m-%d} (UTC), metres about mean water level")
for half_hour in range(49):
    when = day + timedelta(minutes=30 * half_hour)
    height = tides.tide(lon, lat, when)
    if height is None:
        sys.exit("no water in the model near there")
    print(f"  {when:%H:%M} {height:+6.2f}  {' ' * int((height + 3.5) * 8)}*")
