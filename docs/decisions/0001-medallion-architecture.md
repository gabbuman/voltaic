---
number: 0001
title: Adopt medallion architecture (bronze / silver / gold)
status: accepted
date: 2026-05-16
---

## Context

Voltaic ingests messy real-world data from two sources: 85K compressed CSVs
of EV-charging telemetry and ~15-minute solar inverter Parquet on AWS Open
Data. That raw data needs to land somewhere, be cleaned and conformed, then
modeled into business-ready facts and dimensions for dashboards.

We had to pick a layering scheme up front because it shapes storage layout,
re-processing strategy, and where Spark stops and dbt begins.

## Decision

Adopt the standard three-layer medallion: **bronze** for raw landed data
(as-received, schema-on-read), **silver** for cleaned/typed/conformed data
(partitioned by date), and **gold** for business-ready facts and dimensions
(modeled in dbt).

## Tradeoffs

- Gain: each layer isolates a class of failure. If silver logic breaks we
  don't re-hit Caltech; if gold logic breaks we don't re-clean. Each layer
  is independently reprocessable.
- Gain: clean handoff between engines — Spark owns bronze→silver (file
  wrangling), dbt owns silver→gold (SQL modeling).
- Give up: more storage and more orchestration complexity than a two-layer
  scheme. At our scale (portfolio, GB-class) the storage cost is rounding
  error.

## Alternatives considered

- **Two-layer (raw → curated)** — simpler, fewer reruns, but couples
  cleaning and modeling. Rejected because it forces "what does 'curated'
  actually mean?" arguments and loses the replay isolation.
- **Land raw directly in BigQuery and do everything in dbt** — eliminates
  Spark but pushes file-format parsing into SQL, which is painful for
  nested JSON / per-session CSVs and burns BQ query bytes on every dev
  iteration. Rejected as a poor tool-fit at this data shape.
- **Five-layer (bronze / silver / gold / platinum / etc.)** — overkill for
  this scope; the platinum-tier "domain marts" don't earn their keep
  until multi-team consumption.

## Your notes

*(to fill: why medallion specifically resonates with prior Schneider
medallion work, what failure modes pushed you toward the three-layer
isolation, whether you'd revisit with Delta Live Tables / Unity Catalog
patterns at scale)*
