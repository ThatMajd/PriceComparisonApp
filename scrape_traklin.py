import asyncio
import logging
import aiohttp
from typing import Optional

from backend.vendor_registeration import TraklinScraper, TraklinConfig
from backend.vendor_models import ProductSchema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def search_traklin(query: str) -> Optional[ProductSchema]:
    """
    Search for a product on Traklin using the provided query.
    
    Args:
        query (str): The search query (e.g., product name or model).
        
    Returns:
        Optional[ProductSchema]: The found product details or None if search failed/no results.
    """
    scraper = TraklinScraper(
        vendor_name="Traklin",
        config=TraklinConfig,
        logger=logger
    )
    
    logger.info(f"Starting search for query: '{query}'")
    
    try:
        async with aiohttp.ClientSession() as session:
            result = await scraper.run(session, query)
            
            if result:
                logger.info(f"Successfully found product: {result.name}")
                return result
            else:
                logger.warning(f"No product found for query: '{query}'")
                return None
                
    except Exception as e:
        logger.error(f"Error occurred while scraping Traklin: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    # Example usage
    async def main():
        query = "AG653"  # Example query from playground.py
        result = await search_traklin(query)
        if result:
            print("\n--- Product Found ---")
            print(result)
        else:
            print("\n--- No Result ---")

    asyncio.run(main())
