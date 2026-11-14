# File formats

All three files hold the same thing: for each grid cell, a mean and a
cosine and sine coefficient per tidal constituent. A value at an instant is

    value(t) = c0 + sum_k [ a_k cos(w_k (t - epoch)) + b_k sin(w_k (t - epoch)) ]

- `t` is seconds since the time origin, `1735689600` (2025-01-01T00:00:00Z).
- `epoch` is `172800` s: the fit began 48 hours into the model run.
- `w_k` are the angular frequencies in radians per second, stored in each
  file, in the order M2 S2 N2 K1 O1 Q1 P1.
- There are 15 coefficients per quantity: `c0`, then `a_k, b_k` for each of
  the seven constituents.

All integers are little-endian. Coefficients are `int16`: velocity in
millimetres per second, elevation in millimetres, depth in decimetres. The
value `-32768` (the sentinel) in any plane marks a cell with no water.

Grids are node-registered with row 0 at the south and column 0 at the west.
Node `(row, col)` is at

    lon = west  + col * (east  - west ) / (nx - 1)
    lat = south + row * (north - south) / (ny - 1)

The amplitude of a constituent is `hypot(a, b)` and its phase lag, in
`A cos(w t - g)` with `t` from the time origin, is
`g = atan2(b, a) + w * epoch`.

## The pyramid: `weights/pyramid/*-flow.json`

One JSON object per grid, listed in `manifest.json` with each file's byte
count and SHA-256.

| key | meaning |
|---|---|
| `bbox` | `[west, south, east, north]` in degrees |
| `nx`, `ny` | grid size in nodes |
| `raster.cellMetres` | node spacing east-west and north-south |
| `constituents` | names, in coefficient order |
| `harmonicFrequencies` | `w_k`, radians per second |
| `harmonicEpoch` | `epoch`, seconds |
| `timeOriginUnix` | the time origin, Unix seconds |
| `sentinel` | `-32768` |
| `harmonicsB64` | velocity planes |
| `elevationHarmonicsB64` | tide-height planes |
| `depthB64` | the model's bed depth |
| `velocity` | which level the velocity is exported at, and the factor applied |
| `fit` | sample count, span and source stacks of the harmonic fit |
| `station`, `times` | one reference point's hourly series over the fit; not needed to use the model |

Each `...B64` value is base64 of a zlib stream of `int16`:

- `harmonicsB64`: shape `(15, 2, ny, nx)`. Coefficient, then component
  (0 east, 1 north), then row, then column.
- `elevationHarmonicsB64`: shape `(15, ny, nx)`.
- `depthB64`: shape `(ny, nx)`, decimetres, positive down, about the model's
  datum. Negative values are ground that dries.

## The flow pack: `weights/flow.pack`

Currents only. The same grids, finest first, cells in US waters set to the
sentinel, each grid's planes cut into 32 x 32-cell tiles and each tile
deflated on its own. A tile that is all land is not stored.

    "FLOWPAK1"            8 bytes
    u64  data start       offset of the data section from the file start
    u32  field count
    u32  tile side        32

    per field:
      u32 + bytes         name
      f64 x 4             west, south, east, north
      u32 x 2             nx, ny
      u32, f64 x n        frequency count, frequencies
      f64                 epoch
      f64                 time origin (NaN if absent)
      u32, then per name  constituent count; u32 length + bytes
      i32                 sentinel
      u32 x 2             tiles across, tiles down
      u64                 index offset, from the data start

    data section, per field:
      index: (u64 offset from the data start, u32 length) per tile,
             row-major; length 0 means an all-land tile
      tiles: raw deflate (no zlib header) of int16

A tile holds `2 * 15 = 30` planes of `tile_height x tile_width` cells, row
by row. Plane `2c` is coefficient `c` east and plane `2c + 1` coefficient
`c` north. Edge tiles are cut to the grid, so a tile's width is
`min(32, nx - 32 * tx)` and likewise its height.

## The coastline pack: `weights/coast.pack`

Land polygons from OpenStreetMap's coastline, at four levels of detail:
each ring simplified (Douglas-Peucker) to 1 m, 33 m, 167 m and 891 m.
Level 0 is the finest. It is not model output and does not depend on the
model version.

    "COASTLN1"            8 bytes
    u32                   level count (4)
    f64                   scale (10,000,000): stored integer = degrees * scale
    per level:            u64 offset of its first ring, u32 ring count

    per ring:
      u8                  1 if counter-clockwise (land), 0 if clockwise (water inside land)
      u32                 point count n
      f32 x 4             bounding box: west, south, east, north, degrees
      (i32, i32) x n      longitude, latitude, each degrees * scale

Rings are closed implicitly. Their orientation is the fill rule: put every
ring of a level in one path and fill it nonzero, and enclosed water comes
out as holes. Coordinates are WGS 84 longitude and latitude.

## The tide pack: `weights/tide.pack`

Tide heights only, on one grid: the full-domain elevation coefficients
averaged over 4 x 4 cells.

    "TIDEPAK1"            8 bytes
    f64 x 2               west, south: the position of node (0, 0)
    f64 x 2               node spacing in longitude and latitude
    u32 x 2               nx, ny
    u32, f64 x n          frequency count, frequencies
    f64                   epoch
    f64                   time origin
    i32                   sentinel
    u32                   compressed length
    bytes                 zlib of int16, shape (15, ny, nx), millimetres

A lookup takes the nearest node with water within three nodes, so a point
in a narrow pass or close to shore still has a tide.
