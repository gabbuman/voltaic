---
number: 0009
title: Deploy Evidence to GitHub Pages via the Actions artifact API
status: accepted
date: 2026-05-18
---

## Context

The Evidence site is the public face of the portfolio. Its build is not
static-in-repo: `evidence build` queries the BigQuery gold marts at
build time, the output (`evidence/build/`) is gitignored and
regenerated, and the project page is served from a subpath
(`gabbuman.github.io/voltaic/`). So "point Pages at a folder" is not an
option — a build must run in CI, and that build needs the GCP service
account key, which must never enter git (ADR-0003 / .gitignore).

## Decision

**Deploy via a GitHub Actions workflow that builds Evidence and
publishes through the Pages artifact API** (`upload-pages-artifact` +
`deploy-pages`), with Pages "Source" set to **GitHub Actions**.

- The SA key lives in the `GCP_SA_KEY` repo secret. A workflow step
  reconstructs the gitignored `connection.options.yaml` from it, using
  the same base64 encoding Evidence expects. The key is never written
  to a tracked file and never leaves the runner.
- `deployment.basePath: /voltaic` is committed in `evidence.config.yaml`
  (not a CI-only env var) so local preview reproduces the production
  subpath and base-path bugs surface before deploy.
- Workflow runs on pushes that touch `evidence/**` (plus manual
  dispatch).

## Tradeoffs

- Gain: no machine-generated build artifacts in git history; nothing to
  force-push; the repo stays source-only.
- Gain: the secret path is auditable and minimal — one secret, decoded
  on the runner, used only for the build query.
- Gain: short OIDC-token deploy (`id-token: write`), no long-lived
  Pages deploy key.
- Give up: deploys require Actions minutes and a green build; a BigQuery
  outage or (more likely) the sandbox 60-day table expiry will fail the
  deploy until the gold marts are rebuilt. That coupling is the
  motivation for the upcoming scheduled CI rebuild.

## Alternatives considered

- **`gh-pages` branch (Deploy from a branch)** — literally matches
  "deploy from a branch," but a branch full of generated output that is
  force-pushed every deploy adds noise and a failure mode (branch/secret
  drift) for no upside over the artifact API.
- **Commit `evidence/build/` to `/docs` on main** — removes the build
  from CI but bloats history with generated files and still can't
  produce them without the SA key locally. Rejected.
- **CI-only base path via env var** — keeps local preview at root, but
  local then no longer mirrors production and base-path breakage is
  only caught in CI. Rejected for a worse feedback loop.

## Your notes

*(to fill: the "generated artifacts never belong in git" principle;
how secrets were handled in the Schneider CI; why mirroring the prod
base path locally is worth the minor `/voltaic` prefix annoyance; the
plan for decoupling deploy from the sandbox table expiry.)*
