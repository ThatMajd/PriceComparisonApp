from asyncio.log import logger
from backend.vendor_exceptions import SearchFailedException
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import aiohttp
# from bs4 import BeautifulSouptouc

from backend.vendor_models import FetchMethod, RequestMethod, ProductSchema, SearchResultProduct, VendorConfig 
from backend.vendor_exceptions import * 

from selectolax.lexbor import LexborHTMLParser

    

class BaseVendorScraper(ABC):
    """Base class for vendor scrapers"""
    
    def __init__(
        self,
        vendor_name: str,
        config: VendorConfig,
        max_concurrent_requests: int = 5,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        self.vendor_name = vendor_name
        self.config = config
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.logger = logger or logging.getLogger(f"{__name__}.{vendor_name}")
        
        
        if self.config.fetch_method == FetchMethod.API:
            if not self.config.product_data_endpoint:
                raise MissingFieldException(f"Can't fetch data through {self.config.fetch_method}, no product data endpoint was provided")
            
            if not hasattr(self, "parse_product_data"):
                raise NotImplementedError(
                    f"{self.__class__.__name__} must implement parse_product_data() for API scrapers, since fetch method is {self.config.fetch_method}"
                )
    
    async def _fetch(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: Optional[Dict[str, str]] = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"}, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, Any]] = None,
        timeout: int = 20,
        is_return_json: bool = False
    ):
        """Fetch URL content with semaphore control"""
        
        # h = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"}
        
        if not url:
            raise ValueError("No URL was provided to the _fetch method, check caller")

        async with self.semaphore:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    data=data,
                    cookies=cookies,
                    timeout=timeout
                ) as response:

                    if response.status != 200:
                        raise SearchFailedException(f"Error fetching {url}: Status {response.status}")
                    
                    if is_return_json:
                        return await response.json(content_type=None)
                    return await response.text()
                
            except aiohttp.ClientError as e:
                raise ProductFetchException(f"Error fetching {url}: {str(e)}") from e
            except asyncio.TimeoutError as e:
                raise ProductFetchException(f"Timeout fetching {url}") from e
    
    async def run(
        self,
        session: aiohttp.ClientSession,
        query: str
    ) -> ProductSchema:
        

        search_results: List[SearchResultProduct] = await self.search_product(session, query)

        if not search_results:
            logger.warning(f"No search result found for query: {query}")
            return None

        # TODO 
        # choose most relevant product later
        most_relevant_product = self.select_product(search_results) # return first product for now
        
        return await self.get_product_data(session, most_relevant_product)
    
    async def fetch_product(
        self,
        session: aiohttp.ClientSession,
        url: str,
        known_sku: Optional[str] = None
    ) -> Optional[ProductSchema]:
        """
        Fetch product data directly from a known URL.
        Used when a manual/automatic match exists.
        Bypasses the search step entirely.
        known_sku: If provided, will be used as fallback SKU if page doesn't contain one.
        """
        # TODO: 
        # This function may be redundant 
        search_result_prod = SearchResultProduct(
            name="",
            url=url,
            SKU=known_sku,  # Pass known SKU as fallback
            orig_price=None,
            disc_price=None
        )
        return await self.get_product_data(session, search_result_prod)

    
    async def search_product(
        self,
        session: aiohttp.ClientSession,
        query: str,
    ) -> List[SearchResultProduct]:
        
        config = self.config
        
        search_endpoint = config.autocomplete_endpoint
        headers = dict(config.headers)
        params = dict(config.params)
        data = dict(config.data)
        cookies = dict(config.cookies)
        
        # Build request 
        if config.search_param:
            params[config.search_param] = query
        else:
            # LastPrice Case
            # TODO add more rigorus handling
            if "query" not in data:
                raise MissingFieldException("query keyword not found in data object, check API behavior")
            data["query"] = query
            
        # raw_products = await self._fetch(session, search_endpoint, headers=headers, params=params, data=data, cookies=cookies, is_return_json=True)
        # # Model Search Result
        # if len(raw_products) == 0:
        #     return None
        
        # # Response may include other items with the products, selectors are used to only return 
        # # the first product!
        # search_result = self.parse_search_result(raw_products)

        response = await self._fetch(session, search_endpoint, headers=headers, params=params, data=data, cookies=cookies, is_return_json=True)

        search_results: List[SearchResultProduct] = self.parse_search_result(response)


        logger.info(f"Found {len(search_results)} results for [{self.vendor_name}]:\n{"\n".join(str(i+1) + ": " + prod.name for i, prod in enumerate(search_results))}")
        
        return search_results

        
    
    @abstractmethod
    def parse_search_result(self, item: Dict[str, Any]) -> List[SearchResultProduct]:
        pass
    
    def select_product(self, items):
        """Heuristic for picking an item from search results"""
        return items[0]
    
    async def get_product_data(
        self,
        session: aiohttp.ClientSession,
        search_result_product: SearchResultProduct
    ) -> ProductSchema:
        
        fetch_method = self.config.fetch_method
        
        if fetch_method == FetchMethod.HTML_JSON_LD:
            return await self._get_prod_data_html_json_ld(session, search_result_product)
        elif fetch_method == FetchMethod.API:
            return await self._get_prod_data_api(session, search_result_product)
    
    async def _get_prod_data_api(
        self,
        session: aiohttp.ClientSession,
        search_result_product: SearchResultProduct
    ):
        
        prod_sku = search_result_product.SKU or search_result_product.url.split("/")[-1]
        prod_url = f"{self.config.product_data_endpoint.strip('/')}/{prod_sku}"
        
        prod_obj = await self._fetch(session, prod_url, is_return_json=True)
        
        return self.parse_product_data(prod_obj, search_result_product)
    
    async def _get_prod_data_html_json_ld(
        self,
        session: aiohttp.ClientSession,
        search_result_product: SearchResultProduct
    ) -> ProductSchema:
        
        # logger.info(search_result_product)
        html = LexborHTMLParser(await self._fetch(session, url=search_result_product.url, headers=self.config.headers, params=self.config.params, data=self.config.data, cookies=self.config.cookies, is_return_json=False))
        
        for node in html.css('script[type="application/ld+json"]'):
            prod_obj = json.loads(node.text())
            
            # Handle itemPage case - for Netoneto
            if prod_obj.get("@type") == "ItemPage" and "mainEntity" in prod_obj:
                prod_obj = prod_obj["mainEntity"]

            if prod_obj.get("@type") == "Product":
                
                prod_sku = prod_obj.get("SKU") or prod_obj["offers"].get("sku") or search_result_product.SKU
                prod_brand = prod_obj.get("brand") if isinstance(prod_obj.get("brand"), str) else prod_obj.get("brand", {"name": ""}).get("name")
                
                if not prod_sku:
                    raise ParseException("No valid SKU found")

                
                return ProductSchema(
                    availability=prod_obj["offers"].get("availability"),
                    item_condition=prod_obj["offers"].get("itemCondition", ""),
                    
                    offers__price=prod_obj["offers"]["price"],
                    currency=prod_obj["offers"].get("priceCurrency"),
                    description=prod_obj["description"],
                    
                    name=prod_obj.get("name", search_result_product.name),
                    url=search_result_product.url,
                    orig_price=search_result_product.orig_price,
                    disc_price=search_result_product.disc_price,
                    
                    SKU=prod_sku,
                    brand=prod_brand,
                    images=[prod_obj.get("image") or search_result_product.img_src],
                    
                    metadata={"aggregateRating": prod_obj.get("aggregateRating")},
                    additional_info=search_result_product.additional_info
                    )
