"""
API Tests for Mock Commerce API
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.mock_api import app

client = TestClient(app)


class TestCategories:
    def test_get_categories(self):
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        
        # Check category structure
        categories = [c["id"] for c in data]
        assert "cooling" in categories
        assert "power" in categories
        assert "monitoring" in categories
        assert "distribution" in categories
    
    def test_get_category_detail(self):
        response = client.get("/api/v1/categories/cooling")
        assert response.status_code == 200
        assert response.json()["id"] == "cooling"
        assert response.json()["name"] == "Cooling Solutions"
    
    def test_get_category_not_found(self):
        response = client.get("/api/v1/categories/nonexistent")
        assert response.status_code == 404


class TestProducts:
    def test_get_all_products(self):
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 16  # We have 16 products
    
    def test_get_product_by_code(self):
        response = client.get("/api/v1/products/CS-LC-1000")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "CS-LC-1000"
        assert data["name"] == "AeroCool Liquid C1000"
        assert data["category"] == "cooling"
        assert data["price"] == 4500.00
    
    def test_get_product_not_found(self):
        response = client.get("/api/v1/products/NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_products_by_category(self):
        response = client.get("/api/v1/categories/cooling/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # 4 cooling products
        for p in data:
            assert p["category"] == "cooling"
    
    def test_get_products_in_stock_only(self):
        response = client.get("/api/v1/products?in_stock_only=true")
        assert response.status_code == 200
        data = response.json()
        for p in data:
            assert p["in_stock"] is True


class TestSearch:
    def test_search_products(self):
        response = client.get("/api/v1/products/search?q=liquid+cooling")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "liquid cooling"
        assert len(data["products"]) > 0
        
        # Check AeroCool is in results
        codes = [p["code"] for p in data["products"]]
        assert "CS-LC-1000" in codes
    
    def test_search_by_category(self):
        response = client.get("/api/v1/products/search?q=ups&category=power")
        assert response.status_code == 200
        data = response.json()
        for p in data["products"]:
            assert p["category"] == "power"
    
    def test_search_no_results(self):
        response = client.get("/api/v1/products/search?q=xyznonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 0


class TestStock:
    def test_get_stock(self):
        response = client.get("/api/v1/stock/CS-LC-1000")
        assert response.status_code == 200
        data = response.json()
        assert data["product_code"] == "CS-LC-1000"
        assert data["in_stock"] is True
        assert data["stock_level"] == 50
    
    def test_get_stock_not_found(self):
        response = client.get("/api/v1/stock/NONEXISTENT")
        assert response.status_code == 404


class TestBundles:
    def test_get_all_bundles(self):
        response = client.get("/api/v1/bundles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6  # We have 6 bundles
    
    def test_get_bundle_detail(self):
        response = client.get("/api/v1/bundles/bundle-dc-small")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "bundle-dc-small"
        assert data["name"] == "Small Data Center Package"
        assert "products_detail" in data
    
    def test_get_bundle_by_space(self):
        response = client.get("/api/v1/bundles?space_requirement=1000")
        assert response.status_code == 200
        data = response.json()
        # Should return bundles matching 1000 sq ft
        assert len(data) > 0


class TestSolution:
    def test_get_solution_empty(self):
        # Clear solution first
        client.post("/api/v1/solution/clear")
        
        response = client.get("/api/v1/solution")
        assert response.status_code == 200
        data = response.json()
        assert data["total_price"] == 0.0
        assert len(data["items"]) == 0
    
    def test_add_to_solution(self):
        # Clear first
        client.post("/api/v1/solution/clear")
        
        response = client.post(
            "/api/v1/solution/items",
            json={"product_code": "CS-LC-1000", "quantity": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_code"] == "CS-LC-1000"
        assert data["category_coverage"] == ["cooling"]
    
    def test_remove_from_solution(self):
        # Add then remove
        client.post("/api/v1/solution/clear")
        client.post(
            "/api/v1/solution/items",
            json={"product_code": "CS-LC-1000", "quantity": 1}
        )
        
        response = client.delete("/api/v1/solution/items/CS-LC-1000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0


class TestAIRecommendations:
    def test_recommend_by_use_case(self):
        response = client.get("/api/v1/ai/recommend?use_case=cooling+for+data+center")
        assert response.status_code == 200
        data = response.json()
        assert "recommended_products" in data
        assert "explanation" in data
        # Should recommend cooling products
        categories = set(p["category"] for p in data["recommended_products"])
        assert "cooling" in categories
    
    def test_recommend_by_space(self):
        response = client.get("/api/v1/ai/recommend?use_case=data+center&space_size=1000")
        assert response.status_code == 200
        data = response.json()
        assert data["suggested_bundle"] is not None
        assert "1000" in data["suggested_bundle"]["space_requirement"]


class TestComplementary:
    def test_get_complementary(self):
        response = client.get("/api/v1/products/CS-LC-1000/complementary")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # Should include UPS and monitoring
        codes = [p["code"] for p in data]
        assert "PW-UPS-3000" in codes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
