import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse

from apps.documents.models import Document, DocumentChunk
from apps.evaluations.models import EvaluationResult, EvaluationRun
from apps.evaluations.services import load_gold_questions, run_evaluation, score_answer
from apps.workspaces.models import Workspace
from services.retrieval.vector_search import embed_chunks


def create_eval_chunk(user, workspace, *, filename="sample-quiz.md", page_number=1):
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Sample Quiz",
        file=SimpleUploadedFile(filename, b"# Sample Quiz"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="Zenith means peak or highest point in the quiz explanation.",
        token_count=10,
        page_number=page_number,
    )
    embed_chunks([chunk], model_name="text-embedding-3-small")
    return chunk


@pytest.mark.django_db
def test_load_gold_questions_from_yaml(tmp_path):
    dataset = tmp_path / "gold.yml"
    dataset.write_text(
        """
- question: What does zenith mean?
  expected_answer: Zenith means peak.
  expected_sources:
    - sample-quiz.md#page=1
  should_abstain: false
""",
        encoding="utf-8",
    )

    questions = load_gold_questions(dataset)

    assert len(questions) == 1
    assert questions[0].question == "What does zenith mean?"
    assert questions[0].expected_sources == ("sample-quiz.md#page=1",)


def test_score_answer_computes_core_metrics():
    metrics = score_answer(
        question="What does zenith mean?",
        expected_answer="Zenith means peak.",
        expected_sources=["sample-quiz.md#page=1"],
        retrieved_sources=["sample-quiz.md#page=1"],
        cited_sources=["sample-quiz.md#page=1"],
        answer="Zenith means peak. [D1-C1]",
        should_abstain=False,
    )

    assert metrics["retrieval_recall"] == 1.0
    assert metrics["citation_precision"] == 1.0
    assert metrics["faithfulness"] == 1.0
    assert metrics["answer_relevance"] > 0
    assert metrics["abstention_correct"] is True


@pytest.mark.django_db
def test_run_evaluation_persists_run_and_results(settings, tmp_path):
    settings.EMBEDDING_PROVIDER = "local"
    settings.LLM_PROVIDER = "local"
    user = get_user_model().objects.create_user(username="eval-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    chunk = create_eval_chunk(user, workspace)
    dataset = tmp_path / "gold.yml"
    dataset.write_text(
        f"""
- question: What does zenith mean?
  expected_answer: Zenith means peak or highest point.
  expected_sources:
    - {chunk.document.filename}#page=1
  should_abstain: false
""",
        encoding="utf-8",
    )

    run = run_evaluation(
        workspace=workspace,
        user=user,
        dataset_path=dataset,
        name="Smoke eval",
        top_k=3,
    )

    result = EvaluationResult.objects.get(run=run)
    assert run.status == EvaluationRun.Status.COMPLETED
    assert run.average_retrieval_recall == 1.0
    assert run.retrieval_top_k == 3
    assert result.retrieved_sources == [f"{chunk.document.filename}#page=1"]
    assert result.cited_sources == [f"{chunk.document.filename}#page=1"]


@pytest.mark.django_db
def test_run_rag_eval_command_outputs_summary(settings, tmp_path, capsys):
    settings.EMBEDDING_PROVIDER = "local"
    settings.LLM_PROVIDER = "local"
    user = get_user_model().objects.create_user(username="eval-command", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    chunk = create_eval_chunk(user, workspace)
    dataset = tmp_path / "gold.yml"
    dataset.write_text(
        f"""
- question: What does zenith mean?
  expected_answer: Zenith means peak.
  expected_sources:
    - {chunk.document.filename}#page=1
  should_abstain: false
""",
        encoding="utf-8",
    )

    call_command(
        "run_rag_eval",
        workspace=workspace.slug,
        user=user.username,
        dataset=str(dataset),
        top_k=3,
    )

    captured = capsys.readouterr()
    assert "Evaluation run" in captured.out
    assert "Recall@3" in captured.out


@pytest.mark.django_db
def test_evaluation_pages_render_for_workspace_admin(client):
    user = get_user_model().objects.create_user(username="eval-view", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    run = EvaluationRun.objects.create(
        workspace=workspace,
        created_by=user,
        name="View eval",
        dataset_name="gold.yml",
        status=EvaluationRun.Status.COMPLETED,
    )
    EvaluationResult.objects.create(
        run=run,
        question="What does zenith mean?",
        answer="Zenith means peak.",
        retrieved_sources=["sample-quiz.md#page=1"],
    )
    client.force_login(user)

    list_response = client.get(reverse("evaluations:list"))
    detail_response = client.get(run.get_absolute_url())

    assert list_response.status_code == 200
    assert b"View eval" in list_response.content
    assert detail_response.status_code == 200
    assert b"What does zenith mean?" in detail_response.content
