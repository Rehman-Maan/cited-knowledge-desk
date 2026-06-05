# Evaluation

Cited Knowledge Desk includes a deterministic regression harness for checking whether retrieval, answer generation, citations, abstention, and latency stay healthy over time.

## Dataset

Gold questions live in `eval/gold_questions.yml`.

Each item uses this shape:

```yaml
- question: "What is the vacation policy?"
  expected_answer: "Employees receive annual leave."
  expected_sources:
    - "employee-handbook.pdf#page=12"
  should_abstain: false
```

Use `should_abstain: true` for questions that should produce “I don't know based on the available documents.”

## Metrics

- `retrieval_recall`: expected sources retrieved in the top K chunks.
- `citation_precision`: cited sources that match expected sources.
- `faithfulness`: citation-grounding heuristic for supported answers, abstention correctness for unsupported answers.
- `answer_relevance`: token overlap with the expected answer.
- `abstention_accuracy`: whether unsupported questions abstained and supported questions did not.
- `average_latency_ms`, `p50_latency_ms`, `p95_latency_ms`: generation latency.

These are lightweight deterministic metrics for regression testing. They are intentionally local and repeatable; model-graded evals can be added later.

## Run From UI

Open:

- `http://localhost:8000/evaluations/`

Workspace owners/admins can run a dataset and inspect aggregate and per-question results.

## Run From Terminal

```powershell
python manage.py run_rag_eval --workspace your-workspace-slug --user your-username --dataset eval/gold_questions.yml --top-k 8
```

Tests force local providers, but manual runs use your `.env`. Set `LLM_PROVIDER=local` and `EMBEDDING_PROVIDER=local` for free smoke testing.
