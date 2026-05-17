# Decision Log

This folder holds Architecture Decision Records (ADRs) for Voltaic. Each file
captures one design choice, the alternatives considered, and the tradeoffs accepted.

## Why

Portfolio reviewers and interviewers don't just want to see *what* a system does
— they want to see the reasoning that produced it. ADRs make that reasoning
durable. They also turn directly into the "Engineering writeup" page of the
published Evidence.dev site at the end of the project.

## File convention

```
docs/decisions/NNNN-kebab-case-title.md
```

Numbers are zero-padded, assigned in order, never reused. Once an ADR is
written it is not edited in place — if a decision is overturned, write a new
ADR that **supersedes** the old one, and update the old one's `status` field.

## ADR template

See [`TEMPLATE.md`](./TEMPLATE.md). Every new ADR copies the template, then
fills in the sections. The `## Your notes` block at the bottom is **left empty
in the first draft** and is where Shubh writes personal commentary
(motivation, prior experience, what he'd revisit) for the published writeup.

## Status values

- **proposed** — under discussion, not implemented
- **accepted** — implemented (or being implemented now)
- **superseded by NNNN** — overturned by a later ADR
- **deprecated** — no longer relevant but kept for history

## Index

| #     | Title                                                                            | Status     |
|-------|----------------------------------------------------------------------------------|------------|
| 0001  | [Adopt medallion architecture (bronze / silver / gold)](./0001-medallion-architecture.md) | accepted   |
| 0002  | [Split processing between PySpark and dbt on BigQuery](./0002-pyspark-plus-dbt-split.md)  | accepted   |
| 0003  | [Use BigQuery sandbox as the warehouse](./0003-bigquery-sandbox-warehouse.md)             | accepted   |
| 0004  | [Use dbt Core (not dbt Cloud)](./0004-dbt-core-not-cloud.md)                              | accepted   |
| 0005  | [Three-dataset split in BigQuery (raw / gold / ci)](./0005-three-dataset-split.md)        | accepted   |
| 0006  | [Use the ACN-Data static GitHub mirror instead of the live API](./0006-acn-data-static-mirror.md) | accepted   |
