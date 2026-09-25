# API Guide

Interactive Swagger documentation is available at `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | Service health |
| POST | `/api/datasets` | Upload and profile dataset |
| GET | `/api/datasets` | List datasets |
| GET | `/api/datasets/{id}` | Dataset profile and anomalies |
| POST | `/api/rule-sets` | Create reusable quality contract |
| GET | `/api/rule-sets` | List contracts |
| POST | `/api/quality-runs` | Execute a contract against a dataset |
| GET | `/api/quality-runs` | Quality history |
| GET | `/api/quality-runs/{id}` | Detailed run results |
| GET | `/api/metrics` | Portfolio/dashboard metrics |
