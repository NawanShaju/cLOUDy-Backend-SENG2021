import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_ownership_check():
    with patch("app.services.api_key.check_buyer_ownership", lambda f: f):
        yield