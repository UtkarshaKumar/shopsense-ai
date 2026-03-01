"""
Mock B2B Commerce API
FastAPI-based mock server implementing OCC-like REST endpoints
"""
import json
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import schemas
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schemas import (
    Product, Category, StockInfo, Bundle, SearchResult, 
    Solution, SolutionItem, CategoryType
)

app = FastAPI(
    title="B2B Commerce API",
    description="Mock API for AI Commerce Companion",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load mock data
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(data_dir, "products.json")) as f:
    products_data = json.load(f)["products"]
    PRODUCTS = {p["code"]: p for p in products_data}

with open(os.path.join(data_dir, "categories.json")) as f:
    categories_data = json.load(f)["categories"]
    CATEGORIES = {c["id"]: c for c in categories_data}

with open(os.path.join(data_dir, "bundles.json")) as f:
    bundles_data = json.load(f)["bundles"]
    BUNDLES = {b["id"]: b for b in bundles_data}

# In-memory solution (cart)
SOLUTION = {
    "id": "solution-current",
    "items": [],
    "total_price": 0.0,
    "currency": "USD",
    "category_coverage": [],
    "missing_categories": []
}


@app.get("/")
async def root():
    return {
        "message": "B2B Commerce API",
        "version": "1.0.0",
        "endpoints": {
            "products": "/api/v1/products",
            "categories": "/api/v1/categories",
            "search": "/api/v1/products/search",
            "stock": "/api/v1/stock/{productCode}",
            "bundles": "/api/v1/bundles",
            "solution": "/api/v1/solution"
        }
    }


@app.get("/api/v1/categories", response_model=List[Category])
async def get_categories():
    """Get all product categories"""
    return list(CATEGORIES.values())


@app.get("/api/v1/categories/{category_id}")
async def get_category(category_id: str):
    """Get category details"""
    if category_id not in CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found")
    return CATEGORIES[category_id]


@app.get("/api/v1/categories/{category_id}/products", response_model=List[Product])
async def get_products_by_category(
    category_id: str,
    in_stock_only: bool = Query(False, description="Filter to in-stock only")
):
    """Get products in a category"""
    if category_id not in CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found")
    
    products = [
        p for p in PRODUCTS.values() 
        if p["category"] == category_id
    ]
    
    if in_stock_only:
        products = [p for p in products if p["in_stock"]]
    
    return products


@app.get("/api/v1/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    featured: bool = Query(False, description="Featured products only"),
    in_stock_only: bool = Query(False, description="In-stock only")
):
    """Get all products with optional filters"""
    products = list(PRODUCTS.values())
    
    if category:
        products = [p for p in products if p["category"] == category]
    
    if featured:
        products = [p for p in products if p.get("featured", False)]
    
    if in_stock_only:
        products = [p for p in products if p["in_stock"]]
    
    return products


@app.get("/api/v1/products/{product_code}")
async def get_product(product_code: str):
    """Get product details"""
    if product_code not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = PRODUCTS[product_code].copy()
    # Enrich with category name
    if product["category"] in CATEGORIES:
        product["category_name"] = CATEGORIES[product["category"]]["name"]
    
    return product


@app.get("/api/v1/products/search", response_model=SearchResult)
async def search_products(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search products by name, description, or specifications"""
    query = q.lower()
    results = []
    
    for product in PRODUCTS.values():
        # Check if query matches various fields
        matches = (
            query in product["name"].lower() or
            query in product["description"].lower() or
            query in product.get("short_description", "").lower() or
            query in product["category"].lower() or
            any(query in str(v).lower() for v in product.get("specifications", {}).values())
        )
        
        if matches:
            if category is None or product["category"] == category:
                results.append(product)
    
    # Determine suggested categories based on results
    found_categories = list(set(r["category"] for r in results))
    suggested = [c for c in found_categories if c != category] if category else []
    
    return {
        "products": results[:limit],
        "total": len(results),
        "page": 1,
        "page_size": limit,
        "query": q,
        "suggested_categories": suggested
    }


@app.get("/api/v1/stock/{product_code}")
async def get_stock(product_code: str, warehouse: Optional[str] = Query(None)):
    """Get stock information for a product"""
    if product_code not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = PRODUCTS[product_code]
    
    return {
        "product_code": product_code,
        "in_stock": product["in_stock"],
        "stock_level": product["stock_level"],
        "warehouse": warehouse or "CA-01",
        "eta_days": None if product["in_stock"] else 14
    }


@app.get("/api/v1/products/{product_code}/complementary", response_model=List[Product])
async def get_complementary_products(product_code: str):
    """Get complementary products for bundling"""
    if product_code not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = PRODUCTS[product_code]
    complementary_codes = product.get("complementary_products", [])
    
    return [PRODUCTS[code] for code in complementary_codes if code in PRODUCTS]


@app.get("/api/v1/bundles", response_model=List[Bundle])
async def get_bundles(
    space_requirement: Optional[str] = Query(None, description="Filter by space (e.g., '1000 sq ft')")
):
    """Get all product bundles"""
    bundles = list(BUNDLES.values())
    
    if space_requirement:
        # Simple matching logic
        bundles = [
            b for b in bundles 
            if space_requirement.lower() in b.get("space_requirement", "").lower()
        ]
    
    return bundles


@app.get("/api/v1/bundles/{bundle_id}")
async def get_bundle(bundle_id: str):
    """Get bundle details with full product info"""
    if bundle_id not in BUNDLES:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    bundle = BUNDLES[bundle_id].copy()
    
    # Enrich with full product details
    bundle["products_detail"] = [
        PRODUCTS[code] for code in bundle["products"] if code in PRODUCTS
    ]
    
    return bundle


@app.get("/api/v1/solution")
async def get_solution():
    """Get current solution (cart)"""
    return SOLUTION


class AddToSolutionRequest(BaseModel):
    product_code: str
    quantity: int = 1


@app.post("/api/v1/solution/items")
async def add_to_solution(request: AddToSolutionRequest):
    """Add product to solution"""
    if request.product_code not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = PRODUCTS[request.product_code]
    
    # Check if already in solution
    existing = next(
        (item for item in SOLUTION["items"] if item["product_code"] == request.product_code),
        None
    )
    
    if existing:
        existing["quantity"] += request.quantity
        existing["total_price"] = existing["quantity"] * product["price"]
    else:
        SOLUTION["items"].append({
            "product_code": request.product_code,
            "product_name": product["name"],
            "quantity": request.quantity,
            "unit_price": product["price"],
            "total_price": request.quantity * product["price"],
            "category": product["category"]
        })
    
    # Recalculate totals
    SOLUTION["total_price"] = sum(item["total_price"] for item in SOLUTION["items"])
    SOLUTION["category_coverage"] = list(set(item["category"] for item in SOLUTION["items"]))
    
    # Determine missing categories
    all_categories = set(CATEGORIES.keys())
    covered = set(SOLUTION["category_coverage"])
    SOLUTION["missing_categories"] = list(all_categories - covered)
    
    return SOLUTION


@app.delete("/api/v1/solution/items/{product_code}")
async def remove_from_solution(product_code: str):
    """Remove product from solution"""
    SOLUTION["items"] = [item for item in SOLUTION["items"] if item["product_code"] != product_code]
    
    # Recalculate
    SOLUTION["total_price"] = sum(item["total_price"] for item in SOLUTION["items"])
    SOLUTION["category_coverage"] = list(set(item["category"] for item in SOLUTION["items"]))
    
    all_categories = set(CATEGORIES.keys())
    covered = set(SOLUTION["category_coverage"])
    SOLUTION["missing_categories"] = list(all_categories - covered)
    
    return SOLUTION


@app.post("/api/v1/solution/clear")
async def clear_solution():
    """Clear solution (empty cart)"""
    SOLUTION["items"] = []
    SOLUTION["total_price"] = 0.0
    SOLUTION["category_coverage"] = []
    SOLUTION["missing_categories"] = list(CATEGORIES.keys())
    
    return SOLUTION


@app.get("/api/v1/ai/recommend")
async def get_ai_recommendations(
    use_case: str = Query(..., description="Customer use case description"),
    space_size: Optional[int] = Query(None, description="Space size in sq ft")
):
    """Get AI-powered product recommendations based on use case"""
    # Simple recommendation logic based on keywords
    use_case_lower = use_case.lower()
    
    recommendations = []
    bundle = None
    
    # Determine relevant products based on keywords
    if any(word in use_case_lower for word in ["cool", "thermal", "heat", "temperature"]):
        recommendations.extend([
            PRODUCTS["CS-LC-1000"],
            PRODUCTS["CS-CR-2000"],
            PRODUCTS["MN-TEMP-ADV"]
        ])
    
    if any(word in use_case_lower for word in ["power", "ups", "backup", "electric"]):
        recommendations.extend([
            PRODUCTS["PW-UPS-3000"],
            PRODUCTS["PW-UPS-6000"],
            PRODUCTS["PD-RU-42"]
        ])
    
    if any(word in use_case_lower for word in ["monitor", "sensor", "track", "alert"]):
        recommendations.extend([
            PRODUCTS["MN-IC-PRO"],
            PRODUCTS["MN-TEMP-ADV"]
        ])
    
    if any(word in use_case_lower for word in ["edge", "small", "remote"]):
        recommendations.extend([
            PRODUCTS["CS-AC-500"],
            PRODUCTS["PW-UPS-1500"],
            PRODUCTS["PD-SMART-8"]
        ])
        bundle = BUNDLES.get("bundle-edge-small")
    
    # Default bundle based on space size
    if space_size:
        if space_size <= 500:
            bundle = BUNDLES.get("bundle-edge-small")
        elif space_size <= 1000:
            bundle = BUNDLES.get("bundle-dc-small")
        elif space_size <= 2000:
            bundle = BUNDLES.get("bundle-dc-medium")
        else:
            bundle = BUNDLES.get("bundle-dc-enterprise")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for p in recommendations:
        if p["code"] not in seen:
            seen.add(p["code"])
            unique_recommendations.append(p)
    
    # Determine missing categories
    recommended_categories = set(p["category"] for p in unique_recommendations)
    all_categories = set(CATEGORIES.keys())
    missing = list(all_categories - recommended_categories)
    
    return {
        "use_case": use_case,
        "recommended_products": unique_recommendations[:6],
        "suggested_bundle": bundle,
        "missing_categories": missing,
        "explanation": f"Based on your need for '{use_case}', we recommend products that provide optimal performance and reliability."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
