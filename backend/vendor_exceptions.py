class VendorScraperException(Exception):
    """Base exception for vendor scraper"""
    pass

class MissingFieldException(VendorScraperException):
    """Raised when a required field is missing due to an invalid configuiration"""

class SearchFailedException(VendorScraperException):
    """Raised when search endpoint fails"""
    pass


class ProductFetchException(VendorScraperException):
    """Raised when fetching product data fails"""
    pass


class ParseException(VendorScraperException):
    """Raised when parsing data fails"""
    pass


class NormalizationException(VendorScraperException):
    """Raised when normalizing product data fails"""
    pass


class NoProductsFoundException(VendorScraperException):
    """Raised when no products are found in search results"""
    pass