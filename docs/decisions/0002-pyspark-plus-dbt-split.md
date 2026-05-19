---
number: 0002
title: Split processing between PySpark (bronze/silver) and dbt on BigQuery (gold)
status: superseded by 0008
date: 2026-05-16
---

## Context

Given the medallion decision in ADR-0001, *what computes each layer?*
PySpark, dbt, raw Python, and a "single warehouse" SQL-only approach are all
viable. The choice signals taste — and Shopify's published platform splits
exactly this way (Starscream is Spark, Seamster is dbt + BigQuery).

## Decision

Use **PySpark** for bronze and silver: it reads `.csv.gz` and Parquet
natively, parallelizes the 85K-file scan, and writes partitioned Parquet.
Use **dbt Core on BigQuery** for gold: facts, dims, snapshots, tests,
docs, exposures.

The handoff is a `bq load` of the silver Parquet into BigQuery's
`voltaic_raw` dataset.

## Tradeoffs

- Gain: each engine does what it's best at. Spark for file wrangling at
  scale, dbt for declarative SQL with lineage and tests.
- Gain: directly mirrors Shopify's documented Starscream/Seamster split.
- Gain: keeps the warehouse small and cheap — only conformed silver
  enters BigQuery, not raw bytes.
- Give up: two engines = two skill surfaces and two CI environments. For
  a portfolio that's a feature (shows breadth); at small team scale it'd
  be a liability.

## Alternatives considered

- **All-Spark (write everything in PySpark including gold)** — analysts
  can't read it, no built-in test framework like dbt's, no lineage UI.
  Rejected; loses dbt's whole-project benefits.
- **All-dbt (skip Spark, ingest raw to BQ then transform)** — works for
  small/clean inputs but burns query bytes on raw parsing every dev
  iteration. Also forces you to land messy data into BQ, which is
  expensive to clean in SQL. Rejected on cost and ergonomics.
- **Pandas/DuckDB for bronze/silver** — fast at small scale, but the
  "85K files" claim loses force if you didn't actually need a distributed
  engine. Rejected because the dataset *does* justify Spark and the
  portfolio benefits from showing Spark fluency.

## Your notes

*(to fill: how the Schneider OCPP pipeline split work, why "use Spark
where it earns its keep" matters more than "use Spark everywhere",
when you'd switch the whole thing to DuckDB)*
