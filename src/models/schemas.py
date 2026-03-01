"""
Pydantic models for B2B Commerce API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CategoryType(str, Enum):
    COOLING = "cooling"
    POWER = "power"
    MONITORING = "monitoring"
    DISTRIBUTION = "distribution"


class Category(BaseModel):
    id: str = Field(..., description="Category identifier")
    name: str = Field(..., description="Display name")
    type: CategoryType = Field(..., description="Category type")
    color: str = Field(..., description="UI color hex code")
    icon: str = Field(..., description="Icon emoji or identifier")
    description: str = Field(..., description="Category description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cooling",
                "name": "Cooling Solutions",
                "type": "cooling",
                "color": "#F472B6",
                "icon": "❄️",
                "description": "Advanced cooling systems for data centers"
            }
        }


class ProductSpecification(BaseModel):
    capacity: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[str] = None
    power_consumption: Optional[str] = None
    noise_level: Optional[str] = None
    warranty: Optional[str] = None
    certifications: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "capacity": "1000W",
                "dimensions": "600mm x 800mm x 2000mm",
                "weight": "150kg",
                "power_consumption": "2.5kW",
                "noise_level": "65dB",
                "warranty": "3 years",
                "certifications": ["ISO 9001", "Energy Star"]
            }
        }


class Product(BaseModel):
    code: str = Field(..., description="Unique SKU")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Category ID")
    category_name: Optional[str] = Field(None, description="Category display name")
    description: str = Field(..., description="Product description")
    short_description: Optional[str] = Field(None, description="Brief summary")
    specifications: ProductSpecification = Field(default_factory=ProductSpecification)
    price: float = Field(..., description="Unit price")
    currency: str = Field(default="USD", description="Currency code")
    image_url: Optional[str] = Field(None, description="Product image URL")
    in_stock: bool = Field(default=True, description="Availability")
    stock_level: int = Field(default=0, description="Available quantity")
    min_order_quantity: int = Field(default=1, description="Minimum order")
    complementary_products: List[str] = Field(default_factory=list, description="Related SKUs for bundling")
    featured: bool = Field(default=False, description="Featured product flag")
    rating: Optional[float] = Field(None, description="Product rating 0-5")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "CS-LC-1000",
                "name": "AeroCool Liquid C1000",
                "category": "cooling",
                "category_name": "Cooling Solutions",
                "description": "High-performance liquid cooling system designed for data centers up to 1000 sq ft. Features intelligent temperature control and redundant pumps.",
                "short_description": "Liquid cooling for 1000 sq ft data centers",
                "specifications": {
                    "capacity": "1000W",
                    "dimensions": "600mm x 800mm x 2000mm",
                    "weight": "150kg",
                    "power_consumption": "2.5kW",
                    "noise_level": "65dB",
                    "warranty": "3 years",
                    "certifications": ["ISO 9001", "Energy Star"]
                },
                "price": 4500.00,
                "currency": "USD",
                "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400",
                "in_stock": True,
                "stock_level": 50,
                "min_order_quantity": 1,
                "complementary_products": ["PW-UPS-3000", "MN-IC-PRO", "PD-RU-42"],
                "featured": True,
                "rating": 4.7
            }
        }


class StockInfo(BaseModel):
    product_code: str
    in_stock: bool
    stock_level: int
    warehouse: Optional[str] = None
    eta_days: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_code": "CS-LC-1000",
                "in_stock": True,
                "stock_level": 50,
                "warehouse": "CA-01",
                "eta_days": None
            }
        }


class SolutionItem(BaseModel):
    product_code: str
    product_name: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    category: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_code": "CS-LC-1000",
                "product_name": "AeroCool Liquid C1000",
                "quantity": 1,
                "unit_price": 4500.00,
                "total_price": 4500.00,
                "category": "cooling"
            }
        }


class Solution(BaseModel):
    id: str = Field(..., description="Solution identifier")
    items: List[SolutionItem] = Field(default_factory=list)
    total_price: float = Field(default=0.0)
    currency: str = Field(default="USD")
    category_coverage: List[str] = Field(default_factory=list, description="Categories represented")
    missing_categories: List[str] = Field(default_factory=list, description="Suggested missing categories")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "sol-001",
                "items": [
                    {
                        "product_code": "CS-LC-1000",
                        "product_name": "AeroCool Liquid C1000",
                        "quantity": 1,
                        "unit_price": 4500.00,
                        "total_price": 4500.00,
                        "category": "cooling"
                    }
                ],
                "total_price": 4500.00,
                "currency": "USD",
                "category_coverage": ["cooling"],
                "missing_categories": ["power", "monitoring"]
            }
        }


class Bundle(BaseModel):
    id: str
    name: str
    description: str
    products: List[str] = Field(..., description="Product SKUs in bundle")
    use_case: str = Field(..., description="Target scenario")
    space_requirement: Optional[str] = None
    total_price: float
    savings: float = Field(default=0.0, description="Bundle discount amount")
    savings_percent: float = Field(default=0.0, description="Bundle discount %")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "bundle-dc-small",
                "name": "Small Data Center Package",
                "description": "Complete infrastructure for 500-1000 sq ft data center",
                "products": ["CS-LC-1000", "PW-UPS-3000", "MN-IC-PRO"],
                "use_case": "Small data center (500-1000 sq ft)",
                "space_requirement": "500-1000 sq ft",
                "total_price": 12500.00,
                "savings": 1500.00,
                "savings_percent": 10.7
            }
        }


class SearchQuery(BaseModel):
    query: str = Field(..., description="Search terms")
    category: Optional[str] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock_only: bool = Field(default=False)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    products: List[Product]
    total: int
    page: int
    page_size: int
    query: str
    suggested_categories: List[str] = Field(default_factory=list)


class AIRecommendation(BaseModel):
    use_case: str = Field(..., description="Customer's scenario")
    recommended_products: List[Product]
    suggested_bundle: Optional[Bundle] = None
    missing_categories: List[str] = Field(default_factory=list)
    explanation: str = Field(..., description="Why these recommendations")
