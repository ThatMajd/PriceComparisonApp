import asyncio
import logging
import aiohttp
from typing import List, Optional
from datetime import datetime

from backend.db_utils import Database
from backend.vendor_models import ProductSchema
from backend.vendor_registeration import (
    TraklinScraper, TraklinConfig,
    KSPScraper, KSPConfig,
    PayngoScraper, PayngoConfig,
    ShekemScraper, ShekemConfig,
    LastPriceScraper, LastPriceConfig,
    NetoScraper, NetoConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Registered Scrapers
VENDORS = [
    (TraklinScraper, TraklinConfig),
    (NetoScraper, NetoConfig),
    # (KSPScraper, KSPConfig),
    # (PayngoScraper, PayngoConfig),
    # (ShekemScraper, ShekemConfig),
    # (LastPriceScraper, LastPriceConfig)
]

async def scrape_vendor(scraper_cls, config, query: str) -> Optional[ProductSchema]:
    """Helper to instantiate and run a scraper."""
    scraper_name = config.name
    try:
        scraper = scraper_cls(
            vendor_name=scraper_name,
            config=config,
            logger=logger
        )
        async with aiohttp.ClientSession() as session:
            result = await scraper.run(session, query)
            if result:
                logger.info(f"[{scraper_name}] Found: {result.name} (SKU: {result.SKU})")
                return (scraper_name, result)
            else:
                logger.info(f"[{scraper_name}] No result found.")
                return None
    except Exception as e:
        logger.error(f"[{scraper_name}] Error: {e}")
        return None

async def run_multi_vendor_scrape(query: str, initiator: str = "user"):
    logger.info(f"Starting multi-vendor scrape for query: '{query}'")
    
    db = Database()
    await db.connect()
    
    saved_results = []
    
    try:
        # Create Session
        scrape_id = await db.create_scraping_session(query, initiator)
        logger.info(f"Created scraping session ID: {scrape_id}")

        # Run Scrapers concurrently
        tasks = [scrape_vendor(cls, cfg, query) for cls, cfg in VENDORS]
        results = await asyncio.gather(*tasks)
        
        # Filter valid results
        valid_results = [r for r in results if r is not None]
        logger.info(f"Total valid results found: {len(valid_results)}")

        # Find Traklin Result
        traklin_result = next((r[1] for r in valid_results if r[0] == "Traklin"), None)

        if not traklin_result:
            logger.warning("No Traklin result found. Cannot determine 'traklin_sku' for grouping. Skipping insert.")
            await db.update_session_status(scrape_id, "failed_no_traklin_match", 0)
            return []
        
        # Ensure Traklin result has a valid numeric SKU (based on selector logic it should)
        try:
            traklin_sku = int(traklin_result.SKU)
        except ValueError:
            logger.error(f"Traklin SKU '{traklin_result.SKU}' is not an integer. Cannot insert.")
            await db.update_session_status(scrape_id, "failed_invalid_traklin_sku", 0)
            return []

        # Insert Results
        count = 0
        for vendor_name, product in valid_results:
            try:
                # Upsert Product
                await db.upsert_product(traklin_sku, product, vendor_name)
                
                # Insert Snapshot
                await db.insert_snapshot(scrape_id, traklin_sku, product)
                count += 1
                saved_results.append((vendor_name, product))
            except Exception as e:
                logger.error(f"Failed to save result for {vendor_name}: {e}")

        # Update Session Status
        # Determine overall status
        vendors_called = len(VENDORS)
        valid_count = count
        
        status = "failure"
        if valid_count == vendors_called:
            status = "success"
        elif valid_count > 0:
            status = "partial_success"
            
        await db.update_session_status(scrape_id, status, vendors_called, valid_count)
        logger.info(f"Scraping session {scrape_id} completed. Status: {status}. Saved: {valid_count}/{vendors_called}")
        
        return saved_results

    finally:
        await db.close()

if __name__ == "__main__":
    import sys
    query = "GR-730BINS"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    asyncio.run(run_multi_vendor_scrape(query))
