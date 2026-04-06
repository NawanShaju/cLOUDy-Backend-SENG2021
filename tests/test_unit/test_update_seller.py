import pytest
from unittest.mock import MagicMock
from app.services.seller_service import update_seller_service
from app.services.db_services.seller_db import update_seller


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def valid_update_seller_data():
    return {
        "party_name": "Updated Seller Pty Ltd",
        "supplier_assigned_account_id": "SUP-NEW-001",
        "address": {
            "street": "20 George St",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "country_code": "AU"
        },
        "contact": {
            "name": "Updated Seller Contact",
            "telephone": "0400000000",
            "telefax": "0299999999",
            "email": "updated@seller.com"
        },
        "tax_scheme": {
            "registration_name": "Updated Seller Tax Name",
            "company_id": "999999",
            "exemption_reason": "None",
            "scheme_id": "GST",
            "tax_type_code": "GST"
        }
    }


def test_update_seller_not_found_returns_404(monkeypatch, mock_db, valid_update_seller_data):
    monkeypatch.setattr("app.services.seller_service.get_seller_by_id", lambda db, seller_id: None)

    result = update_seller_service(mock_db, "missing-id", valid_update_seller_data)

    assert isinstance(result, tuple)
    assert result[1] == 404
    assert result[0]["error"] == "Seller not found"


def test_update_seller_empty_request_body_returns_400(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )

    result = update_seller_service(mock_db, "seller-uuid-1234", {},)

    assert isinstance(result, tuple)
    assert result[1] == 400
    assert result[0]["error"] == "Request body cannot be empty"


def test_update_seller_with_address_and_tax_scheme_calls_helpers(monkeypatch, mock_db, valid_update_seller_data):
    captured = {}

    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )
    monkeypatch.setattr(
        "app.services.seller_service.insert_address",
        lambda db, address: [("new-address-id",)]
    )
    monkeypatch.setattr(
        "app.services.seller_service.insert_tax_scheme",
        lambda db, tax_scheme: [("new-tax-id",)]
    )

    def fake_update_seller(db, seller_id, data, address_id, tax_scheme_id):
        captured["seller_id"] = seller_id
        captured["address_id"] = address_id
        captured["tax_scheme_id"] = tax_scheme_id
        captured["party_name"] = data.get("party_name")
        return True

    monkeypatch.setattr("app.services.seller_service.update_seller", fake_update_seller)

    result = update_seller_service(mock_db, "seller-uuid-1234", valid_update_seller_data)

    assert isinstance(result, dict)
    assert result["seller_id"] == "seller-uuid-1234"
    assert captured["seller_id"] == "seller-uuid-1234"
    assert captured["address_id"] == "new-address-id"
    assert captured["tax_scheme_id"] == "new-tax-id"
    assert captured["party_name"] == "Updated Seller Pty Ltd"


def test_update_seller_without_address_and_tax_scheme_skips_insert(monkeypatch, mock_db):
    data = {
        "party_name": "Only Name Changed"
    }

    address_calls = []
    tax_calls = []

    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )
    monkeypatch.setattr(
        "app.services.seller_service.insert_address",
        lambda db, address: address_calls.append(address) or [("new-address-id",)]
    )
    monkeypatch.setattr(
        "app.services.seller_service.insert_tax_scheme",
        lambda db, tax_scheme: tax_calls.append(tax_scheme) or [("new-tax-id",)]
    )
    monkeypatch.setattr(
        "app.services.seller_service.update_seller",
        lambda db, seller_id, data, address_id, tax_scheme_id: True
    )

    result = update_seller_service(mock_db, "seller-uuid-1234", data)

    assert isinstance(result, dict)
    assert result["seller_id"] == "seller-uuid-1234"
    assert len(address_calls) == 0
    assert len(tax_calls) == 0


def test_update_seller_no_valid_fields_returns_400(monkeypatch, mock_db, valid_update_seller_data):
    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )
    monkeypatch.setattr(
        "app.services.seller_service.insert_address",
        lambda db, address: [("new-address-id",)]
    )
    monkeypatch.setattr(
        "app.services.seller_service.insert_tax_scheme",
        lambda db, tax_scheme: [("new-tax-id",)]
    )
    monkeypatch.setattr(
        "app.services.seller_service.update_seller",
        lambda db, seller_id, data, address_id, tax_scheme_id: False
    )

    result = update_seller_service(mock_db, "seller-uuid-1234", valid_update_seller_data)

    assert isinstance(result, tuple)
    assert result[1] == 400
    assert result[0]["error"] == "No valid fields provided for update"


def test_update_seller_calls_db(mock_db):
    data = {"party_name": "Updated Name"}
    update_seller(mock_db, "seller-uuid-1234", data)

    mock_db.execute_insert_update_delete.assert_called_once()


def test_update_seller_returns_false_when_no_fields(mock_db):
    result = update_seller(mock_db, "seller-uuid-1234", {})
    assert result is False


def test_update_seller_passes_correct_params(mock_db):
    data = {
        "party_name": "Updated Name",
        "customer_assigned_account_id": "NEW-CO001",
        "contact": {
            "name": "Updated Seller",
            "email": "updated@seller.com"
        }
    }

    update_seller(mock_db, "seller-uuid-1234", data, "addr-id", "tax-id")

    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["seller_id"] == "seller-uuid-1234"
    assert params["party_name"] == "Updated Name"
    assert params["customer_assigned_account_id"] == "NEW-CO001"
    assert params["address_id"] == "addr-id"
    assert params["tax_scheme_id"] == "tax-id"
    assert params["contact_name"] == "Updated Seller"
    assert params["contact_email"] == "updated@seller.com"