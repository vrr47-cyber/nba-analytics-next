import asyncio

import pytest

from backend.app.core.errors import ApplicationError
from backend.app.providers.unconfigured import UnconfiguredProvider


def test_unconfigured_provider_makes_no_network_request():
    with pytest.raises(ApplicationError, match="no network call was attempted"):
        asyncio.run(UnconfiguredProvider().list_teams())
