from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Settings
from .schemas import QualityRunRequest, QualityRunResponse, RuleSetCreate, RuleSetResponse
from .services.io import read_dataset
from .services.profiling import numeric_anomalies, profile_dataframe
from .services.quality import evaluate_rules
from .storage import Store

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    store = Store(settings.database_path)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Data profiling, validation rules, anomaly detection, quality scoring, and audit history.",
    )
    app.state.settings = settings
    app.state.store = store
    app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "service": settings.app_name}

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        datasets = store.list_datasets()
        rule_sets = store.list_rule_sets()
        runs = store.list_runs(12)
        metrics = {
            "datasets": len(datasets),
            "rule_sets": len(rule_sets),
            "runs": len(store.list_runs(1000)),
            "avg_score": round(sum(r["score"] for r in runs) / len(runs), 1) if runs else 0.0,
        }
        return TEMPLATES.TemplateResponse(
            request=request,
            name="index.html",
            context={"app_name": settings.app_name, "datasets": datasets, "rule_sets": rule_sets, "runs": runs, "metrics": metrics},
        )

    @app.get("/datasets/{dataset_id}", response_class=HTMLResponse)
    def dataset_page(dataset_id: int, request: Request):
        dataset = store.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        df = _load_dataframe(dataset)
        return TEMPLATES.TemplateResponse(
            request=request,
            name="dataset.html",
            context={"app_name": settings.app_name, "dataset": dataset, "anomalies": numeric_anomalies(df)},
        )

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    def run_page(run_id: int, request: Request):
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return TEMPLATES.TemplateResponse(
            request=request,
            name="run.html",
            context={"app_name": settings.app_name, "run": run},
        )

    @app.post("/upload")
    async def browser_upload(file: UploadFile = File(...), name: str | None = None):
        payload = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(payload) > settings.max_upload_mb * 1024 * 1024:
            return RedirectResponse(url="/?error=file-too-large", status_code=303)
        try:
            dataset_id = _ingest(store, settings, file.filename or "dataset.csv", payload, name)
        except ValueError:
            return RedirectResponse(url="/?error=unsupported", status_code=303)
        return RedirectResponse(url=f"/datasets/{dataset_id}", status_code=303)

    @app.post("/api/datasets", status_code=201)
    async def api_upload(file: UploadFile = File(...), name: str | None = None):
        payload = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(payload) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File exceeds upload limit")
        try:
            dataset_id = _ingest(store, settings, file.filename or "dataset.csv", payload, name)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return store.get_dataset(dataset_id)

    @app.get("/api/datasets")
    def api_datasets():
        return store.list_datasets()

    @app.get("/api/datasets/{dataset_id}")
    def api_dataset(dataset_id: int):
        dataset = store.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        df = _load_dataframe(dataset)
        return {**dataset, "anomalies": numeric_anomalies(df)}

    @app.post("/api/rule-sets", response_model=RuleSetResponse, status_code=201)
    def create_rule_set(payload: RuleSetCreate):
        try:
            rule_set_id = store.create_rule_set(payload.name, payload.rules)
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Rule-set name already exists") from exc
        return store.get_rule_set(rule_set_id)

    @app.get("/api/rule-sets", response_model=list[RuleSetResponse])
    def list_rule_sets():
        return store.list_rule_sets()

    @app.post("/api/quality-runs", response_model=QualityRunResponse, status_code=201)
    def create_quality_run(payload: QualityRunRequest):
        dataset = store.get_dataset(payload.dataset_id)
        rule_set = store.get_rule_set(payload.rule_set_id)
        if not dataset or not rule_set:
            raise HTTPException(status_code=404, detail="Dataset or rule set not found")
        result = evaluate_rules(_load_dataframe(dataset), rule_set["rules"])
        run_id = store.create_run(dataset["id"], rule_set["id"], result)
        return store.get_run(run_id)

    @app.get("/api/quality-runs", response_model=list[QualityRunResponse])
    def list_quality_runs(limit: int = 50):
        return store.list_runs(max(1, min(limit, 200)))

    @app.get("/api/quality-runs/{run_id}", response_model=QualityRunResponse)
    def get_quality_run(run_id: int):
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Quality run not found")
        return run

    @app.get("/api/metrics")
    def metrics():
        datasets = store.list_datasets()
        runs = store.list_runs(1000)
        return {
            "datasets": len(datasets),
            "rule_sets": len(store.list_rule_sets()),
            "quality_runs": len(runs),
            "average_quality_score": round(sum(r["score"] for r in runs) / len(runs), 2) if runs else 0.0,
            "total_violations": sum(r["total_violations"] for r in runs),
        }

    return app


def _ingest(store: Store, settings: Settings, filename: str, payload: bytes, name: str | None) -> int:
    df = read_dataset(filename, payload)
    if len(df.columns) == 0:
        raise ValueError("Dataset contains no columns")
    digest = hashlib.sha256(payload).hexdigest()[:16]
    safe_name = Path(filename).name
    stored = settings.upload_dir / f"{digest}_{safe_name}"
    stored.write_bytes(payload)
    profile = profile_dataframe(df)
    return store.create_dataset(name or Path(safe_name).stem.replace("_", " ").title(), safe_name, str(stored), profile)


def _load_dataframe(dataset: dict):
    payload = Path(dataset["file_path"]).read_bytes()
    return read_dataset(dataset["filename"], payload)


app = create_app()
