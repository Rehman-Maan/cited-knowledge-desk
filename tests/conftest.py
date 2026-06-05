import pytest


@pytest.fixture(autouse=True)
def disable_auto_ingestion(settings):
    settings.DOCUMENT_INGESTION_AUTO_QUEUE = False
    settings.EMBEDDING_PROVIDER = "local"
    settings.LLM_PROVIDER = "local"
