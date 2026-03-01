"""
Data Models for ShopSense AI Commerce Agent
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ProductCategory(Enum):
    """Product categories"""
    CAMERAS = "cameras"
    VIDEO = "video"
    ACCESSORIES = "accessories"
    FILMS = "films"


@dataclass
class Product:
    """Product model"""
    sku: str
    name: str
    category: ProductCategory
    description: str
    specifications: Dict[str, Any] = field(default_factory=dict)
    compatible_skus: List[str] = field(default_factory=list)
    complementary_skus: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    price: Optional[float] = None
    in_stock: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "specifications": self.specifications,
            "compatible_skus": self.compatible_skus,
            "complementary_skus": self.complementary_skus,
            "tags": self.tags,
            "price": self.price,
            "in_stock": self.in_stock,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Product":
        # Handle both 'sku' and 'code' field names
        sku = data.get("sku") or data.get("code", "")
        
        # Handle complementary_products vs complementary_skus
        complementary = data.get("complementary_skus", [])
        if not complementary and "complementary_products" in data:
            complementary = data["complementary_products"]
        
        return cls(
            sku=sku,
            name=data.get("name", ""),
            category=ProductCategory(data.get("category", "cameras")),
            description=data.get("description", data.get("short_description", "")),
            specifications=data.get("specifications", {}),
            compatible_skus=data.get("compatible_skus", []),
            complementary_skus=complementary,
            tags=data.get("tags", []),
            price=data.get("price"),
            in_stock=data.get("in_stock", True),
        )


@dataclass
class SolutionItem:
    """Item in a solution"""
    sku: str
    quantity: int = 1
    added_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "sku": self.sku,
            "quantity": self.quantity,
            "added_at": self.added_at,
        }


@dataclass
class Category:
    """Category model"""
    id: str
    name: str
    description: str
    color: str
    icon: str
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Category":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            color=data.get("color", "#6366F1"),
            icon=data.get("icon", "box"),
        )


@dataclass
class Bundle:
    """Bundle model"""
    id: str
    name: str
    description: str
    category: str
    items: List[Dict[str, Any]]
    savings_percent: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "items": self.items,
            "savings_percent": self.savings_percent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Bundle":
        # Handle both 'id' and 'bundle_id'
        bundle_id = data.get("id") or data.get("bundle_id", "")
        
        # Handle 'items' vs 'products'
        items = data.get("items", [])
        if not items and "products" in data:
            items = [{"sku": p, "quantity": 1} for p in data["products"]]
        
        return cls(
            id=bundle_id,
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            items=items,
            savings_percent=data.get("savings_percent", data.get("savings_percent", 0)),
        )
