"""
Solution Cart

Manages the user's current solution/saved items.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import SolutionItem


class SolutionCart:
    """In-memory solution cart (per-instance, not singleton)"""

    def __init__(self):
        self._items: Dict[str, SolutionItem] = {}
    
    def add_item(self, sku: str, quantity: int = 1) -> SolutionItem:
        """Add item to solution"""
        if sku in self._items:
            self._items[sku].quantity += quantity
        else:
            self._items[sku] = SolutionItem(
                sku=sku,
                quantity=quantity,
                added_at=datetime.utcnow().isoformat(),
            )
        return self._items[sku]
    
    def remove_item(self, sku: str) -> bool:
        """Remove item from solution"""
        if sku in self._items:
            del self._items[sku]
            return True
        return False
    
    def update_quantity(self, sku: str, quantity: int) -> bool:
        """Update item quantity"""
        if sku in self._items:
            if quantity <= 0:
                del self._items[sku]
            else:
                self._items[sku].quantity = quantity
            return True
        return False
    
    def get_items(self) -> List[SolutionItem]:
        """Get all items in solution"""
        return list(self._items.values())
    
    def get_item(self, sku: str) -> Optional[SolutionItem]:
        """Get specific item"""
        return self._items.get(sku)
    
    def clear(self):
        """Clear all items"""
        self._items.clear()
    
    def is_empty(self) -> bool:
        """Check if solution is empty"""
        return len(self._items) == 0
    
    def get_count(self) -> int:
        """Get total item count"""
        return sum(item.quantity for item in self._items.values())
    
    def analyze_completeness(self) -> Dict[str, Any]:
        """Analyze solution completeness"""
        # This would be more sophisticated in production
        # For now, simple analysis based on categories present
        from .product_catalog import ProductCatalog
        
        catalog = ProductCatalog()
        categories = set()
        
        for item in self._items.values():
            product = catalog.get_by_sku(item.sku)
            if product:
                categories.add(product.category.value)
        
        # Ideal solution has: cooling, power, monitoring
        ideal_categories = {"cooling", "power", "monitoring"}
        present_categories = set(categories)
        
        missing = ideal_categories - present_categories
        has_all_ideal = len(missing) == 0
        
        completeness_score = len(present_categories) / len(ideal_categories)
        
        return {
            "total_items": self.get_count(),
            "unique_items": len(self._items),
            "categories_present": list(categories),
            "categories_missing": list(missing),
            "completeness_score": completeness_score,
            "is_complete": has_all_ideal,
            "suggestions": self._generate_suggestions(missing) if missing else [],
        }
    
    def _generate_suggestions(self, missing_categories: set) -> List[str]:
        """Generate suggestions for missing categories"""
        suggestions = []
        
        category_names = {
            "cooling": "a cooling system",
            "power": "power protection (UPS)",
            "monitoring": "infrastructure monitoring",
            "distribution": "power distribution",
        }
        
        for cat in missing_categories:
            name = category_names.get(cat, cat)
            suggestions.append(f"Consider adding {name}")
        
        return suggestions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "items": [item.to_dict() for item in self._items.values()],
            "total_items": self.get_count(),
            "unique_items": len(self._items),
        }
