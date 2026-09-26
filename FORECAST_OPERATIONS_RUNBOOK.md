# Forecast Operations / Resolution Watch

The four admitted production Forecast issuances are monitored by a derived,
read-only operational watch. It does not change Forecast values, cutoffs,
targets, resolution rules or sources, and it does not create Forecasts,
Outcomes or scores.

Run a reproducible watch with:

```bash
python scripts/forecast_operations.py --as-of 2026-09-27T00:00:00Z
```

Use `--json` for the machine-readable manifest. Without `--as-of`, the command
uses the current UTC time. The seven-day review lead time is explicit in
`data/forecasts/operations_policy.json`.

Operational states are derived from the Forecast resolution window and any
governed Outcome already present:

- `OPEN_NOT_DUE`: before the seven-day review window;
- `OPEN_REVIEW_WINDOW`: within seven days of the resolution window;
- `RESOLUTION_DUE`: the resolution window has opened and evidence is not yet marked available;
- `AWAITING_RESOLUTION`: authoritative evidence is available for human Outcome review;
- `OVERDUE_REVIEW`: the resolution window has closed without a terminal Outcome;
- `RESOLVED`, `VOID`, `UNRESOLVABLE` or `DISPUTED`: derived from a governed Outcome.

New analytical estimates are not scheduled automatically. If material new
evidence justifies an update, retain the existing issuance, freeze a new
cutoff and admit a distinct prospective issuance through the Forecast
admission gate. When a resolution window opens, capture the pre-declared
authoritative evidence, compare it with the original rule, propose an Outcome,
obtain human review and only then admit the governed Outcome transaction.

No public Forecast or Evaluation projection is created. Model Learning remains
deferred until resolved evidence exists.
