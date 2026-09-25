# Interview Guide

## 30-second explanation

> Data Quality Command Center is a FastAPI and Pandas application that ingests CSV/JSON datasets, profiles their structure and completeness, applies reusable data-quality contracts, detects numeric anomalies, and persists quality runs for auditability. I kept the validation engine separate from the API so the same logic can run through HTTP, a CLI, tests, or a future batch scheduler.

## Good technical talking points

### Why not just validate inside an ETL script?

Quality rules become more valuable when they are reusable, inspectable, and measured over time. Persisting checks separately from transformation code makes failures observable and creates an audit trail.

### Why declarative JSON rules?

A data contract should be configuration rather than hard-coded branching. JSON is portable, API-friendly, versionable in Git, and easy to map later to dbt or Great Expectations.

### Why keep raw files separate from SQLite?

The database stores metadata and quality results, while source files remain file objects. This mirrors a common production split between an object store/data lake and a metadata/catalog database.

### What would you improve for enterprise use?

- PostgreSQL metadata store
- S3/Azure Blob source storage
- asynchronous profiling jobs
- schema drift and freshness checks
- lineage metadata
- RBAC and tenant isolation
- alerting
- quality trends and SLOs
- Parquet and warehouse connectors

## Resume bullets

- Built a FastAPI data-quality platform supporting CSV/JSON ingestion, automated profiling, declarative validation contracts, anomaly detection, and persisted audit history.
- Implemented reusable vectorized rules for nullability, uniqueness, numeric ranges, regex formats, allowed values, and dataset-size constraints.
- Added CLI tooling, automated API/unit tests, Docker deployment, GitHub Actions CI, and architecture/interview documentation.
