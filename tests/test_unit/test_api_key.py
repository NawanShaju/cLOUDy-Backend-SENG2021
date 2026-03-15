import pytest
from unittest.mock import MagicMock
from app.services.api_key import hash_password, verify_password, get_api_key

def test_hash_password():
    password = "test123"
    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)

def test_verify_password_correct():
    password = "test123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    password = "test123"
    hashed = hash_password(password)

    assert verify_password("wrongpass", hashed) is False

def test_get_api_key_new_user():
    mock_db = MagicMock()

    mock_db.execute_query.return_value = None

    api_key = get_api_key(mock_db, "testuser", "password")

    assert api_key.startswith("ubl_sk_")
    mock_db.execute_insert_update_delete.assert_called_once()

def test_get_api_key_existing_user_correct_password():
    mock_db = MagicMock()

    password = "password"
    hashed = hash_password(password)

    mock_db.execute_query.return_value = ("ubl_sk_existing", hashed)

    api_key = get_api_key(mock_db, "testuser", password)

    assert api_key == "ubl_sk_existing"

def test_get_api_key_existing_user_wrong_password():
    mock_db = MagicMock()

    hashed = hash_password("correct_password")

    mock_db.execute_query.return_value = ("ubl_sk_existing", hashed)

    with pytest.raises(PermissionError):
        get_api_key(mock_db, "testuser", "wrong_password")

def test_get_api_key_missing_username():
    mock_db = MagicMock()

    with pytest.raises(ValueError):
        get_api_key(mock_db, None, "password")

def test_get_api_key_missing_password():
    mock_db = MagicMock()

    with pytest.raises(ValueError):
        get_api_key(mock_db, "user", None)