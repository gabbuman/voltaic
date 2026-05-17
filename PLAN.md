# Building a Shopify-Tier Data Engineering Portfolio Project: An Opinionated 2-Weekend Plan for Shubh Mall

## TL;DR
- **Build "Voltaic" — a prosumer/EV-charging analytics lakehouse** that ingests Caltech ACN-Data (EV sessions; the 2018–2020 static GitHub mirror at `tongxin-li/ACN-Data-Static` lists "85,877 compressed charging-session time-series files in .csv.gz format") plus NREL PVDAQ solar inverter telemetry (parquet on AWS Open Data at `s3://oedi-data-lake/pvdaq/`), processes with PySpark, models with dbt on BigQuery sandbox, and publishes an Evidence.dev static site to GitHub Pages alongside auto-generated dbt docs. Stack signals (dbt + Spark + BigQuery + Trino-class engine) map 1:1 to Shopify's actual Data Platform.
- **Time it as a 2-weekend sprint**: Weekend 1 = ingest + bronze/silver in PySpark + raw load to BigQuery + skeleton dbt project; Weekend 2 = gold dbt models with tests/sources/exposures, Evidence dashboard, GitHub Actions CI, README/architecture diagram, and writeup blog post. Total cost: $0 (BigQuery sandbox, GitHub Pages, public datasets).
- **Lead with this in the application**, not as supplementary. The current Shopify Staff (Lead) Data Engineer (Remote, Canada) posting explicitly asks for "Experience with the internals of a distributed compute engine (Spark, Presto, DBT, or Flink/Beam)" and "Modern Big-Data storage technologies (Iceberg, Hudi, Delta)" — Voltaic is a literal demo of exactly that, in a domain (energy/IoT prosumer) that maps directly to your Schneider Electric work.

## Key Findings

### 1. Shopify's data stack is unusually well-documented — your project must mirror it
Shopify Engineering has published the stack openly. The central warehouse is **BigQuery**; PySpark batch lives in an internal platform called **Starscream**, but a dbt-based SQL workflow called **Seamster** (dbt + BigQuery) was built to absorb the simple-reporting workloads — per the Nov 19, 2020 Shopify Engineering post *"How to Build a Production Grade Workflow with SQL Modelling"* by Michelle Ark and Chris Wu, "We found that 70 percent or so of the PySpark jobs on Starscream were full batch queries that didn't require generalized computing," and Starscream itself "runs 76,000 jobs and writes 300 terabytes a day." Interactive analytics runs on **Trino** clusters; the engineering post *"Shopify's Path to a Faster Trino Query Execution: Custom Verification, Benchmarking, and Profiling Tooling"* states: "On top of handling over 500 Gbps of data, we strive to deliver p95 query results in five seconds or less." Orchestration is **Apache Airflow** — per Shopify Engineering's *"Lessons Learned From Running Apache Airflow at Scale"* (also presented at Airflow Summit 2022): "In our largest environment, we run over 10,000 DAGs… This environment averages over 400 tasks running at a given moment and over 150,000 runs executed per day." Streaming uses **Kafka** and **Apache Beam on Dataflow**. The lake sits on **GCS** with table formats migrating toward Iceberg/Hudi/Delta per the latest job postings.

The current **Shopify Staff (Lead) Data Engineer (Remote, Canada)** posting (shopify.com/careers) asks for experience with "Spark, Presto, DBT, or Flink/Beam," "Google Cloud, Kubernetes, Terraform," and "Modern Big-Data storage technologies (Iceberg, Hudi, Delta)." Notably, BigQuery, Airflow, and Kafka are *not* named in that posting's bullets, but they are heavily referenced in the engineering blog — so demonstrate the *engines* (Spark + dbt + Trino-class query), and the warehouse (BigQuery) follows naturally.

### 2. The "FAANG-tier" portfolio bar in 2026 is platform thinking, not pipelines
The current bar, per hiring-manager-authored guides (Pipeline2Insights' *"The Data Engineer's GitHub Portfolio (2026 Edition)"*, Data Engineering Academy, DataExpert.io): an interview reviewer should grasp the system from a README in 30 seconds, see an **architecture diagram (Mermaid.js is the standard)**, identify production patterns (**idempotent loads, MERGE on business keys, late-arriving updates, dbt tests, CI gates, lineage**), and verify it actually runs (CI status badge, deployed dashboard). Reviewers explicitly look for `/tests`, conventional commit messages, and a Terraform or Docker setup. They will close the tab on Titanic/Kaggle ETLs and on five-model jaffle-shop clones.

Shopify's interview loop is unusually congruent with this. A June 2025 Glassdoor Data Engineer interview review (Toronto) lists explicitly: "Technical project - walkthrough of one of your technical projects. Again very nice interviewers and asked good questions." The DataInterview 2026 Shopify DE guide gives a representative SQL pair-programming prompt: "A daily ELT job builds a BigQuery table fact_orders from raw shopify_orders events, and the orchestrator retries the task after a mid-run failure. How do you make the load idempotent so retries and backfills do not double count orders, including how you handle late-arriving updates like refunds and cancellations?" A project that already ships idempotent MERGEs, SCD2 dimensions, and dbt tests is doing your interview prep for you.

### 3. Energy/IoT public datasets are unusually good — pick two that pair naturally
- **Caltech ACN-Data** (https://ev.caltech.edu/dataset): real EV charging sessions from Caltech, JPL, and an office site; free API token via registration ("To get an access token please register below"). Site reach: "JPL's ACN includes 52 EVSEs in a parking garage." Static 2018–2020 GitHub mirror at `tongxin-li/ACN-Data-Static` reports "85,877 compressed charging-session time-series files in .csv.gz format. Site folders for Caltech, JPL, and office charging locations." Schema is close to OCPP `StartTransaction`/`MeterValues`/`StopTransaction` — directly leverages your Schneider OCPP background.
- **NREL PVDAQ** on AWS Open Data (`s3://oedi-data-lake/pvdaq/`, no-sign-request): solar inverter time-series data. Per the openEDI documentation: "The PVDAQ Dataset is made available in Parquet format on AWS and is partitioned by year, month, day in AWS Glue and Athena," path `s3://oedi-data-lake/pvdata/system_id=/year=/month=/day=/*.parquet`, "Data is typically taken at 15 minute averaged resolution… processed to the NREL PVDAQ data lake on a monthly basis." A system metadata CSV is published at `oedi-data-lake.s3.amazonaws.com/pvdaq/csv/systems_20250729.csv` (refreshed 2025-07-29). This is *the* dataset to use because it's already a Spark-native parquet lake — `spark.read.parquet(...)` exactly like Schneider's medallion bronze stage.
- **CAISO OASIS** (free API; the `pycaiso` Python wrapper and the `gridstatus` library both support it) provides hourly Locational Marginal Prices — perfect for a gold-layer model that joins EV charging cost to grid prices and asks "what would charging at solar-peak vs. evening have saved this fleet?"

Neither ACN-Data nor PVDAQ is mirrored in BigQuery's public datasets, which is actually *good* for the portfolio: you get to write the ingestion code (Python + Spark) rather than `SELECT * FROM bigquery-public-data.foo`.

### 4. Evidence.dev is the right BI layer — Streamlit is not
Evidence.dev is open-source "BI-as-code": you write SQL queries inside Markdown, it pre-runs them at build time, and outputs a static site that deploys to GitHub Pages. Evidence's docs ship a copy-paste GitHub Actions workflow targeting `actions/upload-pages-artifact@v3` + `actions/deploy-pages` and a step-by-step guide at `docs.evidence.dev/deployment/self-host/github-pages`. It connects natively to BigQuery (`docs.evidence.dev/core-concepts/data-sources/bigquery`) and to DuckDB (Evidence "ships a DuckDB engine to the browser using WebAssembly (WASM)"), so you can also query Parquet on S3 directly for a Trino-style federated demo. Streamlit requires a Python server runtime and cannot be hosted on GitHub Pages.

Quarto is a strong alternative if you want long-form writeups (Quarto + Observable JS), but Evidence is more credible as a "BI" surface because it looks like Looker/Mode, not like a notebook. **Use both**: Evidence for the dashboard, dbt-docs for lineage, and a Markdown writeup page for the narrative.

### 5. dbt Core (not Cloud) is the right call
dbt Cloud is unnecessary and costs money. Shopify themselves run dbt Core in-house (their Seamster framework, described in the engineering blog post and Data Engineering Podcast Episode 171, *"How Shopify Is Building Their Production Data Warehouse Using DBT"* with hosts Tobias Macey and guests Zeeshan Qureshi and Michelle Ark). For a portfolio: dbt Core + BigQuery + a GitHub Actions workflow that runs `dbt build` on PR, then `dbt docs generate` on main and publishes to a `gh-pages` branch is *more* impressive than dbt Cloud because it demonstrates you understand the CI plumbing. The `dbt-labs/dbt-project-evaluator` package gives you a free "did I follow best practices" report (it flags missing primary-key tests, direct source joins, ephemeral chains, etc.) you can commit as a CI artifact.

### 6. BigQuery sandbox is enough for this project
Per the Google Cloud BigQuery pricing page (`cloud.google.com/bigquery/pricing`, last updated May 13, 2026), "The first 1 TiB of query data processed per month is free," and the BigQuery sandbox provides 10 GB active storage with no credit card required, subject to a 60-day default table expiration. Your gold-layer aggregates from ACN-Data + PVDAQ will sit well under 1 GB. Use the sandbox for the dbt warehouse; keep the bronze parquet locally or in a free-tier S3.

---

## Details: The Project — "Voltaic"

### Concept (single sentence for your resume)
> *Voltaic is an end-to-end prosumer analytics lakehouse: it ingests real EV charging telemetry (Caltech ACN-Data, 85K+ sessions) and solar inverter performance (NREL PVDAQ Parquet on AWS Open Data), processes it through a bronze→silver→gold medallion in PySpark, models gold facts/dims in dbt on BigQuery with tests and SCD2, and publishes an Evidence.dev dashboard plus dbt docs to GitHub Pages — all under CI with idempotent backfills.*

### Architecture
```
ACN-Data API ──┐
PVDAQ S3 ──────┼──► Python/PySpark (bronze, raw Parquet)
CAISO OASIS ───┘            │
                            ▼
                    PySpark silver
                    (clean, conformed, partitioned by date)
                            │
                            ▼
                    bq load → BigQuery raw_silver dataset
                            │
                            ▼
                    dbt (Core) gold models
                    ├── dim_charging_station (SCD2 via dbt snapshot)
                    ├── dim_pv_system
                    ├── dim_date
                    ├── fct_charging_session (MERGE-idempotent)
                    ├── fct_solar_production_hourly
                    └── mart_prosumer_offset
                            │
            ┌───────────────┼────────────────┐
            ▼               ▼                ▼
      Evidence.dev      dbt docs        dbt-project-evaluator
      (GitHub Pages)    (GitHub Pages)  CI report
```

### What goes on the GitHub Pages site (single repo, single deployment)
The site is the Evidence.dev build output. Use a multi-page structure:
1. **Home** — One-paragraph project summary, the architecture diagram (Mermaid), a "live" Evidence `BigValue` card showing "kWh delivered" and "Solar MWh produced," a status badge from the GitHub Actions CI.
2. **Fleet Performance** — Evidence dashboard with filters by site (Caltech / JPL / Office) and date range; line chart of daily energy delivered; histogram of session duration; cohort table by user.
3. **Solar Yield** — Capacity factor by month, performance ratio vs. expected, heat-map of underperforming systems.
4. **Prosumer Offset** — The killer chart: hourly stacked area of solar production vs. EV demand for a synthetic prosumer site, with a CAISO LMP overlay showing dollars saved by charging at solar-peak.
5. **Engineering writeup** — Long-form post in Markdown: "Why I built this," design decisions (bronze/silver/gold rationale, choice of MERGE over append, why BigQuery + Spark and not one or the other), and tradeoffs. This is the page Shopify interviewers will actually read.
6. **`/docs` (subpath)** — Auto-published dbt docs site (separate Action that runs `dbt docs generate` and pushes to a `docs/` folder).

### Production patterns you *must* include (interview-defensible)
- **Idempotent gold loads**: `fct_charging_session` is a dbt `incremental` model with `unique_key='session_id'`, `incremental_strategy='merge'`, and a bounded `updated_at` lookback window. This is the literal answer to the "make `fact_orders` MERGE idempotent against retries and late-arriving refunds" prompt from the DataInterview Shopify DE guide.
- **SCD2 on `dim_charging_station`**: use dbt snapshots with `strategy='timestamp'` and `updated_at`.
- **Tests**: `not_null`, `unique`, `relationships` on primary keys plus at least one custom singular test (e.g., "no session has `energy_delivered_kwh` > 200 unless `duration_hr` > 4").
- **Sources with freshness checks**: declare ACN-Data and PVDAQ as dbt sources with `freshness:` blocks.
- **Exposures**: declare each Evidence page as a dbt `exposure` so the dbt-docs lineage graph terminates at named dashboards. The `dbt-project-evaluator` package's `fct_exposure_parents_materializations` model will flag any non-table parent — fix those.
- **CI pipeline (`.github/workflows/`)**: (a) lint with sqlfluff, (b) `dbt build` against a CI dataset in BigQuery sandbox, (c) run `dbt-project-evaluator`, (d) build Evidence site and dbt docs, (e) deploy to `gh-pages` via `actions/deploy-pages@v4` or `JamesIves/github-pages-deploy-action@v4`.
- **A `Makefile`** so a reviewer can `make seed && make build && make docs` in 30 seconds.
- **Conventional commits** (`feat:`, `fix:`, `chore:`) — reviewers do open the git log.

### Repo layout (monorepo, single deployment)
```
voltaic/
├── README.md                  ← architecture diagram + 30-second pitch + live links
├── Makefile
├── pyproject.toml             ← uv or poetry
├── ingestion/                 ← Python + PySpark bronze/silver
│   ├── acn_data.py
│   ├── pvdaq_spark.py
│   └── caiso_oasis.py
├── dbt_voltaic/               ← dbt Core project
│   ├── models/staging/
│   ├── models/marts/
│   ├── snapshots/
│   ├── tests/
│   ├── sources.yml
│   ├── exposures.yml
│   └── dbt_project.yml
├── evidence/                  ← Evidence.dev site
│   ├── pages/index.md
│   ├── pages/fleet.md
│   ├── pages/solar.md
│   ├── pages/prosumer.md
│   └── sources/bigquery/
├── .github/workflows/
│   ├── ci.yml                 ← lint + dbt build on PR
│   └── deploy.yml             ← build Evidence + dbt docs → gh-pages
└── docs/                      ← Markdown writeups
```

### Scope: what NOT to build
- No Airflow/Dagster. Cron in GitHub Actions is enough; mention orchestration choice in the README ("would deploy on Airflow at Shopify scale — they run 10,000 DAGs and 150,000 runs/day per their own engineering blog — here, daily GH Actions cron is sufficient").
- No real-time streaming. Mention you considered Kafka + Beam for the OCPP transport layer and explain the batch vs. streaming tradeoff in the writeup.
- No infrastructure-as-code beyond a `terraform/` stub that creates the BigQuery datasets — sized at ~30 lines. This signals fluency without consuming a weekend.
- No ML. A "predict charging demand" notebook is tempting but pushes you into data-science territory; Shopify DE roles want pipelines, not models.

### Weekend-by-weekend timeline (estimated 18–24 hours total)
**Weekend 1 — Pipeline foundation (8–12 hours)**
- Sat AM: Set up repo skeleton, `pyproject.toml`, BigQuery sandbox project, service account, secrets in GitHub.
- Sat PM: Write ACN-Data API client (register and grab the token at `https://ev.caltech.edu/dataset`) + PVDAQ Spark reader for `s3://oedi-data-lake/pvdaq/` (no-sign-request); land raw parquet locally.
- Sun AM: Silver-layer PySpark transformations + `bq load` to BigQuery raw schema.
- Sun PM: `dbt init`, configure BigQuery profile, write first 3 staging models with `not_null`/`unique` tests, get `dbt build` green locally.

**Weekend 2 — Polish + ship (10–12 hours)**
- Sat AM: Gold marts (`fct_charging_session` incremental MERGE, `dim_*`, SCD2 snapshot), custom singular test, sources with freshness, exposures.
- Sat PM: Evidence.dev project, 4 pages with `BigValue` / line / heatmap / area components, configure BigQuery source via service-account JSON in GH secret.
- Sun AM: Two GitHub Actions workflows (CI + deploy), get `gh-pages` deployed, dbt docs publishing to `/docs` subpath.
- Sun PM: Write the README (architecture diagram + 30-second pitch + 3 quantified claims like "processes 85K real EV sessions, P95 dbt build < 4 min in CI"), write the engineering writeup page, polish commit history, push final tag `v1.0.0`.

---

## Recommendations: Application Strategy

### Lead with the project — three placements
1. **Resume**: Replace one bullet under "Personal Projects" (or, better, create a "Selected Project" section above Experience) with:
   > **Voltaic — Prosumer Lakehouse** ([voltaic.shubhmall.dev](#)) — Production-style data platform on Shopify's stack: PySpark bronze/silver over NREL PVDAQ Parquet (S3) + Caltech ACN-Data (85,877 EV sessions); dbt Core gold marts on BigQuery with incremental MERGE, SCD2 snapshots, dbt tests, sources, and exposures; Evidence.dev dashboard and dbt-docs deployed to GitHub Pages via GitHub Actions CI.
2. **Cover letter** (one paragraph after the hook): "While reading Michelle Ark and Chris Wu's *'How to Build a Production Grade Workflow with SQL Modelling'* on shopify.engineering, I built Voltaic — a small mirror of that Seamster workflow in the prosumer-energy domain I know from Schneider Electric (OCPP telemetry, solar inverters). It runs PySpark over a real Parquet lake into BigQuery, models the gold layer in dbt with idempotent merges and SCD2, and ships a static analytics site through GitHub Actions. The dashboard and lineage are live at [URL]."
3. **LinkedIn featured section**: pin the live site URL with the architecture diagram as the image.

### Yes, Shopify reviewers will click through
The Glassdoor June 2025 Toronto Data Engineer review describes the loop including a "Technical project - walkthrough of one of your technical projects" round; the Shopify intern guide tells applicants the recruiter "may be asked to submit a personal project like a GitHub link so that the recruiter can test your skills." Treat the project as the artifact the entire loop will reference.

### Tie the writeup to Shopify values
The Shopify Engineering & Data careers page emphasizes "They ship weekly," "They're open source nerds," and "they work in the open." Your writeup should:
- Brag about ship cadence ("built and shipped in 2 weekends").
- Include an MIT license and a `CONTRIBUTING.md`.
- Have a public commit history with conventional commits — this is the "work in the open" signal.

### Interview-prep payoff (free bonus)
Building Voltaic *is* your SQL pair-programming prep. The Shopify SQL round (per DataInterview 2026) asks idempotent-MERGE-with-late-updates questions on `fact_orders`; you will have just written `fct_charging_session` with exactly that pattern. The dimensional modeling round asks about SCD2; you will have just shipped one. The "what would you do differently" question becomes the closing paragraph of your writeup.

### Staged next steps & decision thresholds
- **Now → Weekend 1**: Build the pipeline. Push a public repo even if it's ugly; iterate in the open.
- **Weekend 2 done → Apply within 7 days**: The repo and live site are your application; don't let perfectionism delay submission. Apply via Shopify careers + a referral if possible.
- **No response in 3 weeks**: Add a streaming extension (synthetic OCPP via the `SAP/e-mobility-charging-stations-simulator` → Beam DirectRunner → BigQuery streaming insert) and a short blog post. This converts a "thanks but no" into a re-application hook at the 6-month reapply window (per the Interview Query 2026 Shopify guide: "Shopify generally encourages candidates to reapply after six months").
- **Got the loop**: Spend interview prep time on (a) defending every design choice in Voltaic, (b) dimensional modeling drills, (c) STAR stories from Schneider that mirror the Voltaic patterns. Don't grind LeetCode — Shopify is famously SQL/data-modeling-heavy, not algo-heavy.

---

## Caveats

- **Shopify's public stack signals are blog-derived, not a hiring SLA.** The Staff DE posting lists "Spark, Presto, DBT, or Flink/Beam" and "Iceberg/Hudi/Delta" but does not name BigQuery or Airflow explicitly. The strongest evidence that BigQuery is the primary warehouse comes from the Shopify Engineering post *"How to Build a Production Grade Workflow with SQL Modelling"* (Michelle Ark & Chris Wu, Nov 19, 2020) and Data Engineering Podcast Episode 171 *"How Shopify Is Building Their Production Data Warehouse Using DBT"* (host Tobias Macey, guests Zeeshan Qureshi and Michelle Ark). Both are several years old; the platform may have evolved. Hedge: don't claim "I know Shopify's exact stack" — claim "I built on the stack Shopify has publicly written about."
- **The 60-day BigQuery sandbox expiration will silently kill your tables** (Google Cloud documentation: "All tables, views, or partitions in partitioned tables automatically expire after 60 days"). Set a calendar reminder, or add a GitHub Actions cron that re-runs `dbt build` weekly so your demo data stays fresh.
- **PVDAQ system count and exact time range are not perfectly documented**; the OEDI metadata CSV (`oedi-data-lake.s3.amazonaws.com/pvdaq/csv/systems_20250729.csv`, refreshed 2025-07-29) is the source of truth, and you should cite the CSV URL in your README rather than a round number. The OEDI submission landing page describes PVDAQ as "a large-scale time-series database containing system metadata and performance data from a variety of experimental PV sites and commercial public PV sites," with at least one 2023 Solar Data Prize subset requiring "at least five years of historical time series data at a minimum of 15-minute time resolution."
- **Caltech ACN-Data requires registration for a token**, and the API has rate limits — Caltech warns "Only use the /ts endpoint when you really need time series data, as it can be slow and bogs down our servers." Cache the raw responses to a local parquet on first pull so CI doesn't re-hammer their server.
- **Evidence.dev is still a young project** — components occasionally have rough edges. Pin the version in `package.json` and don't upgrade mid-sprint.
- **Don't oversell "real-time"**: this is a batch pipeline. Saying "real-time" in the README when the build runs nightly is the fastest way to lose credibility in the interview round.
- **Two-weekend timeline assumes focused work and existing fluency** in Python, PySpark, and SQL (you have all three from Schneider). If you've never touched dbt or Evidence, add 4–6 hours up front to read the dbt Labs *"How we structure our dbt projects"* guide and the Evidence Getting Started.
- **The Shopify "Life Story" behavioral round matters as much as the technical rounds**, per the Exponent and Interview Query 2026 guides and consistent Glassdoor reports. The project gives you technical artifacts; you still need 5–6 STAR stories from Schneider/Xantrex that demonstrate "Be Merchant Obsessed, Thrive on Change, Act Like an Owner" before applying.