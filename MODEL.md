# The model

## How it was made

A SCHISM hydrodynamic model of the Salish Sea on an unstructured mesh of
2.64 million nodes, about 6 m in the passes and coarser in open water, with
depths from the Canadian Hydrographic Service's 10 m NONNA bathymetry where
it exists. The run behind these weights is a homogeneous (unstratified)
three-dimensional one with 13 vertical levels and a k-kl turbulence
closure, forced for 32 days with seven tidal constituents at the ocean and
northern boundaries, the tide-generating potential, and the tidal prisms of
Puget Sound and Samish Bay as prescribed transports where the mesh ends.

The last 30 days of hourly output were fitted, node by node, with a mean
and the six constituents a month can separate (M2 S2 N2 K1 O1 Q1). P1
cannot be separated from K1 in 30 days, so it is carried at the fixed ratio
and lag the region's gauges show (0.283 of K1, 20.8 degrees later). The
fitted constants were then sampled onto the grids here.

## The current is exported near the surface

The model computes the depth-mean current. A boat is at the surface, and
the published current tables describe the surface. In a tidal pass the
surface runs faster than the depth mean, and the three-dimensional run's
own vertical profiles put that at 10 to 19% at the ten reference passes.

So every velocity coefficient is scaled, cell by cell, by

    1 + 0.9 * sqrt(g n^2 / max(H, 1)^(1/3)) / 0.41

with `H` the depth and `n` the model's bed roughness there. The factor
runs from 1.04 to 1.25 with a median of 1.12. The coefficient 0.9 is about
60% of the model's full surface excess, a level chosen because it scored
best across the reference passes, ferry tracks and current atlas together.

The cost: the same factor is applied in the deep, stratified straits, where
moored current meters show the upper water running at the depth mean. There
the export is about 10% too strong. `manifest.json` records the factor, so
it can be divided out.

## How it scores

Each figure is observed over modelled, so a value above 1 means the model
is too weak. Timing is model minus observed, in minutes; negative is early.
Each constituent's phase error is converted at its own period, so one
degree is 2.1 minutes for M2 and N2 and 4.0 minutes for K1.

| against | measure | result |
|---|---|---|
| 46 tide gauges | M2 amplitude, median | 0.95 |
| | M2 timing, mean and RMS | −3 and 7 min |
| | N2 timing RMS | 16 min |
| | K1 and O1 amplitude, median | 1.15 and 1.10 |
| | K1 timing RMS | 7 min |
| 10 CHS reference passes | M2 peak current, median | 1.06 |
| | within 0.7 to 1.3 | 8 of 10 |
| | M2 timing at the peak, mean and RMS | −11 and 24 min |
| 25 NOAA current-meter moorings | M2 against the depth average, median | 0.89 |
| | M2 timing RMS | 26 min |
| CHS current atlas, 2025, open water | direction error, median | 9.5° |
| | speed, model over the printed band's middle | 0.88 |
| ferry tracks, summer 2023 | observed cross-current against modelled, slope | 0.97 |

By pass, observed over modelled M2 peak current and its timing there:

| pass | amplitude | timing |
|---|---:|---:|
| Seymour Narrows | 1.41 | −17 min |
| Sechelt Rapids | 1.20 | −18 min |
| First Narrows | 1.15 | −8 min |
| Active Pass | 1.14 | −3 min |
| Dodd Narrows | 1.11 | −16 min |
| Gabriola Passage | 1.00 | −12 min |
| Porlier Pass | 0.99 | −19 min |
| Second Narrows | 0.90 | +10 min |
| Calamity Point | 0.86 | +10 min |
| Tillicum Bridge | 0.54 | −63 min |

## Where it is wrong

- **Seymour Narrows is 40% slow.** The model's northern boundary is just
  beyond it, at Brown Bay, and the narrows inherit that.
- **The diurnal tides are small**, K1 by 15% and O1 by 10%, from eastern
  Juan de Fuca inward. On this coast the diurnals are as large as the
  semidiurnals, so high and low water heights are off by up to 15 cm.
- **Rosario and Haro Strait currents turn early**, by 30 to 35 minutes, and
  Haro runs strong.
- **The Strait of Georgia's open-water currents are weak**, about a quarter under
  the current atlas in the southern Strait.
- **Tillicum Bridge (the Gorge) is twice too fast** and an hour early.
- **Drying ground is crude.** Depths are floored at 2 m, so flats that bare
  at low water stay wet in the model. The tide on a drying cell is clipped
  at its bed; read tide heights from water at least 3 m deep, which is what
  `TidePack` does by averaging and searching nearby nodes.
- **No stratification, wind, river flow or weather.** The Fraser plume's
  surface currents and any storm surge are absent.

## Sources

Bathymetry: Canadian Hydrographic Service NONNA-10; NOAA NCEI and ENC
soundings in US waters. Shoreline: OpenStreetMap. Boundary tides: TPXO and
gauge harmonics. Validation: CHS tide and current predictions and current
atlas; NOAA CO-OPS harmonic constants; NOAA Marine Cadastre AIS.
