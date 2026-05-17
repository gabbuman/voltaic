---
number: 0005
title: Three-dataset split in BigQuery (raw / gold / ci)
status: accepted
date: 2026-05-16
---

## Context

A dataset in BigQuery is both a namespace and the unit of access control.
Once we settled on BQ as the warehouse (ADR-0003), we had to decide how
to partition tables across datasets. The two questions: how many
datasets, and along what dimension?

## Decision

Three datasets in the `solardataset-496600` project:

- `voltaic_raw` — silver Parquet landed via `bq load`. The warehouse
  boundary; nothing transforms further upstream of this.
- `voltaic_gold` — dbt outputs (facts, dims, snapshots, marts).
- `voltaic_ci` — scratch space for CI runs; PR builds land here so they
  never touch real demo data.

All three at `US` multi-region with a 60-day default table expiration to
make the sandbox constraint explicit rather than implicit.

## Tradeoffs

- Gain: clean access-control story (analysts get `voltaic_gold` read,
  not `voltaic_raw`). Even on a solo project it signals the right
  mental model.
- Gain: PR builds are bulletproof — a broken model in a PR can't
  corrupt the live dashboard, because the CI runs against `voltaic_ci`.
- Gain: maps to Shopify's documented `seamster_*` vs `production_*`
  dataset split.
- Give up: a tiny amount of operational overhead (three datasets to
  watch instead of one). Negligible.

## Alternatives considered

- **Single dataset** — simplest, but couples access control and entangles
  CI with prod. Rejected on principle even though scale doesn't yet
  force the split.
- **One dataset per dbt schema convention (`staging_*`, `marts_*`)** —
  dbt-canonical, but doesn't address the CI-isolation concern.
- **Layer × environment matrix (6 datasets: `raw_prod`, `raw_ci`,
  `gold_prod`, `gold_ci`, etc.)** — what we'd do at scale, overkill
  here. May revisit if a streaming layer or staging environment is added.

## Your notes

*(to fill: how Schneider handled the analyst-vs-engineer dataset boundary,
why CI isolation is "free" insurance even on a solo project, what would
make you add a fourth dataset)*
