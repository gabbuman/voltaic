---
number: 0004
title: Use dbt Core (not dbt Cloud)
status: accepted
date: 2026-05-16
---

## Context

dbt comes in two flavors: open-source **dbt Core** (a Python CLI) and
hosted **dbt Cloud** (UI, scheduler, CI integration, costs money).
We need to pick one for this project's gold layer.

## Decision

Use **dbt Core**, invoked from the CLI locally and from GitHub Actions
in CI. Configure the BigQuery adapter via a `profiles.yml` that reads
a service-account JSON path from an environment variable.

## Tradeoffs

- Gain: $0 cost.
- Gain: forces a real understanding of dbt's CI plumbing — running
  `dbt build` against a CI dataset, publishing `dbt docs generate`
  output to `gh-pages`. That plumbing is what an interviewer probes for.
- Gain: matches Shopify's in-house pattern. They run dbt Core
  (under the "Seamster" framework) — they don't pay dbt Labs.
- Give up: no hosted scheduler. We replace it with GitHub Actions cron
  (sufficient at this scale).
- Give up: no hosted Explorer / docs hosting. We publish docs to
  GitHub Pages instead, which is itself a portfolio signal.

## Alternatives considered

- **dbt Cloud free tier** — currently exists but is heavily restricted
  and the "I used the SaaS button" story is weaker than "I wired the CI
  myself". Rejected on signal.
- **SQLMesh** — more modern, virtual data environments are appealing,
  but the ecosystem and the interview vocabulary are still dbt. Picking
  the less-canonical tool would force constant explanation. Rejected on
  audience match.

## Your notes

*(to fill: when dbt Cloud actually earns its keep at a real org, why
the "build the CI yourself" framing is more honest about the work, what
you'd tell a junior engineer evaluating dbt Core vs dbt Cloud for the
first time)*
