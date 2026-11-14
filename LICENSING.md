# Licensing

Three things are in this repository and each has its own terms. They are
as open as the data they were made from allows.

| what | terms |
|---|---|
| The code: `salish_tides.py`, `check.py`, `examples/` | MIT, see `LICENSE` |
| The coastline: `weights/coast.pack` | Open Database License 1.0 |
| The model: `weights/pyramid/`, `weights/flow.pack`, `weights/tide.pack` | Creative Commons Attribution-NonCommercial 4.0, with the notices below |

## The code

MIT. Do anything with it.

## The coastline

`weights/coast.pack` is a database derived from OpenStreetMap and is made
available under the Open Database License 1.0
(https://opendatacommons.org/licenses/odbl/1-0/). Any rights in individual
contents of the database are licensed under the Database Contents License
(https://opendatacommons.org/licenses/dbcl/1-0/).

Coastline data (c) OpenStreetMap contributors
(https://www.openstreetmap.org/copyright). If you publish a database derived
from this one, the ODbL requires you to offer it under the same licence. A
map or image drawn from it needs only the credit.

## The model

The model weights are licensed under Creative Commons
Attribution-NonCommercial 4.0 International
(https://creativecommons.org/licenses/by-nc/4.0/). You may copy, share and
adapt them for any non-commercial purpose with credit to Electric
Shipwrights and with the notices below kept.

They are not offered for commercial use, and that is not a choice made
here. The model was computed from Canadian Hydrographic Service data whose
licence forbids derivative products made for profit, and its ocean boundary
from a global tide solution offered for non-commercial use. Nobody downstream of
those terms can grant more than they do.

### Required notice: Canadian Hydrographic Service

The model's bathymetry and part of its boundary forcing come from the
Canadian Hydrographic Service. Its licence agreement requires this notice,
in these words, on any derivative product:

> This product is not to be used for navigation.
>
> This product was made by or for the User Electric Shipwrights and contains
> intellectual property (Data) of the Canadian Hydrographic Service of the
> Department of Fisheries and Oceans.
>
> The copyrights in the Data are and remain the property of His Majesty the
> King in Right of Canada and shall not be sold, licensed, leased, assigned
> or given to a third party.
>
> The incorporation of the Data in this product does not constitute an
> endorsement or an approval of this product by the Canadian Hydrographic
> Service, the Department of Fisheries and Oceans or His Majesty the King in
> Right of Canada

### Other sources

- Contains information licensed under the Open Government Licence - Canada
  (CHS NONNA-10 bathymetry).
- Base bathymetry from SalishSeaCast v21-08, (c) SalishSeaCast Project
  Contributors and The University of British Columbia, licensed under the
  Apache License, Version 2.0. Incorporates CHS data; CHS does not endorse
  this product.
- Bathymetry and US tidal constants from the National Oceanic and
  Atmospheric Administration (NCEI Strait of Juan de Fuca DEM, ETOPO 2022,
  Electronic Navigational Charts, CO-OPS). US Government work, public
  domain. NOAA does not endorse this product.
- Ocean boundary tides from the TPXO global tidal solution (Egbert and
  Erofeeva, Oregon State University).
- The model's shoreline was taken from OpenStreetMap. The weights are values
  on regular latitude and longitude grids and contain no OpenStreetMap
  geometry.
- Computed with SCHISM, (c) the SCHISM Development Team, Apache License 2.0.

## No warranty

The model and the code are provided as they are, without warranty of any
kind. The model has known errors, listed in `MODEL.md`. It is not to be used
for navigation.
