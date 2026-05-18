---
number: 0007
title: Use DuckDB for bronze ingestion (PySpark held in reserve for silver scale-up)
status: accepted
date: 2026-05-17
---

## Context

Bronze ingestion was originally PySpark per ADR-0002. The first run on
Windows hit two failures: Spark's glob handling treated `**` as a literal
directory name, and Parquet writes failed with
`HADOOP_HOME / winutils.exe is unset` — a known Hadoop-on-Windows wall
requiring an out-of-band binary install.

Beyond the platform issue, the workload at this scale (1,474 small
`.csv.gz` files for office_01; tens-of-thousands total across all sites)
does not justify Spark's distributed-compute overhead. Spark earns its
keep at TB-scale shuffles and cluster-parallel reads; reading a few
thousand small files on a laptop is not that.

## Decision

**Use DuckDB to land bronze.** DuckDB reads `read_csv_auto('...**/*.csv.gz')`
natively (recursive glob, gzip-aware, header inference), writes Parquet
partitioned by column, and runs in-process with no JVM and no Hadoop.

**Keep PySpark in the project (still in `pyproject.toml`) for silver and
downstream joins** where its strengths actually apply — wide
transformations across all sites, prosumer-offset joins between EV and
solar data, and any work that benefits from cluster execution at scale.

## Tradeoffs

- Gain: bronze runs in seconds locally without a Windows-specific
  setup script for reviewers. CI on Linux is faster too.
- Gain: tool fit is honest — Spark for distributed, DuckDB for
  single-node analytical SQL. Reviewers see "right tool for the right
  job," not "Spark everywhere because Spark sounds impressive."
- Gain: a defensible interview talking point on platform sizing —
  "we picked DuckDB at this volume; here's the threshold at which we'd
  swap to Spark."
- Give up: a small amount of the "PySpark portfolio signal." Mitigated
  because (a) silver still uses Spark per ADR-0002, (b) the writeup
  explains the choice, and (c) Shopify's posting lists *Spark, Presto,
  DBT, or Flink/Beam* — DuckDB sits firmly in that family of analytical
  query engines.

## Alternatives considered

- **Install winutils.exe and keep Spark for bronze** — works, but
  requires every Windows reviewer to install a third-party binary or
  for us to vendor one in. Friction per reviewer with no architectural
  upside.
- **Move local dev to WSL** — clean Spark experience, but pushes the
  WSL prerequisite onto every reviewer too. Outside-the-project
  complexity.
- **Spark in Docker** — reproducible, but adds a Docker prerequisite
  and CI complexity for what is genuinely small data.
- **All-DuckDB (also for silver)** — tempting and may be the right call
  later, but keeps optionality open by leaving Spark for silver where
  joins-across-sites could benefit from its query optimizer.

## Your notes

*(to fill: how it felt to walk into the winutils wall, the broader
"use the simplest engine that works at your scale" principle, what
specifically would make you swap bronze back to Spark — file count
threshold, latency requirement, cluster availability)*
