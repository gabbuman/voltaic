---
number: 0008
title: Use DuckDB for the silver layer; PySpark reserved as a documented scale-up path
status: accepted
date: 2026-05-18
---

## Context

ADR-0002 split processing as PySpark (bronze + silver) and dbt on
BigQuery (gold). ADR-0007 already moved **bronze** to DuckDB after the
PySpark Parquet write hit the `winutils.exe` / `HADOOP_HOME` wall on
Windows, and kept Spark "in reserve for silver."

Reaching silver forces the reserved question. Silver also writes Parquet,
so PySpark silver would hit the identical Windows wall, and the
workarounds (vendor `winutils.exe`, WSL, Docker) all push an
out-of-band prerequisite onto every reviewer for no architectural gain
— the same reasoning that decided ADR-0007. The silver workload
(office_01: ~7.6M rows from 1,474 small files) is single-node
analytical SQL, not a distributed shuffle. DuckDB already reads the
bronze Parquet and writes typed Parquet in-process.

This means the pipeline now uses **no Spark at all**, which overturns
the processing-engine half of ADR-0002. The *gold* half of ADR-0002
(dbt Core on BigQuery) is unaffected and carried forward unchanged.

## Decision

**Use DuckDB for the silver layer.** Silver reads bronze Parquet,
casts every column to its real type (the bronze→silver contract),
builds the composite session key, and writes typed Parquet that
`load_silver_to_bq.py` lands in `voltaic_raw`.

**PySpark stays in `pyproject.toml` as a reserved, documented
scale-up path** — not dead weight. The interview narrative is explicit:
"single-node DuckDB at this volume; here is the file-count / latency /
cluster threshold at which silver moves to Spark, and the code is
structured so that swap is a transform-engine change, not a rewrite."

This ADR **supersedes ADR-0002** (its PySpark-for-processing premise).
ADR-0007 remains accepted; its bronze decision stands and its
"Spark reserved for silver" note is now resolved by this ADR.

## Tradeoffs

- Gain: a genuine end-to-end pipeline runs on a laptop with zero
  Windows-specific setup — bronze, silver, BigQuery load, dbt, Evidence.
- Gain: honest tool fit. Reviewers see "right engine for the data
  size," with a concrete, defensible scale-up threshold — a stronger
  signal than unused Spark scaffolding.
- Gain: one engine for bronze + silver = one skill surface, one CI env
  for the local stages.
- Give up: the live "Spark fluency" demonstration. Mitigated by (a) the
  scale-up writeup with real thresholds, (b) Shopify's posting listing
  *Spark, Presto, dbt, or Flink/Beam* — DuckDB + dbt sits in that
  analytical-engine family, (c) the transform layer is engine-swappable
  by design.

## Alternatives considered

- **PySpark silver + vendor winutils.exe** — most faithful to ADR-0002,
  but reintroduces the exact per-reviewer Windows friction ADR-0007
  rejected, for a workload that doesn't need distribution.
- **PySpark silver → BigQuery direct (Storage Write API)** — avoids
  local Parquet and winutils, keeps the Spark signal. Viable, but adds
  connector-jar + JVM-on-Windows risk and a second engine for one stage,
  on data that doesn't justify it. Recorded as the path to revisit if
  the Spark signal is later judged worth the complexity.
- **All-dbt (land raw in BQ, transform in SQL)** — burns query bytes
  re-parsing raw every dev iteration and lands messy data in the
  warehouse. Rejected on cost/ergonomics, same as in ADR-0002.

## Your notes

*(to fill: the "use the simplest engine that works at your scale"
principle as a through-line from ADR-0007; how the Schneider OCPP
pipeline sized its engine; the exact threshold — file count / row
volume / latency SLA / cluster availability — at which you'd promote
silver to Spark, and why the transform layer was kept engine-agnostic
to make that swap cheap.)*
