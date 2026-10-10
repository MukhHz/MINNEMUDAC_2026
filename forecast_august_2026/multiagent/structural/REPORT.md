# Structural & data-quality agent: report

(The agent was blocked from writing this file, so it was written from the agent's final message.
Numbers come from `results/summary.csv` and `results/diag_*.csv`.)

**Bottom line:** no structural model clearly beats `damped_yoy_3m`; they confirm it. July 2026 is not incomplete.

## Diagnostics (data through July 2026 only)

### (a) Late or partial reporting: July 2026 looks complete
- 462 sites reported in July 2026, 0.989 of the previous 3-month mean (normal range 0.97–1.04).
- 98.3% of June reporters also reported in July, equal to the Jan 2024–Jun 2026 average.
- 6 sites entered and 8 exited, both within normal ranges.
- 5 of the 431 sites that reported every month January–June 2026 are missing in July; all five reported zero visits.
- Partial-report signals (sites with July below half of their April–June average, or zero) are at the low end of history.
- July 2026 visits are down 8.0% vs July 2025. Of that, −7.6 points comes from sites that reported in both years, and 10 sites explain it.
- July 2025 was itself a spike: August 2025 came in 7.6% below July 2025.
- Pounds were up 1.7% year over year in July 2026, which doesn't fit a missing-reports story.

### (b) Where year-over-year change comes from (visits)
Same-site growth is change at sites that reported in both years; composition is sites starting or stopping reporting.

| Year | Total | Same-site | Composition |
|---|---|---|---|
| 2023 | +26.4% | +23.0 pt | +3.4 pt |
| 2024 | +15.3% | +16.2 pt | −0.9 pt |
| 2025 | +5.4% | +7.3 pt | −1.8 pt |

2026 YTD, visits / pounds / individuals: +0.9% / +3.4% / +4.1%. The May–July window: −4.8% / +0.5% / 0.0%.

### (c) August seasonality is unstable
Visits August/July ratio by year: 1.111 (2022), 1.125 (2023), 1.026 (2024), 0.924 (2025).
The 2022–23 ratios are inflated by the growth period, which is why the July × ratio models lose.

### (d) Outlier flags and repeated-value rows are immaterial
Removing them would change August year-over-year growth by under 0.4 points in 2024–25. The locked policy is unchanged.

## Models (full table in `results/summary.csv`)
Every competitive model forecasts visits at 234.4k–234.8k. Pounds forecasts span 11.90M–13.09M across models of similar skill.
The low end, from `xmetric_dyoy_12m_ratio`, uses an annual pounds-per-visit ratio below the August level.

Nominated `combo_dyoy_xmetric_fb` (monthly 5.44 / 5.02 / 5.81%), but its gains over `damped_yoy_3m` are 0.14 points or less, which is noise.
Undamped, site-by-site and month-ratio models lose. Choosing damping from recent data was unstable.
