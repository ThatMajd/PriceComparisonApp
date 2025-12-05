from backend.vendor_scrapper import BaseVendorScraper
from backend.vendor_registeration import *
from backend.vendor_scrapper import VendorConfig, SearchResultProduct
from backend.vendor_selectors import *
import asyncio
from typing import List
import aiohttp

VENDORS = {
    "Traklin": (TraklinScraper, TraklinConfig),
    "Payngo": (PayngoScraper, PayngoConfig),
    "Shekem": (ShekemScraper, ShekemConfig),
    "LastPrice" : (LastPriceScraper, LastPriceConfig),
    "KSP": (KSPScraper, KSPConfig)
}

def build():
    scrappers = []
    
    for vendor in VENDORS:
        scraper, cfg = VENDORS[vendor]
        scrappers.append(scraper(
            vendor_name=vendor,
            config=cfg
        ))
    return scrappers

async def main():
    
    scrapers: List[BaseVendorScraper] = build()
    query = "GR-728B"
    
    async with aiohttp.ClientSession() as session:
        # Build coroutines (no await here)
        coros = [scraper.run(session, query) for scraper in scrapers]
        # Or use search_products if that’s the actual method name

        # Await them concurrently
        results = await asyncio.gather(*coros, return_exceptions=True)

        # Optional: label results by vendor and handle exceptions
        for scraper, res in zip(scrapers, results):
            if isinstance(res, Exception):
                print(f"{scraper.vendor_name}: ERROR -> {res}")
            else:
                print(f"{scraper.vendor_name} - {res if res else None}")
    
    # srchrslt = SearchResultProduct(**{'name': 'מקרר 4 דלתות מקפיא תחתון אינוורטר 665 ליטר LG GR-728B No Frost - צבע נירוסטה מושחרת', 'description': 'מקרר 4 דלתות מקפיא תחתון אינוורטר 665 ליטר LG No Frost - כולל מדחס אינוורטר שקט וחסכוני באנרגיה, בקרה נוחה ומהירה, ניתן לשלוט במקרר דרך טלפון החכם מרחוק, מדפים מודולריים מזכוכית מחוסמת בתא קירור ועוד. מאושר לשבת מהדרין באישור המכון מדעי טכנולוגי להלכה.', 'SKU': 330693, 'url': 'https://ksp.co.il/web/item/330693', 'img_src': 'https://ksp.co.il/shop/items/330693.jpg?v=5', 'orig_price': 7990, 'disc_price': 7990})
    
    # traklin_scraper = TraklinScraper("Traklin", TraklinConfig)
    
    # async with aiohttp.ClientSession() as session:
    #     print(await traklin_scraper.run(session, query))
    
    
if __name__ == "__main__":
    asyncio.run(main())