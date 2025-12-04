from pipeline.exceptions import InvalidAPIResponseError, VendorNotSupportedError

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
        return {}

    item = results[0]
    required_keys = ["name", "description", "catalog_number", "href", "img_src"]
    for key in required_keys:
        if key not in item:
            raise InvalidAPIResponseError(f"Traklin API response missing key: {key}")

    return {
        "name": one_liner(item["name"]),
        "description": one_liner(item["description"]),
        "SKU": get_nums_from_string(item["catalog_number"]),
        "url": item["href"],
        "img_src": item["img_src"],
        "orig_price": 0,
        "disc_price": 0,
    }


def payngo_selector(results):
    if "items" not in results:
        raise InvalidAPIResponseError("Payngo API response missing 'items' key")
    if len(results["items"]) == 0:
        return {}

    item = results["items"][0]
    required_keys = ["l", "d", "sku", "u", "t2", "p_c", "p"]
    for key in required_keys:
        if key not in item:
            raise InvalidAPIResponseError(f"Payngo API response missing key: {key}")

    return {
        "name": one_liner(item["l"]),
        "description": one_liner(item["d"]),
        "SKU": item["sku"],
        "url": item["u"],
        "img_src": item["t2"],
        "orig_price": item["p_c"],
        "disc_price": item["p"],
    }


def shekem_selector(results):
    return payngo_selector(results)


def lastprice_selector(results):
    if "products" not in results:
        raise InvalidAPIResponseError("LastPrice API response missing 'products' key")
    if not isinstance(results, dict):
        raise InvalidAPIResponseError(f"LastPrice API returned {type(results)} instead of dict")
    
    if len(results["products"]) == 0:
        return {}
    

    item = results["products"][0]
    required_keys = ["title", "subtitle", "productId", "url", "image"]
    for key in required_keys:
        if key not in item:
            raise InvalidAPIResponseError(f"LastPrice API response missing key: {key}")

    return {
        "name": one_liner(item["title"]),
        "description": one_liner(item["subtitle"]),
        "SKU": item["productId"],
        "url": item["url"],
        "img_src": item["image"],
        "orig_price": 0,
        "disc_price": 0,
    }


def ksp_selector(results):
    if "result" not in results and "items" not in results["result"]:
        raise InvalidAPIResponseError("KSP API response missing 'result' key or 'result->items' key")
    if len(results["result"]["items"]) == 0:
        return {}

    item = results["result"]["items"][0]
    
    # required_keys = ["text", "id", "image"]
    # for key in required_keys:
    #     if key not in item:
    #         raise InvalidAPIResponseError(f"KSP API response missing key: {key}")

    return {
        "name": one_liner(item["name"]),
        "description": item["description"],
        "SKU": item["uin"],
        "url": f"https://ksp.co.il/web/item/{item['uin']}",
        "img_src": item["img"],
        "orig_price": item["price"],
        "disc_price": item["min_price"],
    }


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
