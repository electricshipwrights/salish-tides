"""The current at a place, now and over the next twelve hours.

    python examples/current_now.py                 # Active Pass
    python examples/current_now.py -125.350 50.1333    # Seymour Narrows
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tidal_atlas import KNOTS_PER_M_S, FlowPack, speed_and_bearing

lon, lat = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) == 3 else (-123.3128, 48.8604)
pack = FlowPack(Path(__file__).resolve().parent.parent / "weights" / "flow.pack")

start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
print(f"current at {lat:.4f} N, {-lon:.4f} W (UTC)")
for hour in range(13):
    when = start + timedelta(hours=hour)
    current = pack.current(lon, lat, when)
    if current is None:
        sys.exit("no water in the model there (land, US waters, or outside the domain)")
    speed, bearing = speed_and_bearing(*current)
    print(f"  {when:%Y-%m-%d %H:%M}  {speed * KNOTS_PER_M_S:4.1f} kn toward {bearing:3.0f} deg")
