# Milestone 9: Evaluation Harness

Date: 2026-06-03

## Goal

Add a gold-question evaluation harness for regression testing retrieval, answer generation, citations, abstention behavior, and latency.

## Completed

- Added `pyyaml` dependency for real YAML gold-question datasets.
- Added `EvaluationRun` model for aggregate metrics and run status.
- Added `EvaluationResult` model for per-question metrics, sources, answers, and latency.
- Added admin registrations for evaluation runs and result rows.
- Added `eval/gold_questions.yml` sample dataset.
- Added evaluation service for:
  - YAML loading and validation
  - retrieval execution
  - answer generation through the existing LLM gateway
  - retrieval recall@k
  - citation precision
  - faithfulness heuristic
  - answer relevance heuristic
  - abstention accuracy
  - average, p50, and p95 latency
- Added `run_rag_eval` management command for regression runs from terminal or CI.
- Added `/evaluations/` list/run page and `/evaluations/<id>/` detail report.
- Added navigation link for Evaluations.
- Updated README and `docs/evaluation.md`.
- Added tests for dataset loading, metric scoring, persisted runs/results, command output, and UI pages.

## Verification

- Ran `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`: installed `pyyaml`.
- Ran `.\.venv\Scripts\python.exe manage.py makemigrations evaluations`: created `evaluations.0001_initial`.
- Ran `.\.venv\Scripts\python.exe -m pytest tests\test_evaluations.py`: passed, 5 tests.
- Ran `.\.venv\Scripts\python.exe manage.py migrate`: applied `evaluations.0001_initial`.
- Ran `.\.venv\Scripts\python.exe manage.py check`: passed with no issues.
- Ran `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`: no changes detected.
- Ran `.\.venv\Scripts\python.exe -m pytest`: passed, 48 tests.
- Ran a Django client render smoke check for `/evaluations/` and an evaluation detail page: both returned 200 and included the expected UI text.

## Notes

The metrics are deterministic heuristics so local and CI regression checks do not require paid judge-model calls. Ragas or model-graded evaluations can be added later as an advanced evaluation layer.

Manual evaluation runs use the active `.env` providers. Set `LLM_PROVIDER=local` and `EMBEDDING_PROVIDER=local` for free smoke tests.
