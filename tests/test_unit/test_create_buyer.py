import pytest
from unittest.mock import MagicMock, call
from app.services.buyer_service import create_buyer_service
from app.services.db_services.buyer_db import (
    find_buyer_by_account_id,
    insert_buyer_tax_scheme,
    insert_buyer,
    get_buyer_by_id,
)

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def valid_buyer_data():
    return {
        "party_name": "IYT Corporation",
        "customer_assigned_account_id": "XFB01",
        "supplier_assigned_account_id": "GT00978567",
        "address": {
            "street": "10 Pitt St", "city": "Sydney",
            "state": "NSW", "postal_code": "2000", "country_code": "AU"
        },
        "contact": {
            "name": "Fred Churchill", "telephone": "0127 2653214",
            "telefax": "0127 2653215", "email": "fred@iyt.com"
        },
        "tax_scheme": {
            "registration_name": "IYT Tax", "company_id": "123",
            "exemption_reason": "Local Authority",
            "scheme_id": "VAT", "tax_type_code": "VAT"
        }
    }


def test_create_buyer_missing_party_name_returns_400(mock_db):
    result = create_buyer_service(mock_db, {"customer_assigned_account_id": "X01"})
    assert isinstance(result, tuple)
    assert result[1] == 400
    assert result[0]["error"] == "party_name is required"


def test_create_buyer_missing_account_id_returns_400(mock_db):
    result = create_buyer_service(mock_db, {"party_name": "Corp"})
    assert isinstance(result, tuple)
    assert result[1] == 400
    assert result[0]["error"] == "customer_assigned_account_id is required"


def test_create_buyer_duplicate_account_id_returns_409(monkeypatch, mock_db, valid_buyer_data):
    monkeypatch.setattr(
        "app.services.buyer_service.find_buyer_by_account_id",
        lambda db, acc_id: [("existing-buyer-id",)]
    )
    result = create_buyer_service(mock_db, valid_buyer_data)
    assert isinstance(result, tuple)
    assert result[1] == 409
    assert "already exists" in result[0]["error"]


def test_create_buyer_success_returns_buyer_id(monkeypatch, mock_db, valid_buyer_data):
    monkeypatch.setattr("app.services.buyer_service.find_buyer_by_account_id", lambda db, a: None)
    monkeypatch.setattr("app.services.buyer_service.insert_address", lambda db, a: [("addr-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer_tax_scheme", lambda db, t: [("tax-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer", lambda db, d, a, t: [("new-buyer-id",)])

    result = create_buyer_service(mock_db, valid_buyer_data)
    assert isinstance(result, dict)
    assert result["buyer_id"] == "new-buyer-id"


def test_create_buyer_without_address_skips_insert(monkeypatch, mock_db, valid_buyer_data):
    valid_buyer_data.pop("address")
    valid_buyer_data.pop("tax_scheme")
    address_calls = []
    monkeypatch.setattr("app.services.buyer_service.find_buyer_by_account_id", lambda db, a: None)
    monkeypatch.setattr("app.services.buyer_service.insert_address", lambda db, a: address_calls.append(a) or [("addr-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer_tax_scheme", lambda db, t: [("tax-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer", lambda db, d, a, t: [("buyer-id",)])

    create_buyer_service(mock_db, valid_buyer_data)
    assert len(address_calls) == 0


def test_create_buyer_without_tax_scheme_skips_insert(monkeypatch, mock_db, valid_buyer_data):
    valid_buyer_data.pop("tax_scheme")
    tax_calls = []
    monkeypatch.setattr("app.services.buyer_service.find_buyer_by_account_id", lambda db, a: None)
    monkeypatch.setattr("app.services.buyer_service.insert_address", lambda db, a: [("addr-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer_tax_scheme", lambda db, t: tax_calls.append(t) or [("tax-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer", lambda db, d, a, t: [("buyer-id",)])

    create_buyer_service(mock_db, valid_buyer_data)
    assert len(tax_calls) == 0


def test_create_buyer_passes_correct_params_to_insert(monkeypatch, mock_db, valid_buyer_data):
    captured = {}
    valid_buyer_data.pop("tax_scheme")
    monkeypatch.setattr("app.services.buyer_service.find_buyer_by_account_id", lambda db, a: None)
    monkeypatch.setattr("app.services.buyer_service.insert_address", lambda db, a: [("addr-id",)])
    monkeypatch.setattr("app.services.buyer_service.insert_buyer_tax_scheme", lambda db, t: [("tax-id",)])

    def fake_insert_buyer(db, data, addr_id, tax_id):
        captured["addr_id"] = addr_id
        captured["tax_id"] = tax_id
        captured["party_name"] = data.get("party_name")
        return [("buyer-id",)]

    monkeypatch.setattr("app.services.buyer_service.insert_buyer", fake_insert_buyer)
    create_buyer_service(mock_db, valid_buyer_data)

    assert captured["party_name"] == "IYT Corporation"
    assert captured["addr_id"] == "addr-id"
    assert captured["tax_id"] is None

def test_find_buyer_by_account_id_calls_db(mock_db):
    mock_db.execute_query.return_value = [("buyer-id",)]
    result = find_buyer_by_account_id(mock_db, "XFB01")
    mock_db.execute_query.assert_called_once()
    assert result == [("buyer-id",)]


def test_find_buyer_by_account_id_not_found(mock_db):
    mock_db.execute_query.return_value = None
    result = find_buyer_by_account_id(mock_db, "UNKNOWN")
    assert result is None


def test_insert_buyer_tax_scheme_calls_db(mock_db):
    mock_db.execute_insert_update_delete.return_value = [("tax-scheme-id",)]
    tax = {
        "registration_name": "IYT Tax", "company_id": "123",
        "exemption_reason": "Local Authority",
        "scheme_id": "VAT", "tax_type_code": "VAT"
    }
    result = insert_buyer_tax_scheme(mock_db, tax)
    mock_db.execute_insert_update_delete.assert_called_once()
    assert result == [("tax-scheme-id",)]


def test_insert_buyer_calls_db(mock_db):
    mock_db.execute_insert_update_delete.return_value = [("new-buyer-id",)]
    data = {
        "party_name": "IYT Corp",
        "customer_assigned_account_id": "XFB01",
        "supplier_assigned_account_id": "GT01",
        "contact": {
            "name": "Fred", "telephone": "0127", "telefax": "0128", "email": "f@c.com"
        }
    }
    result = insert_buyer(mock_db, data, "addr-id", "tax-id")
    mock_db.execute_insert_update_delete.assert_called_once()
    assert result == [("new-buyer-id",)]


def test_insert_buyer_passes_correct_params(mock_db):
    mock_db.execute_insert_update_delete.return_value = [("buyer-id",)]
    data = {
        "party_name": "IYT Corp",
        "customer_assigned_account_id": "XFB01",
        "supplier_assigned_account_id": None,
        "contact": {"name": "Fred", "telephone": "111", "telefax": "222", "email": "a@b.com"}
    }
    insert_buyer(mock_db, data, "addr-id", "tax-id")
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["party_name"] == "IYT Corp"
    assert params["customer_assigned_account_id"] == "XFB01"
    assert params["address_id"] == "addr-id"
    assert params["tax_scheme_id"] == "tax-id"
    assert params["contact_name"] == "Fred"
    assert params["contact_email"] == "a@b.com"


def test_get_buyer_by_id_not_found(mock_db):
    mock_db.execute_query.return_value = None
    result = get_buyer_by_id(mock_db, "unknown-id")
    assert result is None


def test_get_buyer_by_id_returns_mapped_dict(mock_db):
    mock_db.execute_query.return_value = (
        "buyer-uuid", "XFB01", "GT01", "IYT Corp",
        "Fred", "0127", "0128", "fred@iyt.com",
        "tax-id", "IYT Tax", "123", "Local Authority", "VAT", "VAT",
        "10 Pitt St", "Sydney", "NSW", "2000", "AU"
    )
    result = get_buyer_by_id(mock_db, "buyer-uuid")
    assert result["buyer_id"] == "buyer-uuid"
    assert result["party_name"] == "IYT Corp"
    assert result["customer_assigned_account_id"] == "XFB01"
    assert result["contact"]["name"] == "Fred"
    assert result["contact"]["email"] == "fred@iyt.com"
    assert result["tax_scheme"]["scheme_id"] == "VAT"
    assert result["address"]["city"] == "Sydney"
    assert result["address"]["country_code"] == "AU"


def test_get_buyer_by_id_no_tax_scheme(mock_db):
    mock_db.execute_query.return_value = (
        "buyer-uuid", "XFB01", None, "IYT Corp",
        "Fred", "0127", "0128", "fred@iyt.com",
        None, None, None, None, None, None,
        "10 Pitt St", "Sydney", "NSW", "2000", "AU"
    )
    result = get_buyer_by_id(mock_db, "buyer-uuid")
    assert result["tax_scheme"] is None


def test_get_buyer_by_id_no_address(mock_db):
    mock_db.execute_query.return_value = (
        "buyer-uuid", "XFB01", None, "IYT Corp",
        "Fred", "0127", "0128", "fred@iyt.com",
        None, None, None, None, None, None,
        None, None, None, None, None
    )
    result = get_buyer_by_id(mock_db, "buyer-uuid")
    assert result["address"] is None