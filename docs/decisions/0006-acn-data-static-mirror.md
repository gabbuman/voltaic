---
number: 0006
title: Use the ACN-Data static GitHub mirror instead of the live API
status: accepted
date: 2026-05-16
---

## Context

The original plan ingested EV charging data from Caltech's live ACN-Data
API at `ev.caltech.edu/dataset`. The registration flow is currently
broken: the token-retrieval page requires a login that fails for newly
registered accounts. Separately, Caltech's own docs warn that the
`/ts` time-series endpoint "can be slow and bogs down our servers,"
implying rate limits even when the API does work.

A static GitHub mirror exists at
[`tongxin-li/ACN-Data-Static`](https://github.com/tongxin-li/ACN-Data-Static):
85,877 `.csv.gz` files of per-session telemetry plus a
`caltech_sessions.json` of session metadata, covering 2018–2020 across
three sites (Caltech, JPL, Office).

## Decision

Use the **static mirror as the canonical source** for all ACN-Data
ingestion. Clone it once to a sibling folder
`../voltaic-data/acn-data-static/` so the data lives outside this repo.
A `scripts/setup_acn_data.sh` script makes the clone reproducible for any
reviewer.

## Tradeoffs

- Gain: fully reproducible. Same bytes every time; no API drift, no
  token rot, no rate limits.
- Gain: doesn't bog down Caltech's servers — respects their guidance.
- Gain: actually a richer dataset shape (per-session JSON metadata +
  per-session CSV time-series) that maps cleanly to two bronze tables.
- Give up: data is frozen at 2020, so "real-time freshness" is not part
  of the story. We weren't claiming streaming anyway, so this is moot.
- Give up: ~1–3 GB local disk for the clone. Acceptable.

## Alternatives considered

- **Wait for Caltech to fix the API** — unbounded delay, blocks all
  charging-side work. Rejected.
- **Synthetic data from `SAP/e-mobility-charging-stations-simulator`** —
  weakens the "real data, real sessions" headline. Held in reserve as a
  *streaming-extension* layer (see PLAN.md "staged next steps") but not
  the primary source.
- **A different EV dataset entirely (Hugging Face mirrors, NREL
  Secure Transportation, Kaggle)** — uncertain provenance / smaller
  scale / weaker story. Rejected on signal.

## Your notes

*(to fill: how it actually felt to hit a broken third-party signup mid-
project, why "use the frozen-in-time mirror" is a better instinct than
"force the live integration", what you'd do differently if real-time
was actually required by the project)*
