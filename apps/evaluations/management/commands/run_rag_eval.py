from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.evaluations.services import run_evaluation
from apps.workspaces.models import Workspace


class Command(BaseCommand):
    help = "Run the RAG evaluation harness against a gold question dataset."

    def add_arguments(self, parser):
        parser.add_argument("--workspace", required=True, help="Workspace slug or id.")
        parser.add_argument("--user", required=True, help="Username of the run owner.")
        parser.add_argument("--dataset", default="eval/gold_questions.yml")
        parser.add_argument("--name", default="")
        parser.add_argument("--top-k", type=int, default=8)

    def handle(self, *args, **options):
        workspace = self._get_workspace(options["workspace"])
        user = self._get_user(options["user"])
        run = run_evaluation(
            workspace=workspace,
            user=user,
            dataset_path=options["dataset"],
            name=options["name"],
            top_k=options["top_k"],
        )
        self.stdout.write(self.style.SUCCESS(f"Evaluation run {run.id} completed: {run.name}"))
        self.stdout.write(f"Recall@{run.retrieval_top_k}: {run.average_retrieval_recall:.3f}")
        self.stdout.write(f"Citation precision: {run.average_citation_precision:.3f}")
        self.stdout.write(f"Faithfulness: {run.average_faithfulness:.3f}")
        self.stdout.write(f"Answer relevance: {run.average_answer_relevance:.3f}")
        self.stdout.write(f"p95 latency: {run.p95_latency_ms}ms")

    def _get_workspace(self, value):
        queryset = Workspace.objects.all()
        if value.isdigit():
            workspace = queryset.filter(id=int(value)).first()
        else:
            workspace = queryset.filter(slug=value).first()
        if workspace is None:
            raise CommandError(f"Workspace not found: {value}")
        return workspace

    def _get_user(self, username):
        user = get_user_model().objects.filter(username=username).first()
        if user is None:
            raise CommandError(f"User not found: {username}")
        return user
