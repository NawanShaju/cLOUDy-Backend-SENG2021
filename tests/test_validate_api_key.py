from flask import Flask
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.api_key import validate_api_key


def test_validate_api_key_success():
    app = Flask(__name__)

    @validate_api_key
    def protected():
        return "success"

    with app.test_request_context(headers={"api-key": "valid_key"}):
        with patch("app.services.apiKey.PostgresDB") as mock_db:

            mock_instance = MagicMock()
            mock_instance.execute_query.return_value = True
            mock_db.return_value.__enter__.return_value = mock_instance

            response = protected()

            assert response == "success"


def test_validate_api_key_unauthorized():
    app = Flask(__name__)

    @validate_api_key
    def protected():
        return "success"

    with app.test_request_context(headers={"api-key": "invalid"}):
        with patch("app.services.apiKey.PostgresDB") as mock_db:

            mock_instance = MagicMock()
            mock_instance.execute_query.return_value = None
            mock_db.return_value.__enter__.return_value = mock_instance

            response, status = protected()

            assert status == 401