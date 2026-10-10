# RF Digital Twin for Network Planning and Self-Healing

Coverage optimization, outage recovery, sparse radio-map reconstruction, mmWave beam
management, and handover tuning — all built on real ray-traced channel data.

**Data source:** DeepMIMO v4 — scenario `city_9_sanfrancisco_3p5` (3.5 GHz, C-band).
3 base stations, 40,376 candidate user locations, 53.6% ray-traced eligibility.

> **Note on repo contents:** this repo currently holds the full project report and its
> figures. The `rftwin` Python package described in the report (site selection,
> outage/healing, radio-map reconstruction, beam management, handover modules, shared
> KPI engine, and test suite) is referenced throughout but is not included here yet —
> add it with `git add` / `git push` once you have the source on hand.

## Headline findings

- **Beam management:** an ML model predicting the best transmit beam from user
  position and geometry cuts mean beamforming-gain loss from 23.7 dB to 6.1 dB versus
  a geometric baseline, at the same 87.5% reduction in beam-sweep overhead.
- **Outage resilience:** the busiest site (BS0) carries 6.6 percentage points of
  coverage on its own; a neighbor power-boost self-healing rule recovers 54% of the
  coverage lost when it fails.
- **Radio-map reconstruction:** gradient boosting and Gaussian-process kriging cut
  coverage-map error roughly in half versus a naive distance-based estimate, from
  measurements covering only 5% of the area.
- **Site planning:** the existing 3-site deployment tops out at 78.5% coverage; a 95%
  target is mathematically infeasible without adding sites.
- **Handover tuning:** the optimal parameter pair (6 dB hysteresis, 0.4 s
  time-to-trigger) is consistent across vehicle and pedestrian speeds, but the failure
  mode differs — slow users suffer more radio-link failures, fast users suffer more
  ping-pong handovers.

## Data and methodology

Channel data comes from DeepMIMO v4, a public ray-tracing-based channel dataset
generator built on Wireless InSite. The scenario ray-traces a real street segment of
San Francisco at 3.5 GHz (Verizon's deployed C-band). Per-BS/UE path loss, LoS state,
and up to 10 resolved multipath components per link feed every KPI in the report via a
standard link budget (100 MHz / 30 kHz SCS, 43 dBm Tx power, 15 dB Tx antenna gain,
7 dB noise figure, 0.6 neighbor-cell load, RSRP ≥ −105 dBm and SINR ≥ 0 dB for
coverage). Spectral efficiency uses an attenuated-Shannon mapping capped at
7.4 bits/s/Hz.

The pipeline is a Python package (`rftwin`) with one module per analysis, a shared KPI
engine, and a synthetic 3GPP-UMa-based generator used only to unit-test the pipeline
end-to-end before touching real data. Two real bugs were caught and fixed during
development against real data: a NaN-angle bug in beam-gain calculation from
DeepMIMO's padded "missing path" slots, and a kriging length-scale bound tuned for the
wrong spatial extent.

## Module summaries

1. **Site selection and coverage planning** — greedy search + ILP. 1 site: 65.5%
   coverage; 2 sites: 73.3%; all 3: 78.5%. A 95% target is infeasible with the current
   3 sites (confirmed by the ILP's relaxed, easier RSRP-only formulation).
2. **Outage impact and self-healing** — N−1 analysis + coordinate-ascent power-boost
   healing. BS0 is the critical site (6.6 pp coverage loss if it fails); self-healing
   recovers 54% of that loss. BS1's failure drops cell-edge throughput to 0 Mbps even
   where coverage nominally survives.
3. **Radio-map reconstruction from sparse measurements** — compares log-distance
   trend, inverse-distance weighting, kriging, and gradient boosting at 1–10% sampling,
   under both random and realistic route sampling. All three data-driven methods
   roughly halve the naive baseline's error at 5% sampling; route sampling degrades
   every method versus random sampling.
4. **mmWave beam management** — 64-beam DFT codebook, 32-element array. A
   position-aware random-forest beam predictor beats a geometric (LoS-assumption)
   baseline by 16.6–17.7 dB of beamforming gain across sweep budgets of 1–8 beams,
   concentrated in the 53.2% of users without a clear line of sight.
5. **Handover parameter tuning** — 200 simulated users at 30 and 120 km/h. Optimal
   setting (6 dB hysteresis, 0.4 s TTT) is stable across speeds, but slow users suffer
   nearly 3× the radio-link-failure rate of fast users, who instead generate more
   ping-pong handovers.

## Assumptions and limitations

- Ray-traced data omits most clutter (vehicles, foliage, pedestrians, weather) and
  uses simplified building materials — absolute dB/Mbps values are directional, not
  measured; relative comparisons between methods are the robust conclusions.
- All base stations are modeled as omnidirectional; real deployments use 3-sector
  patterns and tilt, which the outage power-headroom proxy approximates only coarsely.
- Link-budget parameters are engineering assumptions layered on DeepMIMO's path loss,
  not measured values — calibrate against real drive-test/MDT data before using any
  number here for a live capital or configuration decision.
- Only 3 base stations limits the resolution of the site-selection and outage
  analyses.
- Throughput uses an attenuated-Shannon approximation and is not load-aware.

## Future work

Model 3-sector antenna patterns and tilt explicitly; add a second, higher-site-count
scenario; compare this C-band scenario against the same city's mmWave (28 GHz)
scenario to quantify the coverage/capacity trade-off directly; calibrate link-budget
assumptions against real drive-test data from a live market.

## Contents

- [`RF_Digital_Twin_Project_Report.docx`](RF_Digital_Twin_Project_Report.docx) — full
  report with methodology, all figures, and the complete module-by-module discussion.
- [`figures/`](figures/) — the 13 figures from the report (coverage maps, outage
  analysis, radio-map RMSE curves, beam-management gain, handover cost surfaces,
  reference RSRP/SINR/throughput maps).

## License

MIT.
