-- =========================================
-- CLIENTS TABLE
-- =========================================
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- PRODUCTS TABLE
-- =========================================
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name VARCHAR(255),
    product_description TEXT,
    unit_price NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_product UNIQUE (product_name, product_description, unit_price)
);

-- =========================================
-- ADDRESSES TABLE
-- =========================================
CREATE TABLE addresses (
    address_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country_code VARCHAR(10),
    CONSTRAINT unique_address 
        UNIQUE (street, city, state, postal_code, country_code)
);

-- =========================================
-- ORDERS TABLE
-- =========================================
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_buyer_id,
    buyer_id UUID,
    seller_id UUID,
    address_id UUID NOT NULL,
    order_date DATE,
    delivery_date DATE,
    currency_code VARCHAR(10),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_address
        FOREIGN KEY (address_id) REFERENCES addresses(address_id)
    
    CONSTRAINT fk_orders_buyer
        FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id);
    
    CONSTRAINT fk_orders_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id);
);

-- =========================================
-- ORDER ITEMS TABLE
-- =========================================
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    product_id UUID,
    quantity INTEGER,
    total_price NUMERIC(12,2) NOT NULL,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products(product_id),

    CONSTRAINT unique_order_product UNIQUE (order_id, product_id)
);

-- =========================================
-- ORDER DOCUMENTS TABLE
-- =========================================
CREATE TABLE order_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL UNIQUE,
    xml_content TEXT,
    document_version INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_documents_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

-- =========================================
-- BUYERS TABLE
-- =========================================
CREATE TABLE buyers (
    buyer_id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_assigned_account_id    VARCHAR(100),
    supplier_assigned_account_id    VARCHAR(100),

    party_name                      VARCHAR(255),

    address_id                      UUID,

    tax_scheme_id                   UUID,

    contact_name                    VARCHAR(255),
    contact_telephone               VARCHAR(50),
    contact_telefax                 VARCHAR(50),
    contact_email                   VARCHAR(255),

    created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_buyers_address
        FOREIGN KEY (address_id) REFERENCES addresses(address_id),

    CONSTRAINT fk_buyers_tax_scheme
        FOREIGN KEY (tax_scheme_id) REFERENCES tax_schemes(tax_scheme_id)
);

-- =========================================
-- SELLER TABLE
-- =========================================
CREATE TABLE sellers (
    seller_id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_assigned_account_id VARCHAR(100) UNIQUE,
    supplier_assigned_account_id VARCHAR(100),

    party_name                   VARCHAR(255) NOT NULL,

    address_id                   UUID,

    tax_scheme_id                UUID,

    contact_name                 VARCHAR(255),
    contact_telephone            VARCHAR(50),
    contact_telefax              VARCHAR(50),
    contact_email                VARCHAR(255),

    created_at                   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_seller_address
        FOREIGN KEY (address_id) REFERENCES addresses(address_id),

    CONSTRAINT fk_seller_tax_scheme
        FOREIGN KEY (tax_scheme_id) REFERENCES tax_schemes(tax_scheme_id)
);

-- =========================================
-- TAX SCHEMES TABLE
-- =========================================
CREATE TABLE tax_schemes (
    tax_scheme_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    registration_name       VARCHAR(255),
    company_id              VARCHAR(100),
    exemption_reason        VARCHAR(255),
    scheme_id               VARCHAR(50),
    tax_type_code           VARCHAR(50),

    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- INDEXES
-- =========================================
CREATE INDEX idx_orders_external_buyer_id ON orders(external_buyer_id);
CREATE INDEX idx_orders_address_id ON orders(address_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_documents_order_id ON order_documents(order_id);
CREATE INDEX idx_tax_schemes_company_id ON tax_schemes(company_id);
CREATE INDEX idx_buyers_customer_account_id ON buyers(customer_assigned_account_id);
CREATE INDEX idx_buyers_address_id ON buyers(address_id);
CREATE INDEX idx_buyers_tax_scheme_id ON buyers(tax_scheme_id);
CREATE INDEX idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX idx_sellers_seller_id ON sellers(seller_id);
CREATE INDEX idx_sellers_address_id ON sellers(address_id);
CREATE INDEX idx_sellers_tax_scheme_id ON sellers(tax_scheme_id);
CREATE INDEX idx_orders_seller_id ON orders(seller_id);
