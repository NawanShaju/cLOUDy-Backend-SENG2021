from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser

class Address(BaseModel):
    street: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country_code: str = ""

class Contact(BaseModel):
    name: str = ""
    telephone: str = ""
    telefax: str = ""
    email: str = ""

class TaxScheme(BaseModel):
    registration_name: str = ""
    company_id: str = ""
    exemption_reason: str = ""
    scheme_id: str = ""
    tax_type_code: str = ""

class Buyer(BaseModel):
    party_name: str = ""
    customer_assigned_account_id: str = ""
    supplier_assigned_account_id: str = ""
    address: Address = Address()
    contact: Contact = Contact()
    tax_scheme: TaxScheme = TaxScheme()

class Order(BaseModel):
    order_date: str = ""
    delivery_date: str = ""
    currency_code: str = ""
    address: Address = Address()

class OrderExtraction(BaseModel):
    order: Order = Order()
    buyer: Buyer = Buyer()


parser = PydanticOutputParser(
    pydantic_object=OrderExtraction
)
