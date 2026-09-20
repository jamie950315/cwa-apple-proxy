# Accuracy-preserving coverage research

Research date: 2026-09-20. No runtime or mapper changes were made. This is a proposal, not an accepted or deployed accuracy guarantee.

**Subsequent implementation:** the user approved applying this proposal. Version 0.3.2 deploys the coherent/exact-source groups and explicitly derived calendar-day extrema; unvalidated disaggregation, shifted day-part windows and +78/+84h extension remain disabled. See [acceptance evidence](evidence/accuracy-032.json). The research findings below retain their original context.

## Recommendation

Do not equate coverage with the number of overwritten bytes. Track three separate quantities by field, forecast horizon, and location: exact CWA-source coverage, independently validated CWA-derived coverage, and overall display availability (including preserved Apple data). Equal numeric values still count as source coverage when the official value was validated, even if no byte changed.

Use coherent groups rather than independent scalar replacements: temperature/humidity/dew point/source time; daily extrema/occurrence times/day window; precipitation totals/type companions/window/provenance. A group must not retain incompatible Apple metadata after a CWA override. Missing source information must not be invented merely to complete the group.

## Measured source compatibility

Twenty retained native responses were checked against their own CWA snapshots. These are correlated samples from the user's existing locations, not an all-Taiwan or independent forecast-skill evaluation.

| Native future temperature horizon | Slots present | Exact CWA points |
|---|---:|---:|
| Next 24 hours | 464 | 464 |
| Next 36 hours | 512 | 512 |
| Next 48 hours | 560 | 528 |
| Next 72 hours | 656 | 560 |
| Next 96 hours | 752 | 588 |

Across every future hourly slot present in those responses: 1,308 total, 588 exact CWA temperature matches, and another 152 supported by the current <=3h linear interpolation. This denominator includes longer Apple forecast horizons and is not interchangeable with the next-24h denominator.

Exact source-window PoP matches were 0/1,308 hourly slots, 0/200 daily slots, and 0/420 existing day-part slots. The CWA snapshots contained 3h, 6h (a partial interval), and 12h PoP windows. One native day-part pair ran 07:00–19:00 / 19:00–07:00, versus CWA 06:00–18:00 / 18:00–06:00. Copying the percentage without handling this offset is not an exact mapping.

## Temperature: preserve high coverage first

1. Preserve direct current observations and exact official forecast points. The sampled next-24h coverage is already complete without interpolation.
2. Keep current temperature, humidity, dew point and timestamps coherent. Grid temperature alone is not a complete replacement for a station thermodynamic state; choosing a complete station group trades spatial analysis detail for source consistency and needs geographical validation.
3. Existing O-A0001-001 station responses contain `DailyExtreme.DailyHigh/Low.TemperatureInfo`, including `AirTemperature` and `Occurred_at.DateTime`. These fields are currently unused. They can supply today's observed extrema without another download.
4. Today's observed extrema plus the remaining same-calendar-day hourly forecast can form a coherent **derived** daily product, with corresponding observed/predicted occurrence times. For future days, aggregate only a fully covered calendar day. Extrema of sampled hourly points are not guaranteed to equal the official continuous-period extrema; never label this as an unchanged official daily maximum/minimum.
5. Longer-horizon interpolation requires withheld-time validation and cross-field checks. Do not force the current temperature down to fit a forecast maximum.

## Rainfall: retain native windows and expand real source coverage

- [F-B0046-001](https://opendata.cwa.gov.tw/dataset/forecast/F-B0046-001) supplies a forecast accumulation for one specific next-hour interval. It does not by itself supply all subsequent hourly totals, nor an arbitrary rolling one-hour window starting at any request time.
- The currently used WRF [M-A0064](https://opendata.cwa.gov.tw/dataset/mathematics/M-A0064-000) source exposes six-hour leads. Bounded File API/S3 checks found 001/003/009 absent; deterministic six-hour totals cannot be represented as official hourly totals by division.
- The current worker stops at +72h. Public S3 HEAD confirmed +78h and +84h objects, suggesting a possible additional 12h of model coverage **from initialization**, not 84h guaranteed from the current time. Follow-up bounded Range reads did not return a usable 206/body and were interrupted. GRIB parameters, step metadata, same-cycle continuity and all 368 extracted values remain unverified; do not deploy this extension based on object existence alone.
- [F-C0041-001](https://opendata.cwa.gov.tw/dataset/forecast/F-C0041-001), -002 and -003 provide 0–6h, 6–12h and 12–18h quantitative forecast grids, but their official description limits them to land typhoon warning periods. They are a conditional source candidate, not a normal-year replacement or hourly source.
- Sum non-overlapping amounts only across an exactly covered target window and compatible initialization/source. Radar replacement of part of a model interval creates a blended forecast, not simultaneous preservation of both original totals.
- Replacing or omitting precipitation ByType companions must be tested with native consumers. No original Apple example with a positive scalar and empty ByType vector was found in the inspected sample; safe omission cannot be assumed from decoding alone. Do not fabricate phase splits or distribution bounds.
- A future temporal-disaggregation model may use finer forecast timing information as weights, but must be evaluated separately; conservation of total amount alone does not establish accurate hourly timing.

## PoP: an information constraint, not a missing arithmetic trick

[CWA's township product description](https://opendata.cwa.gov.tw/opendatadoc/Forecast/F-D0047-001_093.pdf) distinguishes hourly temperature-related factors from three-hour PoP; longer-period PoP is twelve-hour. This search did not identify a public, currently usable hourly or calendar-day PoP source. This is a research limit, not proof that no other product exists.

Preserve official probabilities only with their original event definition, location, issue time and full interval. Shifting native day-part windows to the official intervals may recover direct day/night coverage, but it would require a complete part-level rewrite and native UI validation; it is not a proven drop-in fix.

A constrained disaggregation model could preserve compatible aggregate probabilities, but still requires assumptions about temporal dependence and the observation threshold. Example: under an independent-block assumption, a 12h probability of 60% and nested 3h probability of 50% leave 20% for the remaining 9h, rather than the current naive recombination result of 74.8513% for the full 12h. This repairs aggregate consistency only; it does not prove any hourly probability. Inconsistent source constraints must be detected rather than silently blended.

Until a derived model passes independent verification, preserve Apple for the incompatible native hourly/daily PoP fields while exposing official CWA interval values in the diagnostics. That retains display availability without falsely claiming full CWA-source coverage.

## Acceptance gates and rollout

1. First repair source-group consistency and exact-window alignment; retain high direct temperature and observed-rain coverage.
2. Add verified longer native rainfall windows and today's already-available observed extrema. Validate source timestamps, units, freshness and companion fields before raising the coverage claim.
3. Evaluate derived products offline before deployment. Archive minimal forecast/observation records without credentials or precise user-location history; no archive or scheduled collector was installed during this research.
4. Use held-out dates and independent weather events, not randomly split adjacent hours. Evaluate temperature bias/MAE, calendar-day extrema errors, rainfall amount and event timing, and PoP Brier score/reliability against a matched observed-event definition. A short trial is not proof across seasons, mountains, typhoons or convective storms.
5. Report exact-source coverage and validated-derived coverage separately, with native Mac/iPhone/Watch acceptance. No policy can guarantee future weather to be error-free.
