-- Create Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    website_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create Products Table
CREATE TABLE IF NOT EXISTS products (
    traklin_sku INTEGER,
    vendor_sku VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (traklin_sku, vendor_sku)
);

-- Create Product Snapshots Table
CREATE TABLE IF NOT EXISTS product_snapshots (
    id SERIAL PRIMARY KEY,
    traklin_sku INTEGER NOT NULL,
    vendor_sku VARCHAR(255) NOT NULL,
    scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Core product data
    name VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    
    -- Pricing
    offers_price INTEGER,
    orig_price INTEGER,
    disc_price INTEGER,
    currency VARCHAR(10) DEFAULT 'ILS',
    
    -- Product details
    images JSONB DEFAULT '[]',
    description TEXT,
    availability VARCHAR(100),
    item_condition VARCHAR(100),
    brand VARCHAR(255),
    metadata JSONB,
    
    FOREIGN KEY (traklin_sku, vendor_sku) REFERENCES products(traklin_sku, vendor_sku) ON DELETE CASCADE
);
