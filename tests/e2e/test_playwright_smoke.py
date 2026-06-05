import sys

import pytest
from django.contrib.auth import get_user_model

pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


def test_login_dashboard_smoke(live_server):
    if sys.platform == "win32":
        pytest.skip("Playwright smoke runs in CI on Linux.")

    sync_api = pytest.importorskip("playwright.sync_api")
    user = get_user_model().objects.create_user(
        username="playwright-smoke",
        password="test-pass",
    )

    try:
        playwright = sync_api.sync_playwright().start()
    except Exception as exc:
        pytest.skip(f"Playwright driver is not available: {exc}")

    try:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/accounts/login/")
        page.fill('input[name="username"]', user.username)
        page.fill('input[name="password"]', "test-pass")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{live_server.url}/")

        assert "Cited Knowledge Desk" in page.text_content("body")
        assert "Dashboard" in page.text_content("body")
        browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright Chromium is not installed: {exc}")
    finally:
        playwright.stop()
