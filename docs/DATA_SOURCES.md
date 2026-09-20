# Data sources, units, time windows, and location selection

This document describes translation version 0.3.2. A value is replaced only when source, time window, location, and related fields are compatible. Reports distinguish official, derived, and mixed assignments. Assignment counts include validated values that were numerically unchanged; they are not a percentage of the entire response and are not a guarantee of forecast accuracy.

## Source ownership

The proxy begins with an Apple native response. It is a selective Taiwan override, not a complete weather provider.

| Field group | Source | Mapping boundary |
|---|---|---|
| Current temperature, humidity, wind | CWA O-A0001-001 / O-A0003-001 | Nearest fresh valid station; wind m/s becomes km/h and humidity fraction becomes percent |
| Temperature-analysis grid | CWA O-A0038-003 | Diagnostics only; never replaces an incomplete station thermodynamic group |
| Hourly temperature, humidity, dew point, apparent temperature, wind | CWA F-D0047 | Exact same-time points only; thermodynamic group must be complete and physically consistent |
| Current dew point | Same-station temperature and humidity | Derived with the Magnus formula; never filled from a different forecast time |
| Daily high/low | Today's validated station `DailyExtreme` plus remaining exact hours; complete 24-hour samples for future days | Local 00:00-24:00 day; value and occurrence time are updated together; explicitly derived |
| Weather code/icon | CWA observation or F-D0047 text | Known clear/cloud/rain/snow/thunder/fog mapping; unknown conditions remain Apple |
| UV | Fresh station or daily F-D0047 value | Current and daily maximum; the hourly UV curve remains Apple |
| Observed rain | CWA O-A0002-001 | Must match `current.asOf` and compatible companions; trace `T` is recorded but not converted to 0.05 mm |
| Current rain intensity | Apple | Ten-minute accumulation is not treated as instantaneous intensity |
| Next-hour QPF | CWA F-B0046-001 | One specific radar-extrapolation interval, with issue and validity times retained |
| Longer precipitation | CWA M-A0064 WRF 3 km | Same-run APCP cumulative differences in six-hour windows from +6 to +72 hours; lead/time consistency required |
| Hourly/daily rain amount | Exact radar or same-run WRF windows | Complete, non-overlapping source windows only; no fractional allocation or radar/model blending |
| Probability of precipitation | Exactly matching CWA interval | No splitting or synthesis; conflicting duplicates retain Apple |
| Pressure | Station observation plus elevation, or WRF sea-level pressure | Station and sea-level pressure remain distinct; derived values are labeled |
| Current gust/visibility | Fresh station | Gust approximately 30 minutes; visibility approximately 90 minutes and category values are representative bounds |
| AQI and pollutants | Taiwan MOENV data delivered through CWA LinkedAPI | Taiwan AQI; CO ppm becomes ppb; the separate native scale endpoint remains incompatible |
| Warnings | CWA W-C0033-002 | Active-time and region filtering; merged with non-CWA Apple alerts |
| Sunrise, sunset, transit, civil twilight, moonrise/moonset | CWA A-B0062-001 / A-B0063-001 | Current-year query and local-date match at a county representative point |

The full minute-by-minute `forecastNextHour` root remains Apple. Radar QPF supplies an interval total only; it does not create a synthetic minute-level curve. Moon phase, illumination, nautical/astronomical twilight, map tiles, proprietary comparisons, and unknown protocol fields also remain Apple.

## Location selection

The proxy reads latitude and longitude from the WeatherKit URL. It handles `country=TW` within 20-27 degrees north and 117-124 degrees east. The public IP of the selected exit node has no role in location selection.

- Core station observations: nearest station within 30 km, updated within 90 minutes, with valid temperature.
- Rain gauge: separately selected within 30 km and 30 minutes.
- Visibility: within 50 km and 90 minutes.
- Source clocks may be up to five minutes ahead.
- Township forecasts: nearest of 368 representative points within 60 km.
- WRF: precomputed township grid points.
- AQI and astronomy: their own distance and representative-location constraints.

Nearest-point matching is approximate near administrative boundaries and in mountainous terrain. Source reports retain station names and distances.

## Apple-retained scope

Apple remains authoritative for unmatched hourly/daily PoP, incomplete rainfall/extrema groups, current apparent temperature, instantaneous rain intensity, minute rain timing, weather maps, cloud layers, forecast gust/visibility, hourly UV, pressure trends, unsupported precipitation phase/distribution fields, moon phase/illumination, nautical/astronomical twilight, news, historical comparisons, proprietary summaries, unknown slots, CWA gaps, and locations outside Taiwan.

This list describes the current integration, not a claim that CWA has no other relevant products.

## Method limits

PoP cannot be uniquely disaggregated; version 0.3.2 uses exact original intervals only. Daily extrema from hourly samples can miss a continuous-time peak. Mixed Apple summaries or icons may disagree with a CWA observation. Preserve observation/forecast semantics instead of changing values merely for visual consistency.

The WRF worker relies on the current file layout but validates GRIB magic, length, parameter, step, level, ETag, and lead time. Layout changes fail closed. A complete dynamic GRIB message index is not yet implemented.

Research snapshots are in `docs/reference/`. Recheck current CWA interfaces before adding a product:

- REST: <https://opendata.cwa.gov.tw/api/v1/rest/datastore/>
- File API: <https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/>
- LinkedAPI: <https://opendata.cwa.gov.tw/linked/graphql>
