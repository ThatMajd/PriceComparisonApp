from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

class FetchMethod(Enum):
    """Method to fetch product data"""
    API = "api"
    HTML_JSON_LD = "html_json_ld"


class RequestMethod(Enum):
    """HTTP request methods"""
    GET = "GET"
    POST = "POST"


@dataclass
class ProductSchema:
    """Normalized product schema"""
    SKU: str
    name: str
    offers__price:int
    orig_price: int
    disc_price: int
    currency: str
    url: str
    images: List[str] = field(default_factory=list)
    description: Optional[str] = None
    availability: Optional[str] = None
    item_condition: Optional[str] = None
    brand: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SearchResultProduct:
    name: str = None
    description: Optional[str] = None
    SKU: Optional[str] = None
    url: str = None
    img_src: Optional[str] = None
    orig_price: Optional[int] = None
    disc_price: Optional[int] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VendorConfig:
    """Configuration for vendor endpoints"""
    name: str
    autocomplete_endpoint: str
    headers: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    cookies: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    search_param: Optional[str] = None
    fetch_method: FetchMethod = FetchMethod.HTML_JSON_LD
    product_data_endpoint: Optional[str] = None
