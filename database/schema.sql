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
    seller_id UUID,
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name VARCHAR(255),
    product_description TEXT,
    unit_price NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE SET NULL;

    CONSTRAINT unique_product_per_seller UNIQUE (seller_id, product_name, product_description, unit_price)
);

-- =========================================
-- PRODUCT INVENTORY TABLE
-- =========================================

CREATE TABLE product_inventory (
    product_inventory_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    inventory_id UUID NOT NULL,
    quantity_required INTEGER NOT NULL DEFAULT 1 CHECK (quantity_required > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pi_product
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT fk_pi_inventory
        FOREIGN KEY (inventory_id) REFERENCES inventory(inventory_id) ON DELETE CASCADE,
    CONSTRAINT unique_product_inventory
        UNIQUE (product_id, inventory_id)
);

-- =========================================
-- INVENTORY TABLE
-- =========================================
CREATE TABLE inventory (
    seller_id UUID NOT NULL,
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_name VARCHAR(255) NOT NULL,
    item_description TEXT,
    purchase_price NUMERIC(12,2) NOT NULL CHECK (purchase_price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE,

    CONSTRAINT unique_inventory_item_per_seller UNIQUE (seller_id, item_name)
);

-- =========================================
-- Carts TABLE
-- =========================================
CREATE TABLE carts (
    cart_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id       UUID NOT NULL,
    currency_code   VARCHAR(10) DEFAULT 'AUD',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_carts_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE,

    CONSTRAINT unique_cart_per_seller UNIQUE (seller_id)
);


-- =========================================
-- Cart Items TABLE
-- =========================================
CREATE TABLE cart_items (
    cart_item_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id         UUID NOT NULL,
    product_id      UUID NOT NULL,
    seller_id       UUID NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(12,2) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cart_items_cart
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id) ON DELETE CASCADE,

    CONSTRAINT fk_cart_items_product
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,

    CONSTRAINT fk_cart_items_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE,

    CONSTRAINT unique_cart_product UNIQUE (cart_id, product_id)
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
-- AUTH TABLE
-- =========================================
CREATE TABLE auth (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key                 VARCHAR(255) NOT NULL,
    buyer_id                VARCHAR(255) NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_auth UNIQUE (api_key, buyer_id)
);

CREATE TABLE seller_auth (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key                 VARCHAR(255) NOT NULL,
    seller_id               UUID NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_seller_auth UNIQUE (api_key, seller_id),
    CONSTRAINT fk_seller_auth_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE
);

CREATE TABLE buyer_seller (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    buyer_id                UUID NOT NULL,
    seller_id               UUID NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_buyer_seller UNIQUE (buyer_id, seller_id),
    CONSTRAINT fk_buyer_seller_buyer
        FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
    CONSTRAINT fk_buyer_seller_seller 
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE
);

CREATE TABLE registered_user (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    seller_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_registered_user_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,

    CONSTRAINT fk_registered_user_seller
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE
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
CREATE INDEX idx_auth_api_key ON auth(api_key);
CREATE INDEX idx_auth_buyer_id ON auth(buyer_id);
CREATE INDEX idx_cart_items_cart_id ON cart_items(cart_id);
CREATE INDEX idx_carts_seller_id ON carts(seller_id);
CREATE INDEX idx_seller_auth_api_key ON seller_auth(api_key);
CREATE INDEX idx_seller_auth_seller_id ON seller_auth(seller_id);
CREATE INDEX idx_buyer_seller_buyer_id ON buyer_seller(buyer_id);
CREATE INDEX idx_buyer_seller_seller_id ON buyer_Seller(seller_id);
CREATE INDEX idx_registered_user_client_id ON registered_user(client_id);
CREATE INDEX idx_registered_user_seller_id ON registered_user(seller_id);
CREATE INDEX idx_registered_user_email ON registered_user(email);
CREATE INDEX idx_registered_user_username ON registered_user(username);
