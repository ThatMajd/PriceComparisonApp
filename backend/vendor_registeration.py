from backend.vendor_models import VendorConfig, SearchResultProduct, FetchMethod, ProductSchema
from backend.vendor_scrapper import BaseVendorScraper
from typing import List, Dict, Any, Optional, Callable
from backend.vendor_selectors import *

import time

TraklinConfig = VendorConfig(
    name="Traklin",
    autocomplete_endpoint="https://www.traklin.co.il/ajax/content_auto_suggest.ashx",
    search_param="prefix"
)

PayngoConfig = VendorConfig(
    name="Payngo",
    autocomplete_endpoint="https://api.instantsearchplus.com",
    search_param="q",
    params={
        "store_id": 1,
        "UUID": "b655c070-2db6-4709-933f-df029bd118a8",
        "cdn_cache_key": "1757229797"
    }   
)

ShekemConfig = VendorConfig(
    name="Shekem",
    autocomplete_endpoint="https://api.instantsearchplus.com",
    search_param="q",
    params={
        "store_id": 2,
        "UUID": "b655c070-2db6-4709-933f-df029bd118a8",
        "cdn_cache_key": "1757229797"
    }   
)

LastPriceConfig = VendorConfig(
    name="LastPrice",
    autocomplete_endpoint="https://www.lastprice.co.il/oapi/oapi_searchbox.asp",
    data={
        "query": "",
        "ResultLimit": "30",
    }  
)

KSPConfig = VendorConfig(
    name="KSP",
    autocomplete_endpoint="https://ksp.co.il/m_action/api/category/0",
    search_param="search",
    fetch_method=FetchMethod.API,
    product_data_endpoint="https://ksp.co.il/m_action/api/item"
)

NetoConfig = VendorConfig(
    name="Neto",
    autocomplete_endpoint="https://www.netoneto.co.il/amasty_xsearch/autocomplete/index/",
    search_param="q",
    fetch_method=FetchMethod.HTML_JSON_LD,
    headers={
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Referer': 'https://www.netoneto.co.il/',
        'X-Requested-With': 'XMLHttpRequest'  # This is key for AJAX requests
    },
    params={
        'uenc': 'aHR0cHM6Ly93d3cubmV0b25ldG8uY28uaWwv',
        'form_key': 'mMDcYUNaMrX29IhX',
        '_': str(int(time.time() * 1000))
    },
    cookies={
        'cf_clearance': 'OytaWgWbXINZ09SCstJ7iIrbfnLWu0LPfQbJr2tBEYA-1765475904-1.2.1.1-...',
        'PHPSESSID': 'b655c070-2db6-4709-933f-df029bd118a8',
        'form_key': 'mMDcYUNaMrX29IhX',
        'private_content_version': '39b9a03dc18ecb2a233e93466e165af4',
        'privateData': '%7B%22search%22%3A%22AG%22%7D'
    },

)


class TraklinScraper(BaseVendorScraper):
    def parse_search_result(self, item):
        return SearchResultProduct(**traklin_selector(item))

class PayngoScraper(BaseVendorScraper):
    def parse_search_result(self, item):
        return SearchResultProduct(**payngo_selector(item))

class ShekemScraper(BaseVendorScraper):
    def parse_search_result(self, item):
        return SearchResultProduct(**shekem_selector(item))

class LastPriceScraper(BaseVendorScraper):
    def parse_search_result(self, item):
        return SearchResultProduct(**lastprice_selector(item))

class KSPScraper(BaseVendorScraper):
    def parse_search_result(self, item):
        return SearchResultProduct(**ksp_selector(item))
    
    def parse_product_data(self, item: Dict[str, Any], search_result_product: SearchResultProduct) -> ProductSchema:
        item__result__data = item["result"]["data"]
        return ProductSchema(
            SKU=item__result__data["uin"],
            name=item__result__data["name"],
            offers__price=item__result__data["price"],
            orig_price=search_result_product.orig_price,
            disc_price=search_result_product.disc_price,
            currency="ILS",
            url=item["seo"]["myUrl"],
            images=[img_obj["sizes"]["b"]["src"] for img_obj in item["result"]['images']],
            description=item__result__data["smalldesc"],
            availability="",
            item_condition="",
            brand=item__result__data["brandName"],
            metadata={
                "cheaperViaPhone": item__result__data["cheaperPriceViaPhone"],
                "redMsg": item["result"]["redMsg"],
                "tags": item["result"]["tags"]
            },
            additional_info=search_result_product.additional_info
        )
    

class NetoScraper(BaseVendorScraper):
    def parse_search_result(self, item):
        return SearchResultProduct(**neto_selector(item))
