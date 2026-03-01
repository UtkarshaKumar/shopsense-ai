"""
Product Catalog — ShopSense AI

Consumer electronics catalog: cameras, video, accessories, films.
Based on SAP Spartacus OOTB electronics sample data.
"""
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import Product, ProductCategory, Category, Bundle


class ProductCatalog:
    """In-memory product catalog"""
    
    _instance = None
    
    def __new__(cls):
        # Singleton pattern — reset on each import so new product data is picked up
        cls._instance = None
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._products: Dict[str, Product] = {}
        self._categories: Dict[str, Category] = {}
        self._bundles: Dict[str, Bundle] = {}
        self._initialized = True
        
        self._load_data()
    
    def _load_data(self):
        """Load product data from JSON files"""
        data_dir = Path(__file__).parent
        
        # Load products
        try:
            with open(data_dir / "products.json") as f:
                products_data = json.load(f)
                for p in products_data.get("products", []):
                    product = Product.from_dict(p)
                    self._products[product.sku] = product
        except FileNotFoundError:
            # Create sample data if file doesn't exist
            self._create_sample_data()
        
        # Load categories
        try:
            with open(data_dir / "categories.json") as f:
                cats_data = json.load(f)
                for c in cats_data.get("categories", []):
                    cat = Category.from_dict(c)
                    self._categories[cat.id] = cat
        except FileNotFoundError:
            pass
        
        # Load bundles
        try:
            with open(data_dir / "bundles.json") as f:
                bundles_data = json.load(f)
                for b in bundles_data.get("bundles", []):
                    bundle = Bundle.from_dict(b)
                    self._bundles[bundle.id] = bundle
        except FileNotFoundError:
            pass
    
    def _create_sample_data(self):
        """Create SAP Spartacus OOTB electronics sample products."""
        sample_products = [
            # ── Cameras ───────────────────────────────────────────────────────
            Product(
                sku="CANON-EOS450D",
                name="Canon EOS 450D",
                category=ProductCategory.CAMERAS,
                description="Entry-level DSLR with a 12.2MP APS-C CMOS sensor, built-in image stabilisation, and Live View. Perfect for enthusiast photographers stepping up from compact cameras.",
                specifications={"resolution_mp": 12.2, "sensor": "APS-C CMOS", "optical_zoom": "3×", "max_iso": 1600, "battery_life_shots": 500, "weight_g": 475, "format": "DSLR"},
                compatible_skus=["CANON-EF50"],
                complementary_skus=["CANON-EF50", "LP-NOVA160", "KG-16GBSD"],
                tags=["camera", "dslr", "canon", "eos", "mirrorless", "photo", "shoot"],
                price=449.99,
                in_stock=True,
            ),
            Product(
                sku="NIKON-D40",
                name="Nikon D40",
                category=ProductCategory.CAMERAS,
                description="Lightweight 6.1MP DSLR with Nikon's DX-format CCD sensor, Guide Mode for beginners, and bundled 18-55mm kit lens. One of Nikon's most accessible DSLRs.",
                specifications={"resolution_mp": 6.1, "sensor": "APS-C CCD", "optical_zoom": "kit lens", "max_iso": 1600, "battery_life_shots": 470, "weight_g": 467, "format": "DSLR"},
                compatible_skus=[],
                complementary_skus=["LP-NOVA160", "KG-16GBSD"],
                tags=["camera", "dslr", "nikon", "d40", "beginner", "photo", "shoot"],
                price=319.99,
                in_stock=True,
            ),
            Product(
                sku="SONY-DSCW55",
                name="Sony Cyber-shot DSC-W55",
                category=ProductCategory.CAMERAS,
                description="Slim 7.2MP point-and-shoot with Carl Zeiss 3× optical zoom, 2.5\" LCD, and Sony's SteadyShot image stabilisation. Ideal for everyday compact photography.",
                specifications={"resolution_mp": 7.2, "sensor": "1/2.5\" CCD", "optical_zoom": "3×", "max_iso": 1000, "battery_life_shots": 260, "weight_g": 120, "format": "Compact"},
                compatible_skus=[],
                complementary_skus=["LP-NOVA160", "KG-16GBSD"],
                tags=["camera", "compact", "sony", "cybershot", "point and shoot", "photo"],
                price=159.99,
                in_stock=True,
            ),
            Product(
                sku="CANON-IXUS780",
                name="Canon IXUS 780 IS",
                category=ProductCategory.CAMERAS,
                description="Ultra-slim 8MP compact with optical Image Stabiliser, 3× optical zoom, and 2.5\" LCD. Canon's iconic IXUS design in titanium finish — pocketable everyday camera.",
                specifications={"resolution_mp": 8, "sensor": "1/2.5\" CCD", "optical_zoom": "3×", "max_iso": 1600, "battery_life_shots": 240, "weight_g": 105, "format": "Compact"},
                compatible_skus=[],
                complementary_skus=["LP-NOVA160", "KG-16GBSD", "KODAK-MAX400"],
                tags=["camera", "compact", "canon", "ixus", "slim", "pocket", "photo"],
                price=199.99,
                in_stock=False,
            ),
            Product(
                sku="FUJI-A850",
                name="Fujifilm FinePix A850",
                category=ProductCategory.CAMERAS,
                description="8.1MP compact powered by standard AA batteries — no proprietary charger needed. 3× optical zoom, 2.5\" LCD, and Fujifilm's natural colour processing.",
                specifications={"resolution_mp": 8.1, "sensor": "1/2.5\" CCD", "optical_zoom": "3×", "max_iso": 800, "battery_life_shots": 200, "weight_g": 130, "format": "Compact"},
                compatible_skus=[],
                complementary_skus=["LP-NOVA160", "KG-16GBSD", "FUJI-SUP200"],
                tags=["camera", "compact", "fuji", "fujifilm", "finepix", "aa battery", "photo"],
                price=119.99,
                in_stock=True,
            ),
            # ── Video / Camcorders ────────────────────────────────────────────
            Product(
                sku="SONY-DCRSR55",
                name="Sony Handycam DCR-SR55",
                category=ProductCategory.VIDEO,
                description="40GB hard-disk camcorder with 40× optical zoom, 2.7\" Clear LCD, and Carl Zeiss lens. Store up to 37 hours of standard-definition video without a single tape or disc.",
                specifications={"resolution": "SD (720×576)", "sensor_size": "1/6\"", "optical_zoom": "40×", "max_fps": 25, "battery_life_min": 115, "storage_type": "40GB HDD"},
                compatible_skus=[],
                complementary_skus=["LP-NOVA160", "KG-16GBSD"],
                tags=["video", "camcorder", "sony", "handycam", "record", "hdd"],
                price=249.99,
                in_stock=True,
            ),
            Product(
                sku="CANON-HFRE",
                name="Canon Legria HF R38",
                category=ProductCategory.VIDEO,
                description="Full HD 1080p AVCHD camcorder with SuperRange 32× optical zoom, Intelligent IS image stabilisation, and built-in 8GB flash memory. Sharp, lightweight and conference-ready.",
                specifications={"resolution": "Full HD 1080p", "sensor_size": "1/4.85\"", "optical_zoom": "32×", "max_fps": 50, "battery_life_min": 155, "storage_type": "8GB flash + SDXC"},
                compatible_skus=[],
                complementary_skus=["LP-NOVA160", "KG-16GBSD"],
                tags=["video", "camcorder", "canon", "legria", "hd", "fullhd", "1080p", "record"],
                price=399.99,
                in_stock=True,
            ),
            # ── Accessories ───────────────────────────────────────────────────
            Product(
                sku="LP-NOVA160",
                name="Lowepro Nova 160 AW Camera Bag",
                category=ProductCategory.ACCESSORIES,
                description="Padded shoulder bag with All Weather Cover™, fits a DSLR body with attached lens plus 2 additional lenses. Side access for fast camera retrieval, customisable interior dividers.",
                specifications={"fits": "DSLR + 2 lenses", "weather_resistant": True, "side_access": True, "tripod_straps": True, "weight_g": 560},
                compatible_skus=["CANON-EOS450D", "NIKON-D40"],
                complementary_skus=["KG-16GBSD", "JOBY-GPSRL"],
                tags=["bag", "camera bag", "accessories", "lowepro", "dslr bag", "carry"],
                price=79.99,
                in_stock=True,
            ),
            Product(
                sku="KG-16GBSD",
                name="Kingston 16GB Class 10 SDHC Card",
                category=ProductCategory.ACCESSORIES,
                description="Class 10 SDHC card with up to 10MB/s write speed — fast enough for burst shooting and 1080p video. Universally compatible with all SDHC/SDXC cameras and camcorders.",
                specifications={"capacity_gb": 16, "class": 10, "write_mbps": 10, "read_mbps": 45, "form_factor": "SDHC"},
                compatible_skus=["CANON-EOS450D", "NIKON-D40", "CANON-HFRE"],
                complementary_skus=["LP-NOVA160"],
                tags=["sd card", "memory card", "accessories", "kingston", "storage", "16gb"],
                price=24.99,
                in_stock=True,
            ),
            Product(
                sku="JOBY-GPSRL",
                name="Joby GorillaPod SLR Flexible Tripod",
                category=ProductCategory.ACCESSORIES,
                description="Flexible, wrappable mini-tripod with rubberised ring joints — wrap around branches, poles or railings. Supports DSLRs up to 1.5kg. Compact enough to fit in any camera bag.",
                specifications={"max_load_kg": 1.5, "height_cm": 25, "flexible": True, "weight_g": 260, "fits": "DSLRs and compact cameras"},
                compatible_skus=["CANON-EOS450D", "NIKON-D40"],
                complementary_skus=["LP-NOVA160", "KG-16GBSD"],
                tags=["tripod", "gorillpod", "accessories", "joby", "flexible", "mini tripod", "stand"],
                price=39.99,
                in_stock=True,
            ),
            Product(
                sku="CANON-EF50",
                name="Canon EF 50mm f/1.8 II Lens",
                category=ProductCategory.ACCESSORIES,
                description="Canon's legendary 'nifty fifty' — the fastest, sharpest, most affordable prime lens for EOS cameras. f/1.8 maximum aperture delivers beautiful background blur and excellent low-light performance.",
                specifications={"focal_length_mm": 50, "max_aperture": "f/1.8", "min_aperture": "f/22", "autofocus": True, "filter_mm": 52, "weight_g": 130},
                compatible_skus=["CANON-EOS450D"],
                complementary_skus=["LP-NOVA160", "JOBY-GPSRL"],
                tags=["lens", "canon lens", "accessories", "50mm", "prime lens", "ef lens", "bokeh"],
                price=109.99,
                in_stock=True,
            ),
            # ── Films & Media ─────────────────────────────────────────────────
            Product(
                sku="KODAK-MAX400",
                name="Kodak MAX Versatility 400 (3-pack)",
                category=ProductCategory.FILMS,
                description="ISO 400 colour negative film for all-purpose shooting indoors and out. Excellent grain, vivid Kodak colours, 24-exposure roll — 3 rolls per pack. Works in all 35mm film cameras.",
                specifications={"iso": 400, "exposures": 24, "format": "35mm", "type": "colour negative", "pack_count": 3},
                compatible_skus=[],
                complementary_skus=["FUJI-SUP200"],
                tags=["film", "kodak", "colour film", "iso 400", "35mm", "analogue", "photo film"],
                price=13.99,
                in_stock=True,
            ),
            Product(
                sku="FUJI-SUP200",
                name="Fujifilm Superia 200 (3-pack)",
                category=ProductCategory.FILMS,
                description="ISO 200 daylight colour negative film with Fujifilm's signature natural skin tones and fine grain. 36-exposure roll, 3 rolls per pack — great for outdoor and travel photography.",
                specifications={"iso": 200, "exposures": 36, "format": "35mm", "type": "colour negative", "pack_count": 3},
                compatible_skus=[],
                complementary_skus=["KODAK-MAX400"],
                tags=["film", "fuji", "fujifilm", "superia", "colour film", "iso 200", "35mm", "analogue"],
                price=10.99,
                in_stock=True,
            ),
        ]

        for p in sample_products:
            self._products[p.sku] = p
    
    def get_all(self) -> List[Product]:
        """Get all products"""
        return list(self._products.values())
    
    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        return self._products.get(sku)
    
    def get_by_category(self, category: ProductCategory) -> List[Product]:
        """Get products by category"""
        return [p for p in self._products.values() if p.category == category]
    
    def search(self, query: str) -> List[Product]:
        """Search products by query string"""
        query_lower = query.lower()
        results = []
        
        for product in self._products.values():
            # Check name
            if query_lower in product.name.lower():
                results.append(product)
                continue
            
            # Check description
            if query_lower in product.description.lower():
                results.append(product)
                continue
            
            # Check tags
            if any(query_lower in tag.lower() for tag in product.tags):
                results.append(product)
                continue
            
            # Check SKU
            if query_lower in product.sku.lower():
                results.append(product)
                continue
        
        return results
    
    def get_compatible(self, sku: str) -> List[Product]:
        """Get compatible products"""
        product = self._products.get(sku)
        if not product:
            return []
        
        return [
            self._products[s]
            for s in product.compatible_skus
            if s in self._products
        ]
    
    def get_complementary(self, sku: str) -> List[Product]:
        """Get complementary products"""
        product = self._products.get(sku)
        if not product:
            return []
        
        return [
            self._products[s]
            for s in product.complementary_skus
            if s in self._products
        ]
    
    def check_availability(self, sku: str) -> Dict[str, Any]:
        """Check product availability"""
        product = self._products.get(sku)
        if not product:
            return {"available": False, "error": "Product not found"}
        
        return {
            "sku": sku,
            "available": product.in_stock,
            "in_stock": product.in_stock,
        }
    
    def get_categories(self) -> List[Category]:
        """Get all categories"""
        return list(self._categories.values())
    
    def get_category(self, category_id: str) -> Optional[Category]:
        """Get category by ID"""
        return self._categories.get(category_id)
    
    def get_bundles(self) -> List[Bundle]:
        """Get all bundles"""
        return list(self._bundles.values())
    
    def get_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """Get bundle by ID"""
        return self._bundles.get(bundle_id)
