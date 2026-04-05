import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

def make_db(query_result=None, insert_result=None, fetch_all_result=None):
    db = MagicMock()
    db.execute_query.return_value = query_result
    db.execute_insert_update_delete.return_value = insert_result
    def _query(sql, params, fetch_all=False):
        if fetch_all:
            return fetch_all_result
        return query_result
    db.execute_query.side_effect = _query
    return db

class TestFindSellerByAccountId:
 
    def test_returns_result_when_found(self):
        from app.services.db_services.seller_db import find_seller_by_account_id
        db = make_db(query_result=("seller-uuid",))
        result = find_seller_by_account_id(db, "ACC-001")
        assert result == ("seller-uuid",)
        db.execute_query.assert_called_once()
 
    def test_returns_none_when_not_found(self):
        from app.services.db_services.seller_db import find_seller_by_account_id
        db = make_db(query_result=None)
        result = find_seller_by_account_id(db, "UNKNOWN")
        assert result is None
 
    def test_passes_correct_account_id(self):
        from app.services.db_services.seller_db import find_seller_by_account_id
        db = make_db(query_result=None)
        find_seller_by_account_id(db, "ACC-XYZ")
        call_params = db.execute_query.call_args[0][1]
        assert call_params["customer_assigned_account_id"] == "ACC-XYZ"
 
 
class TestInsertSeller:
 
    def _make_data(self, **overrides):
        base = {
            "customer_assigned_account_id": "ACC-001",
            "supplier_assigned_account_id": "SUP-001",
            "party_name": "Acme Corp",
            "contact": {
                "name": "Jane Doe",
                "telephone": "0400000000",
                "telefax": "0299999999",
                "email": "jane@acme.com",
            },
        }
        base.update(overrides)
        return base
 
    def test_insert_returns_seller_id(self):
        from app.services.db_services.seller_db import insert_seller
        db = MagicMock()
        db.execute_insert_update_delete.return_value = [["new-seller-id"]]
 
        result = insert_seller(db, self._make_data(), address_id=1, tax_scheme_id=2)
 
        assert result[0][0] == "new-seller-id"
 
    def test_insert_passes_correct_params(self):
        from app.services.db_services.seller_db import insert_seller
        db = MagicMock()
        db.execute_insert_update_delete.return_value = [["id"]]
        data = self._make_data()
 
        insert_seller(db, data, address_id=10, tax_scheme_id=20)
 
        params = db.execute_insert_update_delete.call_args[0][1]
        assert params["party_name"] == "Acme Corp"
        assert params["address_id"] == 10
        assert params["tax_scheme_id"] == 20
        assert params["contact_name"] == "Jane Doe"
        assert params["contact_email"] == "jane@acme.com"
 
    def test_insert_handles_missing_contact(self):
        from app.services.db_services.seller_db import insert_seller
        db = MagicMock()
        db.execute_insert_update_delete.return_value = [["id"]]
        data = self._make_data()
        del data["contact"]
 
        insert_seller(db, data, address_id=None, tax_scheme_id=None)
 
        params = db.execute_insert_update_delete.call_args[0][1]
        assert params["contact_name"] is None
        assert params["contact_email"] is None
 
 
class TestGetSellerById:
 
    def _make_row(self):
        return (
            "seller-uuid",       # 0  seller_id
            "ACC-001",           # 1  customer_assigned_account_id
            "SUP-001",           # 2  supplier_assigned_account_id
            "Acme Corp",         # 3  party_name
            "Jane Doe",          # 4  contact_name
            "0400000000",        # 5  contact_telephone
            "0299999999",        # 6  contact_telefax
            "jane@acme.com",     # 7  contact_email
            1,                   # 8  tax_scheme_id (truthy → include tax_scheme)
            "Acme Reg",          # 9  registration_name
            "ABN123",            # 10 company_id
            None,                # 11 exemption_reason
            "GST",               # 12 scheme_id
            "VAT",               # 13 tax_type_code
            "123 Main St",       # 14 street
            "Sydney",            # 15 city
            "NSW",               # 16 state
            "2000",              # 17 postal_code
            "AU",                # 18 country_code
        )
 
    def test_returns_none_when_not_found(self):
        from app.services.db_services.seller_db import get_seller_by_id
        db = make_db(query_result=None)
        assert get_seller_by_id(db, "missing-id") is None
 
    def test_returns_structured_dict(self):
        from app.services.db_services.seller_db import get_seller_by_id
        db = make_db(query_result=self._make_row())
        result = get_seller_by_id(db, "seller-uuid")
 
        assert result["seller_id"] == "seller-uuid"
        assert result["party_name"] == "Acme Corp"
        assert result["contact"]["email"] == "jane@acme.com"
        assert result["tax_scheme"]["scheme_id"] == "GST"
        assert result["address"]["city"] == "Sydney"
        assert result["address"]["country_code"] == "AU"
 
    def test_tax_scheme_is_none_when_no_tax_scheme_id(self):
        from app.services.db_services.seller_db import get_seller_by_id
        row = list(self._make_row())
        row[8] = None  # tax_scheme_id = None
        db = make_db(query_result=tuple(row))
        result = get_seller_by_id(db, "seller-uuid")
        assert result["tax_scheme"] is None
 
    def test_address_is_none_when_no_street(self):
        from app.services.db_services.seller_db import get_seller_by_id
        row = list(self._make_row())
        row[14] = None  # street = None
        db = make_db(query_result=tuple(row))
        result = get_seller_by_id(db, "seller-uuid")
        assert result["address"] is None
 
    def test_seller_id_is_string(self):
        from app.services.db_services.seller_db import get_seller_by_id
        row = list(self._make_row())
        row[0] = 42  # numeric ID from DB
        db = make_db(query_result=tuple(row))
        result = get_seller_by_id(db, 42)
        assert isinstance(result["seller_id"], str)
 
 
class TestCreateSellerService:
 
    def _valid_data(self, **overrides):
        base = {
            "party_name": "Acme Corp",
            "customer_assigned_account_id": "ACC-001",
        }
        base.update(overrides)
        return base
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    @patch("app.services.seller_service.insert_seller")
    def test_creates_seller_successfully(self, mock_insert, mock_find):
        from app.services.seller_service import create_seller_service
        mock_find.return_value = None
        mock_insert.return_value = [["new-uuid"]]
        db = MagicMock()
 
        result = create_seller_service(db, self._valid_data())
 
        assert result["seller_id"] == "new-uuid"
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    def test_missing_party_name_returns_400(self, mock_find):
        from app.services.seller_service import create_seller_service
        db = MagicMock()
        result, status = create_seller_service(db, {"customer_assigned_account_id": "ACC-001"})
        assert status == 400
        assert "party_name" in result["error"]
        mock_find.assert_not_called()
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    def test_missing_account_id_returns_400(self, mock_find):
        from app.services.seller_service import create_seller_service
        db = MagicMock()
        result, status = create_seller_service(db, {"party_name": "Acme"})
        assert status == 400
        assert "customer_assigned_account_id" in result["error"]
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    def test_duplicate_account_id_returns_409(self, mock_find):
        from app.services.seller_service import create_seller_service
        mock_find.return_value = ("existing-seller-id",)
        db = MagicMock()
 
        result, status = create_seller_service(db, self._valid_data())
 
        assert status == 409
        assert "already exists" in result["error"]
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    @patch("app.services.seller_service.insert_address")
    @patch("app.services.seller_service.insert_seller")
    def test_inserts_address_when_provided(self, mock_insert, mock_addr, mock_find):
        from app.services.seller_service import create_seller_service
        mock_find.return_value = None
        mock_addr.return_value = [[99]]
        mock_insert.return_value = [["seller-id"]]
        db = MagicMock()
 
        data = self._valid_data(address={"street": "1 Main St", "city": "Sydney"})
        create_seller_service(db, data)
 
        mock_addr.assert_called_once_with(db, {"street": "1 Main St", "city": "Sydney"})
        call_kwargs = mock_insert.call_args[0]
        assert call_kwargs[2] == 99  # address_id
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    @patch("app.services.seller_service.insert_tax_scheme")
    @patch("app.services.seller_service.insert_seller")
    def test_inserts_tax_scheme_when_provided(self, mock_insert, mock_tax, mock_find):
        from app.services.seller_service import create_seller_service
        mock_find.return_value = None
        mock_tax.return_value = [[55]]
        mock_insert.return_value = [["seller-id"]]
        db = MagicMock()
 
        data = self._valid_data(tax_scheme={"scheme_id": "GST"})
        create_seller_service(db, data)
 
        mock_tax.assert_called_once_with(db, {"scheme_id": "GST"})
        call_kwargs = mock_insert.call_args[0]
        assert call_kwargs[3] == 55  # tax_scheme_id
 
    @patch("app.services.seller_service.find_seller_by_account_id")
    @patch("app.services.seller_service.insert_seller")
    def test_address_and_tax_scheme_none_when_not_provided(self, mock_insert, mock_find):
        from app.services.seller_service import create_seller_service
        mock_find.return_value = None
        mock_insert.return_value = [["seller-id"]]
        db = MagicMock()
 
        create_seller_service(db, self._valid_data())
 
        call_kwargs = mock_insert.call_args[0]
        assert call_kwargs[2] is None  # address_id
        assert call_kwargs[3] is None  # tax_scheme_id