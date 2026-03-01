"""
Tools - Actions the agent can perform

Defines all available tools and their execution logic.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

from src.data.product_catalog import ProductCatalog
from src.data.solution_cart import SolutionCart
from src.data.models import Product, ProductCategory


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    data: Any
    message: str = ""
    error: Optional[str] = None


class Tool(ABC):
    """Abstract base class for tools"""
    
    name: str = ""
    description: str = ""
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters"""
        pass


class SearchProductsTool(Tool):
    """Search for products in catalog"""
    
    name = "search_products"
    description = "Search for products by query, category, or specifications"
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
    
    # Keywords that map to product categories for smarter matching
    _CATEGORY_KEYWORDS: Dict[str, str] = {
        # Cameras
        "camera": "cameras", "dslr": "cameras", "mirrorless": "cameras",
        "compact cam": "cameras", "point and shoot": "cameras", "slr": "cameras",
        "canon eos": "cameras", "nikon d": "cameras", "fujifilm finepix": "cameras",
        "canon ixus": "cameras", "cyber-shot": "cameras", "cybershot": "cameras",
        "shoot": "cameras", "photograph": "cameras",
        # Video
        "video": "video", "camcorder": "video", "record": "video",
        "handycam": "video", "legria": "video", "hd cam": "video",
        "full hd": "video", "1080p": "video", "4k": "video",
        # Accessories
        "bag": "accessories", "camera bag": "accessories", "lens": "accessories",
        "tripod": "accessories", "sd card": "accessories", "memory card": "accessories",
        "gorilla": "accessories", "prime lens": "accessories", "ef lens": "accessories",
        "sdhc": "accessories", "storage": "accessories",
        # Films
        "film": "films", "colour film": "films", "color film": "films",
        "kodak": "films", "fuji film": "films", "superia": "films",
        "iso 400": "films", "iso 200": "films", "35mm": "films", "analogue": "films",
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        query = params.get("query", "")
        category = params.get("category")

        try:
            # Detect implied category from query keywords when not explicit
            if not category and query:
                for kw, cat in self._CATEGORY_KEYWORDS.items():
                    if kw in query.lower():
                        category = cat
                        break

            if category:
                try:
                    cat = ProductCategory(category) if isinstance(category, str) else category
                    results = self.catalog.get_by_category(cat)
                except ValueError:
                    results = self.catalog.get_all()
            else:
                results = self.catalog.get_all()

            # Keyword-level matching (tokenize the query, not full-string)
            if query:
                stop_words = {
                    "i", "need", "want", "a", "an", "the", "for", "my", "is",
                    "are", "to", "of", "in", "and", "or", "with", "that", "can",
                    "do", "show", "me", "get", "find", "what", "best", "under",
                    "good", "cheap", "nice", "top",
                }
                keywords = [
                    w.strip(".,?!") for w in query.lower().split()
                    if len(w.strip(".,?!")) > 2 and w.strip(".,?!") not in stop_words
                ]
                if keywords:
                    def matches(p) -> bool:
                        text = (p.name + " " + p.description + " " + " ".join(p.tags)).lower()
                        return any(kw in text for kw in keywords)
                    filtered = [p for p in results if matches(p)]
                    # Only apply keyword filter if it actually narrows results
                    if filtered:
                        results = filtered

            return ToolResult(
                success=True,
                data=results,
                message=f"Found {len(results)} products"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=str(e)
            )


class GetProductDetailsTool(Tool):
    """Get detailed product information"""
    
    name = "get_product_details"
    description = "Get detailed information about a specific product"
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        # Handle different parameter names
        identifier = params.get("identifier", params.get("product_code", params.get("sku", "")))
        
        try:
            # Try to find by SKU first
            product = self.catalog.get_by_sku(identifier)
            
            if not product:
                # Try to find by name (partial match)
                all_products = self.catalog.get_all()
                identifier_lower = identifier.lower()
                for p in all_products:
                    if identifier_lower in p.name.lower():
                        product = p
                        break
            
            if not product:
                # Token-level fuzzy match: all search tokens must appear in name
                tokens = [
                    t for t in identifier_lower.split()
                    if len(t) > 1 and t not in {"the", "a", "an", "and", "or"}
                ]
                for p in all_products:
                    name_lower = p.name.lower()
                    if tokens and all(t in name_lower for t in tokens):
                        product = p
                        break

            if not product:
                # Partial token match: any token matches SKU or name
                for p in all_products:
                    combined = (p.sku + " " + p.name).lower()
                    if any(t in combined for t in tokens):
                        product = p
                        break

            if product:
                return ToolResult(
                    success=True,
                    data=product,
                    message=f"Found product: {product.name}"
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Product not found: {identifier}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class CheckStockTool(Tool):
    """Check product availability"""
    
    name = "check_stock"
    description = "Check if products are in stock"
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        skus = params.get("skus", [])
        
        try:
            if skus:
                results = {
                    sku: self.catalog.check_availability(sku)
                    for sku in skus
                }
            else:
                # Check all products
                all_products = self.catalog.get_all()
                results = {
                    p.sku: self.catalog.check_availability(p.sku)
                    for p in all_products
                }
            
            return ToolResult(
                success=True,
                data=results,
                message=f"Stock status checked for {len(results)} products"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )


class GetComplementaryTool(Tool):
    """Get complementary products"""
    
    name = "get_complementary"
    description = "Get products that complement a given product"
    
    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        # Try different parameter names
        sku = params.get("sku", params.get("product_code", params.get("for_top_product", None)))
        
        try:
            if sku and sku is not True:  # Handle for_top_product=True case
                products = self.catalog.get_complementary(sku)
            else:
                # Return all complementary pairs
                all_products = self.catalog.get_all()
                products = []
                for p in all_products:
                    if p.complementary_skus:
                        products.extend([
                            self.catalog.get_by_sku(s)
                            for s in p.complementary_skus
                        ])
                products = [p for p in products if p]
            
            return ToolResult(
                success=True,
                data=products,
                message=f"Found {len(products)} complementary products"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=str(e)
            )


class GetSolutionTool(Tool):
    """Get current solution"""
    
    name = "get_solution"
    description = "Get the current solution/saved products"
    
    def __init__(self, solution: SolutionCart):
        self.solution = solution
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            items = self.solution.get_items()
            return ToolResult(
                success=True,
                data=items,
                message=f"Solution contains {len(items)} items"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=str(e)
            )


class AddToSolutionTool(Tool):
    """Add product to solution"""
    
    name = "add_solution_item"
    description = "Add a product to the current solution"
    
    def __init__(self, solution: SolutionCart):
        self.solution = solution
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        sku = params.get("product_code")
        quantity = params.get("quantity", 1)
        
        try:
            self.solution.add_item(sku, quantity)
            return ToolResult(
                success=True,
                data={"sku": sku, "quantity": quantity},
                message=f"Added {sku} to solution"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class RemoveFromSolutionTool(Tool):
    """Remove product from solution"""
    
    name = "remove_solution_item"
    description = "Remove a product from the current solution"
    
    def __init__(self, solution: SolutionCart):
        self.solution = solution
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        sku = params.get("product_code")
        
        try:
            self.solution.remove_item(sku)
            return ToolResult(
                success=True,
                data={"sku": sku},
                message=f"Removed {sku} from solution"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class ClearSolutionTool(Tool):
    """Clear solution"""
    
    name = "clear_solution"
    description = "Clear all items from solution"
    
    def __init__(self, solution: SolutionCart):
        self.solution = solution
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            self.solution.clear()
            return ToolResult(
                success=True,
                data={},
                message="Solution cleared"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class CheckSolutionCompletenessTool(Tool):
    """Check if solution is complete"""
    
    name = "check_solution_completeness"
    description = "Check if the current solution has all required components"
    
    def __init__(self, solution: SolutionCart):
        self.solution = solution
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            analysis = self.solution.analyze_completeness()
            return ToolResult(
                success=True,
                data=analysis,
                message=f"Solution completeness: {analysis['completeness_score']:.0%}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )


class GetCategoryProductsTool(Tool):
    """Get products by category"""

    name = "get_category_products"
    description = "Get all products in a given category"

    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        category = params.get("category")
        try:
            if category:
                try:
                    cat = ProductCategory(category) if isinstance(category, str) else category
                    results = self.catalog.get_by_category(cat)
                except ValueError:
                    results = self.catalog.get_all()
            else:
                results = self.catalog.get_all()
            return ToolResult(success=True, data=results, message=f"Found {len(results)} products")
        except Exception as e:
            return ToolResult(success=False, data=[], error=str(e))


class FilterProductsTool(Tool):
    """Filter products (no-op passthrough — filtering done in search)"""

    name = "filter_products"
    description = "Filter products by constraints"

    def __init__(self, catalog: ProductCatalog):
        self.catalog = catalog

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        results = self.catalog.get_all()
        return ToolResult(success=True, data=results, message=f"Returned {len(results)} products")


class AnalyzeQueryTool(Tool):
    """Analyse the user query (no-op stub)"""

    name = "analyze_query"
    description = "Analyse and understand a user query"

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, data={"query": params.get("query", "")}, message="Query analysed")


class ToolRegistry:
    """Registry of all available tools"""

    def __init__(self, catalog: ProductCatalog, solution: SolutionCart):
        self.catalog = catalog
        self.solution = solution
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools"""
        tools = [
            SearchProductsTool(self.catalog),
            GetProductDetailsTool(self.catalog),
            CheckStockTool(self.catalog),
            GetComplementaryTool(self.catalog),
            GetSolutionTool(self.solution),
            AddToSolutionTool(self.solution),
            RemoveFromSolutionTool(self.solution),
            ClearSolutionTool(self.solution),
            CheckSolutionCompletenessTool(self.solution),
            GetCategoryProductsTool(self.catalog),
            FilterProductsTool(self.catalog),
            AnalyzeQueryTool(),
        ]
        
        for tool in tools:
            self.register(tool)
    
    def register(self, tool: Tool):
        """Register a tool"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names"""
        return list(self._tools.keys())
    
    def execute(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get(name)
        if tool:
            return tool.execute(params)
        else:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool not found: {name}"
            )
