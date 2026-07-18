# Security Dashboard — 2026-07-18

## Plan

- [x] EntryView mtime/atime/ctime; password_strength extract; PEM SSH algo + cert not_after
- [x] security_dashboard package: models, analyzer, scoring, recommendations + unit tests
- [x] Reusable ui/charts: KPI, Gauge, Donut, Bar/Histogram, HeatMap, badges
- [x] ViewModel + panel registry + all panels + dialog; theme QSS
- [x] MainWindow/palette rename; ui-spec; catalog_tr; README; smoke + suite

## Review

Security Dashboard replaces Password Health as Tools → Security Dashboard… (alias `open_password_health` kept).

- Analyzer builds `DashboardSnapshot` (score, buckets, risk, recommendations) on top of `AuditEngine`
- Custom QPainter charts in `ui/charts/`; modular panels via `panel_registry`
- EntryView gains `modified` / `accessed` / `created`; PEM inspector adds SSH algo + cert dates
- Verification: 143 tests passed; ruff clean on new packages
