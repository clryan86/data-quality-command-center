# Data Quality Command Center

[![CI](https://github.com/clryan86/data-quality-command-center/actions/workflows/ci.yml/badge.svg)](https://github.com/clryan86/data-quality-command-center/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-data%20quality-009688)
![Pandas](https://img.shields.io/badge/Pandas-profiling-150458)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)

A production-minded data quality platform for **dataset ingestion, automated profiling, declarative validation, anomaly detection, quality scoring, and auditable run history**.

This project demonstrates the engineering work that sits between raw data ingestion and trustworthy analytics. Instead of assuming an incoming file is usable, the system profiles it, applies reusable quality contracts, records violations, and gives operators a measurable quality score.

## What it demonstrates

- Python data engineering
- Pandas-based profiling and validation
- FastAPI REST design
- SQLite audit persistence
- declarative data-quality contracts
- anomaly detection
- command-line tooling
- automated API/unit tests
- Docker deployment
- GitHub Actions CI
- recruiter-facing architecture and engineering documentation

## Core capabilities

### Dataset profiling
- row and column counts
- inferred dtypes
- null counts and percentages
- unique and duplicate values
- duplicate row counts
- numeric min/max/mean/median/std
- string length statistics
- completeness score

### Quality contracts
Reusable JSON rule sets support:

- `not_null`
- `unique`
- numeric `range`
- `regex`
- `allowed_values`
- `row_count`

Every rule produces a pass/fail result, violation count, diagnostic detail, and sample row indexes.

### Anomaly detection
Numeric columns are scanned for statistical outliers using z-score analysis. The service exposes anomaly findings alongside the persisted dataset profile.

### Audit history
Each quality execution records dataset, rule set, quality score, passed/failed rule counts, violation totals, per-rule details, and timestamp.

## Architecture

```text
CSV / JSON / JSONL
        |
        v
+-------------------+
| FastAPI Ingestion |
+---------+---------+
          |
   +------v-------+
   | Pandas Frame |
   +---+-------+--+
       |       |
       |       +----------------+
       v                        v
+-------------+          +--------------+
| Profiler    |          | Rule Engine  |
| statistics  |          | contracts    |
+------+------+          +------+-------+
       |                        |
       +------------+-----------+
                    v
              +-----------+
              |  SQLite   |
              | audit DB  |
              +-----------+
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

```bash
python -m venv .venv
```

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open the dashboard at `http://127.0.0.1:8000`, OpenAPI at `/docs`, and the health check at `/healthz`.

## CLI

```bash
python -m app.cli profile sample_data/customers.csv
python -m app.cli validate sample_data/customers.csv sample_data/customer_rules.json
```

## Demo dataset

`sample_data/customers.csv` intentionally contains bad email data, duplicate identifiers, an invalid status, a missing field, and an impossible age. `customer_rules.json` defines the contract used to surface those defects.

## Tests

```bash
pytest
ruff check .
```

## Docker

```bash
docker compose up --build
```

## Roadmap

- schema drift detection
- freshness / SLA checks
- referential-integrity rules
- quality trends over time
- Parquet support
- PostgreSQL warehouse metadata
- dbt test import/export
- Great Expectations adapter
- alert destinations
- scheduled source checks

## Author

**Christopher Ryan**  
Python • Data Engineering • Automation • Applied AI

Built as part of a professional software-engineering portfolio focused on reliable, testable systems.

## License

MIT
