from langchain_core.prompts import ChatPromptTemplate
from .mode_schema import parser

prompt = ChatPromptTemplate(
    messages=[
        ("system", """You are an AI that extracts procurement order data from unstructured text.
Output ONLY valid JSON. No markdown, no explanation. Start with {{ and end with }}.

ADDRESS EXTRACTION RULES:
- Street addresses can appear in many formats for example: "unit 5/200 George St", "Lot 3 Commerce Blvd", "47 Industrial Ave"
- Unit/suite numbers are PART of the street field: "unit 5/200 George St" → street = "Unit 5/200 George St"
- "ship to", "ship 2", "deliver to", "delivery address", "send to" all indicate the delivery address
- State can be abbreviated (VIC, NSW, QLD) or written in full
- Country can appear as AUS, AU, Australia — always extract it

DATE RULES:
- Normalize all dates to YYYY-MM-DD format
- "march-20-2025", "20th march 2025", "20/03/2025" → "2025-03-20"
- "ordr date", "order date", "dt.", "dated" all indicate the order date
- "wanted by", "deliver by", "delivery date", "no later than" all indicate the delivery date

ACCOUNT RULES:
- "our acct", "cust acct", "customer account", "CUST#" → customer_assigned_account_id
- "suppl. acct", "supplier account", "supp ref" → supplier_assigned_account_id

CURRENCY RULES:
- "$$$=GBP", "currency=AUD", "in USD", "invoicing in AUD" all indicate currency_code
- Always extract the 3-letter ISO currency code

TAX RULES:
- "regd name", "registered name", "registration name" → registration_name
- "abn", "company id", "co_id" → company_id
- "no exemption reason given" or similar → leave exemption_reason as empty string
- "scheme", "schemeID" → scheme_id
- "taxcode", "tax type", "tax code" → tax_type_code

PRODUCT EXTRACTION RULES:
- Extract ALL products mentioned
- There can be multiple products
- Use context to identify product
- Extract product_name and quantity
- Quantity is usually a number before the product or a meaning 1
- Products must be returned inside: "products": []
- If quantity missing → use "1".
- If anything missing → leave empty "".

GENERAL RULES:
- Ignore irrelevant sentences (shipping preferences, notes, complaints)
- If a field cannot be found in the text, use empty string ""
- If delivery address is not given, assume it is the same as the buyer address
"""),
        ("human", "{format_instructions}\n\nTEXT:\n{text}\n\nJSON OUTPUT:")
    ],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)