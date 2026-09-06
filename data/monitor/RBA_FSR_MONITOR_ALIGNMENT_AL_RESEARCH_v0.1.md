# WORLD SIGNALS — RBA FSR monitor alignment AL research v0.1

**Reference date:** 2026-09-06

**Exact base main:** `72103267f90475b04c80129e03b41b605d4b7f58`

**Architecture position:** Source/Change Monitor only. No canonical, Calendar, Live Intelligence or Analysis mutation.

## Pressure-audit finding

The post-AK read-only pressure audit reran the live monitor against canonical registry v0.37 / 687 and source registry v1.78 / 242. All seven expected adapter entries were observed, all were healthy, canonical state remained byte-identical and no review candidate was generated.

One observation is nevertheless structurally wrong: `RBA_FSR_RSS` reports the official item `Financial Stability Review - March 2026`, published `2026-03-19T11:30:00+11:00`, as `RBA_PUBLICATION_UNMATCHED`.

This is not a source failure and not a canonical defect.

## Root cause

The canonical series `WSER-FIN-AU-RBA-FSR` now contains two 2026 occurrences:

- `WSO-FIN-B-0001` — October 2026 FSR — `PLANNED` — 1 October 2026, 11:30 Australia/Sydney;
- `WSO-FIN-B-0004` — March 2026 FSR — `COMPLETED` — 19 March 2026, 11:30 Australia/Sydney.

Historical-anchor tranche AC admitted the March occurrence into the existing RBA FSR series and existing source contract. The live-monitor expectations, however, still scope `RBA_FSR_RSS` only to `WSO-FIN-B-0001`.

`rba_fsr_review_candidates` intentionally matches only records named by `canonical_occurrence_ids`. The March publication is therefore compared only with the October occurrence. The 196-day separation exceeds the reviewed 75-day matching window, so the item becomes `RBA_PUBLICATION_UNMATCHED` even though the exact completed canonical occurrence exists.

## Current authoritative RBA evidence

The RBA publishing calendar records the March 2026 Financial Stability Review at 19 March 2026, 11:30 am AEDT. The RBA News & Announcements archive records both the Review and its release at the same time. The RBA FSR landing page states that the FSR is published twice a year and identifies 19 March 2026 as the last publication and 1 October 2026 as the next publication. The March FSR page and media release are current first-party evidence that the review was published.

The fresh live RSS adapter observed the same official March item at `2026-03-19T11:30:00+11:00` with source health `HEALTHY`.

## Selected repair

AL will keep explicit reviewed occurrence scoping. It will not dynamically widen an adapter to every record in a series, because explicit IDs are part of monitor governance and other adapters may intentionally track only selected occurrences.

The narrow repair is:

1. bump `data/monitor/expectations.json` from v0.8 to v0.9;
2. add `WSO-FIN-B-0004` to `RBA_FSR_RSS.canonical_occurrence_ids`, preserving `WSO-FIN-B-0001`;
3. add a regression contract proving the current March official item resolves to `RBA_PUBLICATION_ALREADY_REFLECTED`, with no review candidate;
4. prove the October forward occurrence remains independently matchable;
5. rerun the real read-only live monitor after the write and require no RBA unmatched observation, no RBA review candidate, healthy source state and byte-identical canonical state.

No matching window, source identity, lifecycle rule or canonical record changes.

## Why this outranks another Analysis specimen

The six completed-unreviewed Analysis anchors remain available, including the March RBA FSR. But a monitor that emits false unmatched observations about an already-canonical official publication weakens the Source/Change Monitor layer itself. Repairing that boundary has greater marginal architectural value than adding another reviewed Analysis row, and combining the two would blur layers.

The RBA FSR remains a strong subsequent Analysis candidate once monitor alignment is restored.

## Guardrails

- Official publication evidence does not directly mutate canonical state.
- Absence from an RSS feed never implies cancellation or non-completion.
- Historical admission of an occurrence does not automatically authorize dynamic monitor scope expansion.
- Explicit monitor scope remains reviewed configuration.
- The March completed occurrence is not changed merely to silence the monitor.
- The October planned occurrence remains planned.
- No Google Calendar write.
- No Analysis population in AL.
- No auto-merge.
