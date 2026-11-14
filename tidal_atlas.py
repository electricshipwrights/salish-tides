"""Read the Salish Sea tidal model: currents and tide heights at any place and time.

The model is a set of harmonic constants on grids. At every wet cell it
stores a mean and a cosine/sine pair for each of seven tidal constituents
(M2 S2 N2 K1 O1 Q1 P1), for the east and north components of the current
and for the height of the tide. A value at an instant is

    value(t) = mean + sum_k [ a_k cos(w_k (t - epoch)) + b_k sin(w_k (t - epoch)) ]

with t in seconds since the model's time origin (2025-01-01T00:00:00Z) and
w_k the constituent's angular frequency in radians per second. Nothing is
interpolated in time and nothing expires: the same constants answer for any
date. They carry no nodal corrections, so they are most exact for 2025 and
drift by a few per cent of amplitude over the 18.6-year nodal cycle.

Three readers, one per file format, all with the same two questions:

    Pyramid("weights/pyramid")   the full model: currents and tide heights,
                                 14 nested grids, 180 m down to 10 m
    FlowPack("weights/flow.pack")  currents only, Canadian waters only, the
                                 same grids tiled and compressed for fast
                                 random access
    TidePack("weights/tide.pack")  tide heights only, one 730 m grid

    model.current(lon, lat, when)  -> (east, north) in m/s, or None
    model.tide(lon, lat, when)     -> metres about mean water level, or None

`when` is a `datetime` (naive ones are taken as UTC) or Unix seconds.
Depends on numpy and the standard library.
"""

from __future__ import annotations

import base64
import json
import math
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

__all__ = ["Pyramid", "FlowPack", "TidePack", "Grid", "speed_and_bearing", "KNOTS_PER_M_S"]

KNOTS_PER_M_S = 1.943844


def _unix(when) -> float:
    if isinstance(when, (int, float)):
        return float(when)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.timestamp()


def speed_and_bearing(east: float, north: float) -> tuple[float, float]:
    """Speed in m/s and the direction the water is going, degrees true."""
    return math.hypot(east, north), math.degrees(math.atan2(east, north)) % 360.0


def _factors(frequencies, epoch, model_time):
    """[1, cos w1 t, sin w1 t, cos w2 t, ...] at a model time."""
    out = [1.0]
    for w in frequencies:
        angle = w * (model_time - epoch)
        out += [math.cos(angle), math.sin(angle)]
    return np.array(out)


class Grid:
    """One node-registered grid of harmonic constants (one pyramid file).

    Row 0 is the southern edge and column 0 the western; node (row, col) is at
    `south + row * (north - south) / (ny - 1)`, likewise in longitude.

    `velocity` has shape (coefficients, 2, ny, nx) in mm/s, component 0 east
    and 1 north; `elevation` (coefficients, ny, nx) in mm; `depth` (ny, nx) in
    decimetres below the model's datum. Coefficient 0 is the mean, then a
    cosine and a sine plane per constituent. A cell with no water is
    `sentinel` in every plane.
    """

    def __init__(self, path):
        doc = json.loads(Path(path).read_text())
        self.name = Path(path).name.removesuffix("-flow.json")
        self.west, self.south, self.east, self.north = doc["bbox"]
        self.nx, self.ny = doc["nx"], doc["ny"]
        self.constituents = doc["constituents"]
        self.frequencies = doc["harmonicFrequencies"]
        self.epoch = doc["harmonicEpoch"]
        self.time_origin = doc["timeOriginUnix"]
        self.sentinel = doc["sentinel"]
        self.cell_metres = doc["raster"]["cellMetres"]
        self.velocity_level = doc.get("velocity", {"level": "depthMean"})
        count = 1 + 2 * len(self.frequencies)

        def planes(key, shape):
            raw = zlib.decompress(base64.b64decode(doc[key]))
            return np.frombuffer(raw, dtype="<i2").reshape(shape)

        self.velocity = planes("harmonicsB64", (count, 2, self.ny, self.nx))
        self.elevation = planes("elevationHarmonicsB64", (count, self.ny, self.nx))
        self.depth = planes("depthB64", (self.ny, self.nx))

    def contains(self, lon, lat) -> bool:
        return self.west <= lon <= self.east and self.south <= lat <= self.north

    def cell(self, lon, lat) -> tuple[int, int]:
        """The nearest node, as (row, col)."""
        col = round((lon - self.west) / (self.east - self.west) * (self.nx - 1))
        row = round((lat - self.south) / (self.north - self.south) * (self.ny - 1))
        return row, col

    def current(self, lon, lat, when):
        row, col = self.cell(lon, lat)
        planes = self.velocity[:, :, row, col]
        if (planes == self.sentinel).any():
            return None
        east, north = _factors(self.frequencies, self.epoch, _unix(when) - self.time_origin) @ planes * 0.001
        return float(east), float(north)

    def tide(self, lon, lat, when):
        row, col = self.cell(lon, lat)
        planes = self.elevation[:, row, col]
        if (planes == self.sentinel).any():
            return None
        return float(_factors(self.frequencies, self.epoch, _unix(when) - self.time_origin) @ planes * 0.001)

    def constants(self, lon, lat, field="current"):
        """Amplitude and phase per constituent at the nearest node.

        Phase g is in `A cos(w t - g)` with t from the time origin, degrees.
        For "current" each entry is ((A_east, g_east), (A_north, g_north)) in
        m/s; for "tide" it is (A, g) in metres. None on a dry cell.
        """
        row, col = self.cell(lon, lat)
        planes = self.velocity[:, :, row, col] if field == "current" else self.elevation[:, row, col][:, None]
        if (planes == self.sentinel).any():
            return None
        out = {}
        for k, (name, w) in enumerate(zip(self.constituents, self.frequencies)):
            a, b = planes[1 + 2 * k] * 0.001, planes[2 + 2 * k] * 0.001
            amp = np.hypot(a, b)
            phase = (np.degrees(np.arctan2(b, a)) + math.degrees(w * self.epoch)) % 360.0
            pairs = [(float(x), float(g)) for x, g in zip(amp, phase)]
            out[name] = tuple(pairs) if field == "current" else pairs[0]
        return out


class Pyramid:
    """The full model: every grid in a directory, finest first.

    A question is answered by the finest grid that covers the place and has
    water in that cell, so a point in Active Pass is read from its 10 m grid
    and a point in the open Strait from the 300 m one.
    """

    def __init__(self, directory):
        directory = Path(directory)
        manifest = json.loads((directory / "manifest.json").read_text())
        self.manifest = manifest
        self.grids = sorted((Grid(directory / a["file"]) for a in manifest["artifacts"]),
                            key=lambda g: (g.east - g.west) / g.nx)

    def current(self, lon, lat, when):
        """(east, north) in m/s from the finest grid with water there, else None."""
        for grid in self.grids:
            if grid.contains(lon, lat):
                value = grid.current(lon, lat, when)
                if value is not None:
                    return value
        return None

    def tide(self, lon, lat, when):
        """Tide height in metres about mean water level, else None."""
        for grid in self.grids:
            if grid.contains(lon, lat):
                value = grid.tide(lon, lat, when)
                if value is not None:
                    return value
        return None

    def grid_at(self, lon, lat):
        """The finest grid with water at a place: the one `current` reads."""
        for grid in self.grids:
            if grid.contains(lon, lat):
                row, col = grid.cell(lon, lat)
                if grid.velocity[0, 0, row, col] != grid.sentinel:
                    return grid
        return None


class FlowPack:
    """`flow.pack`: the currents, tiled for random access without loading it all.

    The same grids as the pyramid, finest first, with the cells in US waters
    removed and no tide heights or depths. Each grid's planes are cut into
    32 x 32-cell tiles, each deflated on its own; a lookup inflates one tile.
    """

    TILE = 32

    def __init__(self, path, cache_tiles=256):
        self._data = memoryview(Path(path).read_bytes())
        d = self._data
        if bytes(d[:8]) != b"FLOWPAK1":
            raise ValueError("not a flow pack")
        data_start, count, tile = struct.unpack_from("<QII", d, 8)
        if tile != self.TILE:
            raise ValueError("unexpected tile size")
        self._cache, self._cache_limit = {}, cache_tiles
        self.fields = []
        o = 24

        def text():
            nonlocal o
            (n,) = struct.unpack_from("<I", d, o)
            s = bytes(d[o + 4:o + 4 + n]).decode()
            o += 4 + n
            return s

        for index in range(count):
            f = {"name": text(), "index": index}
            f["west"], f["south"], f["east"], f["north"], f["nx"], f["ny"], nf = struct.unpack_from("<4dIII", d, o)
            o += 44
            f["frequencies"] = list(struct.unpack_from(f"<{nf}d", d, o))
            o += 8 * nf
            f["epoch"], f["time_origin"], nc = struct.unpack_from("<ddI", d, o)
            o += 20
            f["constituents"] = [text() for _ in range(nc)]
            sentinel, f["tiles_x"], f["tiles_y"], index_offset = struct.unpack_from("<iIIQ", d, o)
            o += 20
            f["sentinel"] = sentinel
            f["index_offset"] = data_start + index_offset
            f["planes"] = 2 * (1 + 2 * nf)
            self.fields.append(f)
        self._data_start = data_start

    def _tile(self, f, tx, ty):
        key = (f["index"], tx, ty)
        if key in self._cache:
            return self._cache[key]
        entry = f["index_offset"] + (ty * f["tiles_x"] + tx) * 12
        offset, length = struct.unpack_from("<QI", self._data, entry)
        tile = None
        if length:
            tw = min(self.TILE, f["nx"] - tx * self.TILE)
            th = min(self.TILE, f["ny"] - ty * self.TILE)
            start = self._data_start + offset
            raw = zlib.decompress(self._data[start:start + length], -15)  # raw deflate
            tile = np.frombuffer(raw, dtype="<i2").reshape(f["planes"], th, tw)
        if len(self._cache) >= self._cache_limit:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = tile
        return tile

    def current(self, lon, lat, when):
        """(east, north) in m/s from the finest grid with water there, else None."""
        unix = _unix(when)
        for f in self.fields:
            if not (f["west"] <= lon <= f["east"] and f["south"] <= lat <= f["north"]):
                continue
            col = round((lon - f["west"]) / (f["east"] - f["west"]) * (f["nx"] - 1))
            row = round((lat - f["south"]) / (f["north"] - f["south"]) * (f["ny"] - 1))
            tile = self._tile(f, col // self.TILE, row // self.TILE)
            if tile is None:
                continue
            # planes run coefficient 0 east, coefficient 0 north, coefficient 1 east, ...
            values = tile[:, row % self.TILE, col % self.TILE]
            if (values == f["sentinel"]).any():
                continue
            factors = _factors(f["frequencies"], f["epoch"], unix - f["time_origin"])
            return float(factors @ values[0::2] * 0.001), float(factors @ values[1::2] * 0.001)
        return None


class TidePack:
    """`tide.pack`: the height of the tide on one coarse grid (about 730 m).

    The full-domain grid's tide constants averaged over 4 x 4 cells. The
    height of the tide changes over kilometres, so nothing a plot would show
    is lost, and the file is under half a megabyte.
    """

    REACH = 3  # nodes searched for the nearest one with water

    def __init__(self, path):
        d = Path(path).read_bytes()
        if d[:8] != b"TIDEPAK1":
            raise ValueError("not a tide pack")
        self.west, self.south, self.dx, self.dy, self.nx, self.ny, nf = struct.unpack_from("<4dIII", d, 8)
        o = 52
        self.frequencies = list(struct.unpack_from(f"<{nf}d", d, o))
        o += 8 * nf
        self.epoch, self.time_origin, self.sentinel, length = struct.unpack_from("<ddiI", d, o)
        o += 24
        raw = zlib.decompress(d[o:o + length])
        self.planes = np.frombuffer(raw, dtype="<i2").reshape(1 + 2 * nf, self.ny, self.nx)

    def tide(self, lon, lat, when):
        """Tide height in metres about mean water level at the nearest wet node, else None."""
        c0 = round((lon - self.west) / self.dx)
        r0 = round((lat - self.south) / self.dy)
        best = None
        for dr in range(-self.REACH, self.REACH + 1):
            for dc in range(-self.REACH, self.REACH + 1):
                r, c = r0 + dr, c0 + dc
                if not (0 <= r < self.ny and 0 <= c < self.nx) or self.planes[0, r, c] == self.sentinel:
                    continue
                if best is None or dr * dr + dc * dc < best[0]:
                    best = (dr * dr + dc * dc, r, c)
        if best is None:
            return None
        factors = _factors(self.frequencies, self.epoch, _unix(when) - self.time_origin)
        return float(factors @ self.planes[:, best[1], best[2]] * 0.001)
