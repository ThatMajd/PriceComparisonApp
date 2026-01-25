from bs4 import BeautifulSoup
from backend.vendor_models import SearchResultProduct
import logging

logger = logging.getLogger(__name__)


class InvalidAPIResponseError(Exception):
    """Raised when the API response doesn't match the expected protocol."""
    pass

class VendorNotSupportedError(Exception):
    """Raised when vendor is not yet supported."""
    pass

class ConfigurationError(Exception):
    """Raised when an incorrect configuration is setup"""

# TODO
# 1. Move the exception to a seprate file
# 2. No need for strict checking of all keys

get_nums_from_string = lambda x: "".join([c for c in str(x) if c.isdigit()])


def one_liner(x):
    if isinstance(x, list):
        return " ".join(x)
    return str(x)


def traklin_selector(results):
    # Check for required structure
    if not isinstance(results, list):
        raise InvalidAPIResponseError("Traklin API response must be a list of results")
    if len(results) == 0:
        return []

    parsed_results = []
    for item in results:

        required_keys = ["name", "description", "catalog_number", "href", "img_src"]
        for key in required_keys:
            if key not in item:
                raise InvalidAPIResponseError(f"Traklin API response missing key: {key}")

        parsed_results.append(SearchResultProduct(
            name=one_liner(item["name"]),
            description=one_liner(item["description"]),
            SKU=get_nums_from_string(item["catalog_number"]),
            url=item["href"],
            img_src=item["img_src"],
            orig_price=0,
            disc_price=0,
            additional_info={
                "internal_id": int(item["value"]),
            }
        ))
    return parsed_results


def payngo_selector(results):
    if "items" not in results:
        raise InvalidAPIResponseError("Payngo API response missing 'items' key")
    if len(results["items"]) == 0:
        return []

    parsed_results = []
    for item in results["items"]:
        # required_keys = ["l", "d", "sku", "u", "t2", "p_c", "p"]
        # for key in required_keys:
        #     if key not in item:
        #         raise InvalidAPIResponseError(f"Payngo API response missing key: {key}")

        parsed_results.append(
        SearchResultProduct(
            name=one_liner(item["l"]),
            description=one_liner(item["d"]),
            SKU=item["sku"],
            url=item["u"],
            img_src=item["t2"],
            orig_price=item["p_c"],
            disc_price=item["p"],
        ))
    return parsed_results


def shekem_selector(results):
    return payngo_selector(results)


def lastprice_selector(results):
    if "products" not in results:
        raise InvalidAPIResponseError("LastPrice API response missing 'products' key")
    if not isinstance(results, dict):
        raise InvalidAPIResponseError(f"LastPrice API returned {type(results)} instead of dict")
    
    if len(results["products"]) == 0:
        return []
    
    parsed_results = []
    for item in results["products"]:
        required_keys = ["title", "subtitle", "productId", "url", "image"]
        for key in required_keys:
            if key not in item:
                raise InvalidAPIResponseError(f"LastPrice API response missing key: {key}")

        parsed_results.append(SearchResultProduct(
            name=one_liner(item["title"]),
            description=one_liner(item["subtitle"]),
            SKU=item["productId"],
            url=item["url"],
            img_src=item["image"],
            orig_price=0,
            disc_price=0,
        ))
    return parsed_results


def ksp_selector(results):
    if "result" not in results and "items" not in results["result"]:
        raise InvalidAPIResponseError("KSP API response missing 'result' key or 'result->items' key")
    if len(results["result"]["items"]) == 0:
        return []

    # item = results["result"]["items"][0]
    
    parsed_results = []
    for item in results["result"]["items"]:
        # required_keys = ["name", "description", "uin", "img", "price", "min_price"]
        # for key in required_keys:
        #     if key not in item:
        #         raise InvalidAPIResponseError(f"KSP API response missing key: {key}")

        parsed_results.append(SearchResultProduct(
            name=one_liner(item["name"]),
            description=item["description"],
            SKU=item["uin"],
            url=f"https://ksp.co.il/web/item/{item['uin']}",
            img_src=item["img"],
            orig_price=item["price"],
            disc_price=item["min_price"],
        ))
    return parsed_results


def neto_selector(results):
    try:
        html = results['10']['html']

        if not html:
            raise InvalidAPIResponseError("Neto API response 'html' is empty")
        
    except KeyError:
        raise InvalidAPIResponseError("Neto API response missing 'html' key")
    
    soup = BeautifulSoup(html, "html.parser")

    # Each product is in <li class="amsearch-item product-item">
    for li in soup.select("ul.amsearch-product-list li.amsearch-item.product-item"):
        # URL: prefer data-click-url, fallback to the product link
        url = li.get("data-click-url")
        if not url:
            link_el = li.select_one("a.amsearch-link")
            url = link_el["href"] if link_el and link_el.has_attr("href") else None

        # Name: text of the product link
        name_el = li.select_one("a.amsearch-link")
        name = name_el.get_text(strip=True) if name_el else None


        # Image URL
        img_el = li.select_one("img.product-image-photo")
        img_src = img_el["src"] if img_el and img_el.has_attr("src") else None

        # Price: data-price-amount attribute
        price_el = li.select_one("[data-price-type='basePrice']")
        disc_price = None
        if price_el and price_el.has_attr("data-price-amount"):
            try:
                disc_price = int(float(price_el["data-price-amount"]))
            except ValueError:
                pass

        # Optional brand and internal product id for additional_info
        # brand_img = li.select_one(".amshopby-option-link img")
        # brand = brand_img["alt"] if brand_img and brand_img.has_attr("alt") else None

        price_box = li.select_one(".price-box")

        # SKU: highlighted part (e.g. AG653)
        # sku_el = li.select_one("a.amsearch-link span.amsearch-highlight")
        # sku = sku_el.get_text(strip=True) if sku_el else None
        sku = (
            price_box["data-product-id"]
            if price_box and price_box.has_attr("data-product-id")
            else "MISSING"
        )

        additional_info: Dict[str, Any] = {}
        # if brand:
        #     additional_info["brand"] = brand
        # if sku is not None:
        #     additional_info["internal_id"] = sku

        return {
            "name": name,
            "SKU": sku,
            "url": url,
            "img_src": img_src,
            "orig_price": disc_price,
            "disc_price": None,
            "additional_info": additional_info,
        }
        
def neto_selector(results):
    try:
        html = results['10']['html']

        if not html:
            raise InvalidAPIResponseError("Neto API response 'html' is empty")
        
    except KeyError:
        raise InvalidAPIResponseError("Neto API response missing 'html' key")
    
    soup = BeautifulSoup(html, "html.parser")

    parsed_results = []

    # Each product is in <li class="amsearch-item product-item">
    for li in soup.select("ul.amsearch-product-list li.amsearch-item.product-item"):
        # URL: prefer data-click-url, fallback to the product link
        url = li.get("data-click-url")
        if not url:
            link_el = li.select_one("a.amsearch-link")
            url = link_el["href"] if link_el and link_el.has_attr("href") else None

        # Name: text of the product link
        name_el = li.select_one("a.amsearch-link")
        name = name_el.get_text(strip=True) if name_el else None


        # Image URL
        img_el = li.select_one("img.product-image-photo")
        img_src = img_el["src"] if img_el and img_el.has_attr("src") else None

        # Price: data-price-amount attribute
        price_el = li.select_one("[data-price-type='basePrice']")
        disc_price = None
        if price_el and price_el.has_attr("data-price-amount"):
            try:
                disc_price = int(float(price_el["data-price-amount"]))
            except ValueError:
                pass

        # Optional brand and internal product id for additional_info
        # brand_img = li.select_one(".amshopby-option-link img")
        # brand = brand_img["alt"] if brand_img and brand_img.has_attr("alt") else None

        price_box = li.select_one(".price-box")

        # SKU: highlighted part (e.g. AG653)
        # sku_el = li.select_one("a.amsearch-link span.amsearch-highlight")
        # sku = sku_el.get_text(strip=True) if sku_el else None
        sku = (
            price_box["data-product-id"]
            if price_box and price_box.has_attr("data-product-id")
            else "MISSING"
        )

        additional_info: Dict[str, Any] = {}
        # if brand:
        #     additional_info["brand"] = brand
        # if sku is not None:
        #     additional_info["internal_id"] = sku

        parsed_results.append(SearchResultProduct(
            name=name,
            SKU=sku,
            url=url,
            img_src=img_src,
            orig_price=disc_price,
            disc_price=None,
            additional_info=additional_info,
        ))
    
    return parsed_results
    
def bigelectric_selector(results):
    raise NotImplementedError("BigElectric API is not yet supported")

    try:
        for categories in results["indexes"]:
            if categories["identifier"] == "magento_catalog_product":
                products = categories["items"]
    except KeyError or IndexError:
        raise InvalidAPIResponseError("BigElectric API response missing 'indexes' key or 'indexes->items' key")
    
    if not products:
        raise InvalidAPIResponseError("BigElectric API returned empty product")
    
    parsed_results = []

    for prod in products:
        parsed_results.append(SearchResultProduct(
            name=prod["name"],
            SKU=prod["sku"],
            url=prod["url"],
            img_src=prod["imageUrl"],
            orig_price=prod["price"].split('.')[0].replace(',', ''),
            disc_price=0,
        ))
    
    return parsed_results
        


_selectors = {
    "Traklin": traklin_selector,
    "Payngo": payngo_selector,
    "Shekem": shekem_selector,
    "LastPrice": lastprice_selector,
    "KSP": ksp_selector,
}

def get_vendor_selector(vendor):
    if vendor not in _selectors.keys():
        raise VendorNotSupportedError(f"{vendor} is not currently supported.")
    
    return _selectors[vendor]


