"""Verify the weights: file hashes against the manifest, and the three readers
against each other.

    python check.py
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from tidal_atlas import Coast, FlowPack, Pyramid, TidePack

root = Path(__file__).resolve().parent / "weights"
manifest = json.loads((root / "pyramid" / "manifest.json").read_text())
bad = 0
for artifact in manifest["artifacts"]:
    data = (root / "pyramid" / artifact["file"]).read_bytes()
    ok = hashlib.sha256(data).hexdigest() == artifact["sha256"] and len(data) == artifact["bytes"]
    bad += not ok
    print(("ok   " if ok else "BAD  ") + artifact["file"])
for line in (root / "SHA256SUMS").read_text().splitlines():
    digest, name = line.split()
    ok = hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    bad += not ok
    print(("ok   " if ok else "BAD  ") + name)

pyramid, pack, tides = Pyramid(root / "pyramid"), FlowPack(root / "flow.pack"), TidePack(root / "tide.pack")
when = datetime(2025, 6, 10, 20, 0, tzinfo=timezone.utc)
places = {"Seymour Narrows": (-125.350, 50.1333), "Active Pass": (-123.3128, 48.8604),
          "Dodd Narrows": (-123.8171, 49.1344), "Strait of Georgia": (-123.5, 49.2),
          "Juan de Fuca": (-124.0, 48.40)}
for name, (lon, lat) in places.items():
    a, b = pyramid.current(lon, lat, when), pack.current(lon, lat, when)
    same = a is not None and b is not None and max(abs(a[0] - b[0]), abs(a[1] - b[1])) < 1e-9
    bad += not same
    print(("ok   " if same else "BAD  ") + f"{name}: pyramid and pack agree on the current")
    fine, coarse = pyramid.tide(lon, lat, when), tides.tide(lon, lat, when)
    close = fine is not None and coarse is not None and abs(fine - coarse) < 0.25
    bad += not close
    print(("ok   " if close else "BAD  ") + f"{name}: tide {fine:+.2f} m (pyramid) {coarse:+.2f} m (tide pack)")
us = (-122.75, 48.55)  # Rosario Strait: in the pyramid, cut from the pack
ok = pyramid.current(*us, when) is not None and pack.current(*us, when) is None
bad += not ok
print(("ok   " if ok else "BAD  ") + "US waters: in the pyramid, absent from the pack")
coast = Coast(root / "coast.pack")
ok = (coast.level_count == 4 and coast.is_land(-123.10, 49.26) and coast.is_land(-123.50, 48.80)
      and not coast.is_land(-123.5, 49.2) and not coast.is_land(-123.3128, 48.8604))
bad += not ok
print(("ok   " if ok else "BAD  ") + "coastline: Vancouver and Saltspring are land, the Strait and Active Pass are not")
sys.exit(1 if bad else 0)
