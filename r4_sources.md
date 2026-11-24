# Verified source index (2026-11-23)
- Official challenge: https://moonbasechallenge.org/rules/ and https://moonbasechallenge.org/power-generation-storage/ . Human screening remains required.
- NASA PGDA high-resolution LOLA south-pole DEMs: https://pgda.gsfc.nasa.gov/products/78 . Candidate regions; elevation error affects illumination.
- NASA PGDA polar illumination: https://pgda.gsfc.nasa.gov/products/69 . Long-term averages are NOT chronological availability.
- NASA SVS 2023–2030: https://svs.gsfc.nasa.gov/4930/ . Time-dependent visualization; not a validated site power time series.
- LOLA PDS archive: https://imbrium.mit.edu/ .
- LROC time-weighted illumination: https://data.lroc.im-ldi.com/lroc/view_rdr/WAC_POLE_ILL_TWI_SOUTH . Useful for site screening only.
- Hayne et al., Diviner thermophysical properties: https://doi.org/10.1002/2017JE005387 . Temperature dependence of native fines; do not extrapolate to molten core.
- Semitransparent TPV: https://doi.org/10.1073/pnas.2215977119 . 32.5% laboratory conversion at 1036 Celsius, specialized cell; not system-level HELIOS validation.
- NASA-CR-189073 index: https://ntrs.nasa.gov/search?q=NASA-CR-189073 . Prior art, not proof of originality or containment.

## Data acquisition contract
Select site and projection, obtain DEM with coverage beyond local ridges, record product ID, resolution, vertical datum, SHA256 and uncertainty; obtain timestamped Sun vectors in matching lunar frame; verify horizon against NASA products; retain consecutive darkness durations and compare measured/derived illumination. Never substitute average illumination for chronological storage dispatch. No actual site raster or ephemeris has been downloaded or validated in this branch yet.
