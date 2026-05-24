# Hermes Core

Hermes Core is the workflow-first AI orchestration layer for Project Hermes.

It currently includes:

- structured Hermes agent profiles
- runtime prompt compilation
- explicit workflow run state
- durable event log
- policy and permission evaluation
- self-learning memory records
- execution adapter contracts
- MiniMax API adapter
- FastAPI and CLI entrypoints

The architecture docs live in `docs/hermes/`.

## Local Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

## API

```bash
uvicorn hermes_core.app:app --reload
```

Available foundation endpoints:

```text
GET /health
GET /profiles
POST /runs
```

## CLI

```bash
hermes-core init
hermes-core profiles
```

## Documentation

Generate the browsable docs:

```bash
node tools/build-hermes-docs.mjs
```

Open `docs/hermes/index.html`.

