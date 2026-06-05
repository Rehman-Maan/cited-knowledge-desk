"""Celery application for Cited Knowledge Desk."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("cited_knowledge_desk")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.imports = ("workers.document_ingestion",)
app.autodiscover_tasks()
