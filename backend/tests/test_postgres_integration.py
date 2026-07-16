import os

import pytest


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not configured")
def test_postgres_integration_placeholder():
    """The CI/database job supplies TEST_DATABASE_URL for migration integration tests."""
    assert os.environ["TEST_DATABASE_URL"].startswith("postgres")
