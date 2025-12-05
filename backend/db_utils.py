import asyncpg
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from backend.vendor_models import ProductSchema

logger = logging.getLogger(__name__)

def safe_int(val):
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return int(val)
        return int("".join(filter(str.isdigit, str(val))))
    except ValueError:
        return None

class Database:
    def __init__(self):
        self.pool = None
        # Default fallback + Env vars
        self.user = os.getenv("POSTGRES_USER", "testuser")
        self.password = os.getenv("POSTGRES_PASSWORD", "testpassword")
        self.database = os.getenv("POSTGRES_DB", "testdb")
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5433") # Defaulting to mapped port for local execution

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    host=self.host,
                    port=self.port
                )
                logger.info("Database connection pool established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def create_scraping_session(self, query: str, initiator: str = "user") -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO scraping_sessions (query, initiator, status, scraped_at)
                VALUES ($1, $2, 'running', NOW())
                RETURNING scrape_id
            """, query, initiator)
            return row['scrape_id']

    async def update_session_status(self, scrape_id: int, status: str, num_results: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE scraping_sessions
                SET status = $1, num_results = $2
                WHERE scrape_id = $3
            """, status, num_results, scrape_id)

    async def upsert_product(self, traklin_sku: int, product: ProductSchema, vendor_name: str):
        """
        Upsert a product record into the products table.
        Note: The products table uses (traklin_sku, vendor_sku) as composite PK.
        """
        async with self.pool.acquire() as conn:
            # Get vendor_id
            vendor_id = await conn.fetchval("SELECT id FROM vendors WHERE name = $1", vendor_name)
            
            await conn.execute("""
                INSERT INTO products (traklin_sku, vendor_sku, vendor_id, name, description, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (traklin_sku, vendor_sku) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    vendor_id = EXCLUDED.vendor_id,
                    updated_at = NOW()
            """, traklin_sku, str(product.SKU), vendor_id, product.name, product.description)

    async def insert_snapshot(self, scrape_id: int, traklin_sku: int, product: ProductSchema):
        async with self.pool.acquire() as conn:
            # We encode images/metadata to json if they differ from None, 
            # but asyncpg handles dict/list -> jsonb automagically if configured or casted? 
            # Usually we need to dump it if passing to text, but for jsonb param asyncpg might need help or a codec.
            # safe fallback: cast simple python types. list/dict maps to JSONB in newer asyncpg but explicit json.dumps is safer often.
            # However asyncpg automatically converts python types to postgres types.
            
            # Using query parameters
            await conn.execute("""
                INSERT INTO product_snapshots (
                    traklin_sku, vendor_sku, scrape_id,
                    name, url,
                    offers_price, orig_price, disc_price, currency,
                    images, description, availability, item_condition, brand, metadata
                ) VALUES (
                    $1, $2, $3,
                    $4, $5,
                    $6, $7, $8, $9,
                    $10::jsonb, $11, $12, $13, $14, $15::jsonb
                )
            """, 
            traklin_sku, str(product.SKU), scrape_id,
            product.name, product.url,
            safe_int(product.offers__price), safe_int(product.orig_price), safe_int(product.disc_price), product.currency,
            import_json(product.images), product.description, product.availability, product.item_condition, product.brand, import_json(product.metadata)
            )

import json
def import_json(val):
    if val is None:
        return 'null'
    return json.dumps(val)
