## Database Tables

### Vendors
```sql
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    website_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Products
```sql
CREATE TABLE IF NOT EXISTS products (
    traklin_sku INTEGER,
    vendor_sku VARCHAR(255),
    vendor_id INTEGER,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (traklin_sku, vendor_sku),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);
```

### Scraping Sessions
```sql
CREATE TABLE IF NOT EXISTS scraping_sessions (
    scrape_id SERIAL PRIMARY KEY,
    scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    query TEXT,
    num_results INTEGER,
    initiator VARCHAR(50),
    status VARCHAR(50)
);
```

### Product Snapshots
```sql
CREATE TABLE IF NOT EXISTS product_snapshots (
    id SERIAL PRIMARY KEY,
    traklin_sku INTEGER NOT NULL,
    vendor_sku VARCHAR(255) NOT NULL,
    scrape_id INTEGER,
    
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
    
    FOREIGN KEY (traklin_sku, vendor_sku) REFERENCES products(traklin_sku, vendor_sku) ON DELETE CASCADE,
    FOREIGN KEY (scrape_id) REFERENCES scraping_sessions(scrape_id) ON DELETE SET NULL
);
```
