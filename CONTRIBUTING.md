# Contributing

Install development dependencies with `pip install -r requirements-dev.txt`.

Before a pull request:

```bash
ruff check .
pytest
```

New rule types should include focused unit tests and at least one API or integration-level example when appropriate.
