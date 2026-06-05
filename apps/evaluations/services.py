import math
import time
from dataclasses import dataclass
from pathlib import Path

import yaml
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.chat.services import SYSTEM_INSTRUCTIONS, build_answer_prompt
from apps.evaluations.models import EvaluationResult, EvaluationRun
from apps.workspaces.models import Workspace
from services.citation_builder.parser import parse_citation_labels
from services.llm_gateway.embeddings import TOKEN_PATTERN
from services.llm_gateway.responses import get_llm_provider
from services.retrieval.vector_search import search_similar_chunks


@dataclass(frozen=True)
class GoldQuestion:
    question: str
    expected_answer: str = ""
    expected_sources: tuple[str, ...] = ()
    should_abstain: bool = False


def load_gold_questions(dataset_path: str | Path) -> list[GoldQuestion]:
    path = Path(dataset_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Gold question dataset must be a YAML list.")

    questions = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Gold question #{index} must be a mapping.")
        question = str(item.get("question", "")).strip()
        if not question:
            raise ValueError(f"Gold question #{index} is missing `question`.")
        questions.append(
            GoldQuestion(
                question=question,
                expected_answer=str(item.get("expected_answer", "")).strip(),
                expected_sources=tuple(str(source).strip() for source in item.get("expected_sources", [])),
                should_abstain=bool(item.get("should_abstain", False)),
            )
        )
    return questions


def run_evaluation(
    *,
    workspace: Workspace,
    user,
    dataset_path: str | Path = "eval/gold_questions.yml",
    name: str = "",
    top_k: int = 8,
) -> EvaluationRun:
    questions = load_gold_questions(dataset_path)
    dataset_name = Path(dataset_path).name
    run = EvaluationRun.objects.create(
        workspace=workspace,
        created_by=user,
        name=name or f"{dataset_name} - {timezone.now():%Y-%m-%d %H:%M}",
        dataset_name=dataset_name,
        model_name=settings.LLM_MODEL if settings.LLM_PROVIDER == "openai" else "local-llm",
        retrieval_top_k=top_k,
    )

    try:
        results = [evaluate_question(run=run, workspace=workspace, gold=gold, top_k=top_k) for gold in questions]
        finalize_run(run, results)
    except Exception as exc:
        run.status = EvaluationRun.Status.FAILED
        run.error_message = str(exc)
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "error_message", "completed_at"])
        raise

    return run


def evaluate_question(
    *,
    run: EvaluationRun,
    workspace: Workspace,
    gold: GoldQuestion,
    top_k: int,
) -> EvaluationResult:
    started = time.perf_counter()
    retrieval_results = search_similar_chunks(
        workspace=workspace,
        query=gold.question,
        top_k=top_k,
        model_name=settings.EMBEDDING_MODEL,
    )
    prompt = build_answer_prompt(question=gold.question, retrieval_results=retrieval_results)
    response = get_llm_provider().generate(instructions=SYSTEM_INSTRUCTIONS, prompt=prompt)
    latency_ms = int((time.perf_counter() - started) * 1000)
    retrieved_sources = [source_reference(result.chunk) for result in retrieval_results]
    cited_sources = cited_source_references(response.content, retrieval_results)
    expected_sources = list(gold.expected_sources)

    metrics = score_answer(
        question=gold.question,
        expected_answer=gold.expected_answer,
        expected_sources=expected_sources,
        retrieved_sources=retrieved_sources,
        cited_sources=cited_sources,
        answer=response.content,
        should_abstain=gold.should_abstain,
    )

    return EvaluationResult.objects.create(
        run=run,
        question=gold.question,
        expected_answer=gold.expected_answer,
        answer=response.content,
        expected_sources=expected_sources,
        retrieved_sources=retrieved_sources,
        cited_sources=cited_sources,
        should_abstain=gold.should_abstain,
        retrieval_recall=metrics["retrieval_recall"],
        citation_precision=metrics["citation_precision"],
        faithfulness=metrics["faithfulness"],
        answer_relevance=metrics["answer_relevance"],
        abstention_correct=bool(metrics["abstention_correct"]),
        latency_ms=latency_ms,
        model_name=response.model_name,
    )


def score_answer(
    *,
    question: str,
    expected_answer: str,
    expected_sources: list[str],
    retrieved_sources: list[str],
    cited_sources: list[str],
    answer: str,
    should_abstain: bool,
) -> dict[str, float | bool]:
    abstained = is_abstention(answer)
    expected_source_count = len(expected_sources)
    retrieval_hits = sum(1 for source in expected_sources if source_matches_any(source, retrieved_sources))
    citation_hits = sum(1 for source in cited_sources if source_matches_any(source, expected_sources))

    retrieval_recall = retrieval_hits / expected_source_count if expected_source_count else 1.0
    citation_precision = citation_hits / len(cited_sources) if cited_sources else (1.0 if should_abstain else 0.0)
    abstention_correct = abstained if should_abstain else not abstained

    if should_abstain:
        faithfulness = 1.0 if abstained else 0.0
        relevance = 1.0 if abstained else 0.0
    else:
        faithfulness = max(citation_precision, retrieval_recall if cited_sources else 0.0)
        relevance = token_overlap(answer, expected_answer or question)

    return {
        "retrieval_recall": clamp(retrieval_recall),
        "citation_precision": clamp(citation_precision),
        "faithfulness": clamp(faithfulness),
        "answer_relevance": clamp(relevance),
        "abstention_correct": abstention_correct,
    }


def finalize_run(run: EvaluationRun, results: list[EvaluationResult]) -> None:
    latencies = [result.latency_ms for result in results]
    run.status = EvaluationRun.Status.COMPLETED
    run.average_retrieval_recall = average(result.retrieval_recall for result in results)
    run.average_citation_precision = average(result.citation_precision for result in results)
    run.average_faithfulness = average(result.faithfulness for result in results)
    run.average_answer_relevance = average(result.answer_relevance for result in results)
    run.abstention_accuracy = average(1.0 if result.abstention_correct else 0.0 for result in results)
    run.average_latency_ms = int(average(latencies))
    run.p50_latency_ms = percentile(latencies, 50)
    run.p95_latency_ms = percentile(latencies, 95)
    run.completed_at = timezone.now()
    with transaction.atomic():
        run.save()


def source_reference(chunk) -> str:
    page = f"#page={chunk.page_number}" if chunk.page_number else ""
    return f"{chunk.document.filename}{page}"


def cited_source_references(answer: str, retrieval_results) -> list[str]:
    result_by_pair = {
        (result.chunk.document_id, result.chunk.id): result
        for result in retrieval_results
    }
    references = []
    for pair in parse_citation_labels(answer):
        result = result_by_pair.get(pair)
        if result:
            references.append(source_reference(result.chunk))
    return references


def source_matches_any(expected: str, candidates: list[str]) -> bool:
    normalized_expected = normalize_source(expected)
    return any(normalized_expected in normalize_source(candidate) for candidate in candidates)


def normalize_source(source: str) -> str:
    return source.lower().replace("\\", "/").strip()


def token_overlap(left: str, right: str) -> float:
    left_tokens = set(TOKEN_PATTERN.findall(left.lower()))
    right_tokens = set(TOKEN_PATTERN.findall(right.lower()))
    if not right_tokens:
        return 1.0
    return len(left_tokens & right_tokens) / len(right_tokens)


def is_abstention(answer: str) -> bool:
    lowered = answer.lower()
    return "i don't know" in lowered or "based on the available documents" in lowered


def average(values) -> float:
    value_list = list(values)
    if not value_list:
        return 0.0
    return sum(value_list) / len(value_list)


def percentile(values: list[int], percent: int) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = math.ceil((percent / 100) * len(sorted_values)) - 1
    return sorted_values[max(0, min(index, len(sorted_values) - 1))]


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
