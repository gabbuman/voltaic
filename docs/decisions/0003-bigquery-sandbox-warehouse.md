---
number: 0003
title: Use the BigQuery sandbox as the warehouse
status: accepted
date: 2026-05-16
---

## Context

We need a warehouse to land silver tables and host gold marts. The target
employer (Shopify) uses BigQuery as its central warehouse per their
engineering blog. Beyond that signal, we need: (a) free or near-free at
this scale, (b) credible cloud warehouse, (c) no credit card.

## Decision

Use the **BigQuery sandbox**. It provides 10 GB of active storage and 1 TiB
of free queries per month, no credit card. Three datasets are provisioned
in the `solardataset-496600` project (see ADR-0005).

## Tradeoffs

- Gain: $0 cost at our scale; gold marts will be well under 1 GB.
- Gain: same warehouse Shopify uses — reviewers see the exact `dbt-bigquery`
  adapter and BQ-flavored SQL they read all day.
- Give up: **tables auto-expire after 60 days** in the sandbox. Mitigated
  by a weekly GitHub Actions cron that re-runs `dbt build`, keeping
  demo data fresh.
- Give up: no `RESERVATIONS`, no slot-based pricing knobs to demonstrate
  cost-tuning. Acceptable — that conversation belongs in a Staff
  interview, not in a portfolio repo.

## Alternatives considered

- **Snowflake trial** — requires credit card, credits burn quickly during
  dev, no permanent free tier. Rejected on cost.
- **Postgres (Neon free tier or local)** — credible as a database but a
  weak signal for a data engineering portfolio targeting cloud-warehouse
  shops. Rejected on signal.
- **DuckDB** — actually excellent for local dev (and Evidence ships a
  WASM DuckDB to the browser, which we'll exploit). But "I shipped a
  DuckDB-backed portfolio" tells reviewers nothing about cloud warehouse
  fluency. May still use it locally for fast iteration on dbt models.

## Your notes

*(to fill: why the sandbox's 60-day expiry feels like a real-world
constraint to manage rather than a flaw to apologize for, what you'd
choose if cost wasn't a factor, whether you'd test sandbox-vs-paid
performance for the writeup)*
