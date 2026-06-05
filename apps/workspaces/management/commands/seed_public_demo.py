import os

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.chat.models import ChatMessage, ChatSession, Citation
from apps.documents.models import Document, DocumentChunk
from apps.evaluations.models import EvaluationResult, EvaluationRun
from apps.feedback.models import AnswerFeedback
from apps.workspaces.models import Workspace, WorkspaceMembership
from services.llm_gateway.embeddings import embed_texts


class Command(BaseCommand):
    help = "Seed a clean public demo workspace for hosted portfolio previews."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.environ.get("DEMO_USERNAME", "demo_public"))
        parser.add_argument("--password", default=os.environ.get("DEMO_USER_PASSWORD", "DemoPublicPass123!"))
        parser.add_argument("--email", default=os.environ.get("DEMO_USER_EMAIL", "demo@example.com"))

    def handle(self, *args, **options):
        user = self._upsert_user(
            username=options["username"],
            password=options["password"],
            email=options["email"],
        )
        workspace = self._upsert_workspace(user)
        self._clear_workspace(workspace)

        operations_doc, operations_chunk = self._create_document_with_chunk(
            workspace=workspace,
            user=user,
            title="Operations Handbook",
            filename="operations-handbook.md",
            page_number=2,
            content=(
                "Refund requests must be reviewed within two business days. Enterprise contracts require "
                "finance approval before renewal. Support escalations should include account ID, issue "
                "summary, and customer impact."
            ),
        )
        security_doc, security_chunk = self._create_document_with_chunk(
            workspace=workspace,
            user=user,
            title="Security Policy",
            filename="security-policy.md",
            page_number=4,
            content=(
                "Production secrets must live in environment variables and should never be committed to "
                "source control. Access reviews happen quarterly and privileged changes require an audit note."
            ),
        )

        session, assistant_message = self._create_chat(
            workspace=workspace,
            user=user,
            document=operations_doc,
            chunk=operations_chunk,
        )
        self._create_feedback(user=user, assistant_message=assistant_message)
        run = self._create_evaluation(
            workspace=workspace,
            user=user,
            security_doc=security_doc,
            security_chunk=security_chunk,
            operations_doc=operations_doc,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded public demo: "
                f"username={user.username} workspace={workspace.slug} "
                f"chat_id={session.pk} evaluation_id={run.pk}"
            )
        )

    def _upsert_user(self, *, username, password, email):
        User = get_user_model()
        user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
        user.email = email
        user.first_name = "Rao Abdul"
        user.last_name = "Rehman"
        user.set_password(password)
        user.save()
        return user

    def _upsert_workspace(self, user):
        workspace, _ = Workspace.objects.update_or_create(
            slug="demo-knowledge-workspace",
            defaults={
                "name": "Rao Abdul Rehman's Workspace",
                "created_by": user,
            },
        )
        WorkspaceMembership.objects.update_or_create(
            workspace=workspace,
            user=user,
            defaults={"role": WorkspaceMembership.Role.OWNER},
        )
        return workspace

    def _clear_workspace(self, workspace):
        Document.objects.filter(workspace=workspace).delete()
        ChatSession.objects.filter(workspace=workspace).delete()
        EvaluationRun.objects.filter(workspace=workspace).delete()

    def _create_document_with_chunk(self, *, workspace, user, title, filename, page_number, content):
        document = Document.objects.create(
            workspace=workspace,
            title=title,
            file_type="md",
            status=Document.Status.READY,
            uploaded_by=user,
        )
        document.file.save(filename, ContentFile(f"# {title}\n\n{content}\n"), save=True)
        chunk = DocumentChunk.objects.create(
            workspace=workspace,
            document=document,
            chunk_index=1,
            content=content,
            token_count=max(1, len(content.split())),
            page_number=page_number,
            section_title=title,
            embedding_model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
        )
        chunk.embedding = embed_texts([content])[0]
        chunk.save(update_fields=["embedding", "embedding_model"])
        return document, chunk

    def _create_chat(self, *, workspace, user, document, chunk):
        session = ChatSession.objects.create(
            workspace=workspace,
            user=user,
            title="How are refunds handled?",
        )
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content="How quickly should refund requests be reviewed?",
        )
        assistant_message = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=f"Refund requests should be reviewed within two business days. [D{document.pk}-C{chunk.pk}]",
            model_name="local-demo",
            latency_ms=980,
        )
        Citation.objects.create(
            assistant_message=assistant_message,
            document=document,
            chunk=chunk,
            quote="Refund requests must be reviewed within two business days.",
            page_number=chunk.page_number,
            score=0.92,
        )
        return session, assistant_message

    def _create_feedback(self, *, user, assistant_message):
        AnswerFeedback.objects.update_or_create(
            message=assistant_message,
            user=user,
            defaults={
                "rating": AnswerFeedback.Rating.DOWN,
                "failure_tag": AnswerFeedback.FailureTag.WEAK_CITATION,
                "comment": "Citation is helpful, but this answer should be checked during review before publishing.",
                "reviewed": False,
            },
        )

    def _create_evaluation(self, *, workspace, user, security_doc, security_chunk, operations_doc):
        run = EvaluationRun.objects.create(
            workspace=workspace,
            created_by=user,
            name="Public Demo Evaluation",
            dataset_name="demo_gold_questions.yml",
            model_name="local-demo",
            retrieval_top_k=5,
            status=EvaluationRun.Status.COMPLETED,
            average_retrieval_recall=1.0,
            average_citation_precision=0.95,
            average_faithfulness=0.9,
            average_answer_relevance=0.92,
            abstention_accuracy=1.0,
            average_latency_ms=1140,
            p50_latency_ms=980,
            p95_latency_ms=1460,
            completed_at=timezone.now(),
        )
        EvaluationResult.objects.create(
            run=run,
            question="Where should production secrets live?",
            expected_answer="Production secrets must live in environment variables.",
            answer=(
                "Production secrets must live in environment variables and should not be committed. "
                f"[D{security_doc.pk}-C{security_chunk.pk}]"
            ),
            expected_sources=[f"{security_doc.filename}#page=4"],
            retrieved_sources=[f"{security_doc.filename}#page=4", f"{operations_doc.filename}#page=2"],
            cited_sources=[f"{security_doc.filename}#page=4"],
            retrieval_recall=1.0,
            citation_precision=1.0,
            faithfulness=1.0,
            answer_relevance=0.95,
            abstention_correct=True,
            latency_ms=980,
            model_name="local-demo",
        )
        EvaluationResult.objects.create(
            run=run,
            question="What is the vendor cafeteria menu?",
            expected_answer="The source set does not contain that answer.",
            answer="I do not have enough cited source material to answer that.",
            expected_sources=[],
            retrieved_sources=[f"{operations_doc.filename}#page=2"],
            cited_sources=[],
            should_abstain=True,
            retrieval_recall=1.0,
            citation_precision=1.0,
            faithfulness=1.0,
            answer_relevance=0.9,
            abstention_correct=True,
            latency_ms=1460,
            model_name="local-demo",
        )
        return run
