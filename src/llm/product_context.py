"""
Product Context Management

Provides LLM with understanding of product catalog without
overwhelming context window.

Strategy: Hybrid approach
1. Concise Product Guide (in-context)
2. RAG for detailed lookups (retrieval)
3. Tools for real-time queries (API)
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProductSummary:
    """Condensed product info for LLM context"""
    code: str
    name: str
    category: str
    price: float
    key_specs: Dict[str, str]
    best_for: List[str]  # Use cases
    complementary: List[str]


class ProductContextManager:
    """
    Manages product knowledge for LLM consumption.
    
    Creates multiple views of product catalog:
    - Overview: Categories and their purposes
    - Quick Reference: Top products by category
    - Use Case Map: Products → scenarios they solve
    - Spec Matrix: Technical specifications
    """
    
    def __init__(self, products_file: str, categories_file: str):
        with open(products_file) as f:
            self.products = json.load(f)["products"]
        with open(categories_file) as f:
            self.categories = {c["id"]: c for c in json.load(f)["categories"]}
        
        self._build_indexes()
    
    def _build_indexes(self):
        """Build lookup indexes for fast retrieval"""
        self.products_by_category = {}
        self.products_by_use_case = {}
        
        for p in self.products:
            # By category
            cat = p["category"]
            if cat not in self.products_by_category:
                self.products_by_category[cat] = []
            self.products_by_category[cat].append(p)
            
            # By use case (inferred from name/description)
            use_cases = self._infer_use_cases(p)
            for uc in use_cases:
                if uc not in self.products_by_use_case:
                    self.products_by_use_case[uc] = []
                self.products_by_use_case[uc].append(p)
    
    def _infer_use_cases(self, product: Dict) -> List[str]:
        """Infer use cases from product attributes"""
        use_cases = []
        name_lower = product["name"].lower()
        desc_lower = product["description"].lower()
        specs = product.get("specifications", {})
        
        # Space-based
        if "1000" in name_lower or "1000" in desc_lower:
            use_cases.append("small_data_center")
        if "2000" in name_lower or "large" in desc_lower:
            use_cases.append("medium_data_center")
        if "500" in name_lower or "small" in desc_lower:
            use_cases.append("edge_location")
        if "3000" in name_lower or "enterprise" in desc_lower:
            use_cases.append("large_data_center")
        
        # Density-based
        if "high-density" in desc_lower or "rack" in desc_lower:
            use_cases.append("high_density")
        
        # Form factor
        if "tower" in name_lower:
            use_cases.append("tower_form_factor")
        if "rack" in name_lower:
            use_cases.append("rack_mount")
        
        # Noise
        noise = specs.get("noise_level", "")
        if "65" in noise or "58" in noise:
            use_cases.append("quiet_environment")
        
        return use_cases
    
    def get_context_guide(self, detail_level: str = "standard") -> str:
        """
        Generate product guide for LLM context.
        
        detail_level: "minimal" | "standard" | "comprehensive"
        """
        if detail_level == "minimal":
            return self._get_minimal_guide()
        elif detail_level == "standard":
            return self._get_standard_guide()
        else:
            return self._get_comprehensive_guide()
    
    def _get_minimal_guide(self) -> str:
        """Minimal context (~500 tokens) - for simple queries"""
        lines = [
            "Product Catalog Summary",
            "=" * 50,
            "",
            "Categories:",
        ]
        
        for cat_id, cat in self.categories.items():
            lines.append(f"- {cat['name']}: {cat['description'][:60]}...")
        
        lines.extend([
            "",
            "Featured Products:",
        ])
        
        featured = [p for p in self.products if p.get("featured", False)]
        for p in featured[:4]:
            lines.append(f"- {p['name']} ({p['category']}): ${p['price']:.0f}")
        
        lines.extend([
            "",
            "Use product_search tool for specific queries.",
        ])
        
        return "\n".join(lines)
    
    def _get_standard_guide(self) -> str:
        """Standard context (~1500 tokens) - for most queries"""
        lines = [
            "B2B Commerce Product Guide",
            "=" * 50,
            "",
            "OVERVIEW",
            "-" * 50,
            "We offer 4 categories of infrastructure products:",
            "",
        ]
        
        # Category details
        for cat_id, cat in self.categories.items():
            lines.extend([
                f"{cat['icon']} {cat['name']} ({cat_id})",
                f"  {cat['description']}",
                f"  Color: {cat['color']}",
                "",
                "  Key Products:",
            ])
            
            # Top 3 products in category
            cat_products = self.products_by_category.get(cat_id, [])
            for p in cat_products[:3]:
                specs = p.get("specifications", {})
                spec_summary = self._summarize_specs(specs, cat_id)
                lines.append(f"    • {p['name']} [{p['code']}]")
                lines.append(f"      Price: ${p['price']:.0f} | {spec_summary}")
            
            lines.append("")
        
        # Quick reference
        lines.extend([
            "USE CASE QUICK REFERENCE",
            "-" * 50,
            "Small Edge Location (100-200 sq ft):",
            "  → ChillZone AC500 + VoltGuard UPS 1500VA + SmartStrip 8",
            "",
            "Small Data Center (500-1000 sq ft):",
            "  → AeroCool Liquid C1000 + VoltGuard UPS 3000VA + InfraWatch Pro",
            "",
            "Medium Data Center (1000-2000 sq ft):",
            "  → FrostFlow CR2000 + PowerShield 6kVA + TempGuard Advanced",
            "",
            "Large Data Center (2000+ sq ft):",
            "  → ThermoMax HX3000 + PowerShield 10kVA + InfraWatch Enterprise",
            "",
            "TOOLS AVAILABLE",
            "-" * 50,
            "• product_search(query, category?) - Search products",
            "• get_product_details(code) - Full product info",
            "• check_stock(code) - Availability",
            "• get_complementary(code) - Related products",
            "• get_bundles(space_requirement?) - Pre-built solutions",
            "",
        ])
        
        return "\n".join(lines)
    
    def _get_comprehensive_guide(self) -> str:
        """Comprehensive context (~3000 tokens) - for complex queries"""
        lines = [
            "Complete Product Catalog Reference",
            "=" * 50,
            "",
        ]
        
        # All categories with all products
        for cat_id, cat in self.categories.items():
            lines.extend([
                f"{cat['icon']} {cat['name'].upper()}",
                "=" * 50,
                f"{cat['description']}",
                "",
            ])
            
            cat_products = self.products_by_category.get(cat_id, [])
            for p in cat_products:
                specs = p.get("specifications", {})
                lines.extend([
                    f"{p['name']} [{p['code']}]",
                    f"  Price: ${p['price']:.2f} | Stock: {'Yes' if p['in_stock'] else 'No'}",
                    f"  {p['short_description'] or p['description'][:100]}",
                ])
                
                # Key specs
                spec_lines = []
                for key, value in specs.items():
                    if value and key not in ['certifications']:
                        spec_lines.append(f"{key.replace('_', ' ').title()}: {value}")
                if spec_lines:
                    lines.append(f"  Specs: {' | '.join(spec_lines[:3])}")
                
                lines.append("")
        
        # Bundles
        lines.extend([
            "PRE-BUILT BUNDLES",
            "=" * 50,
            "",
        ])
        
        # We would load bundles here
        lines.append("Use get_bundles tool for pre-built solution packages.")
        
        return "\n".join(lines)
    
    def _summarize_specs(self, specs: Dict, category: str) -> str:
        """Extract most relevant spec for display"""
        if category == "cooling":
            return f"{specs.get('capacity', 'N/A')} capacity"
        elif category == "power":
            return f"{specs.get('capacity', 'N/A')} output"
        elif category == "monitoring":
            return f"{specs.get('sensors_included', 'N/A')} sensors"
        elif category == "distribution":
            return f"{specs.get('outlets', 'N/A')} outlets"
        return ""
    
    def get_products_for_query(self, query: str) -> List[ProductSummary]:
        """
        Retrieve relevant products for a specific query.
        Used for RAG-style retrieval to augment context.
        """
        query_lower = query.lower()
        relevant = []
        
        # Category matching
        for cat_id, cat in self.categories.items():
            if cat_id in query_lower or cat["name"].lower() in query_lower:
                for p in self.products_by_category.get(cat_id, [])[:3]:
                    relevant.append(self._to_summary(p))
        
        # Use case matching
        for use_case, products in self.products_by_use_case.items():
            if use_case.replace("_", " ") in query_lower:
                for p in products[:2]:
                    if p["code"] not in [r.code for r in relevant]:
                        relevant.append(self._to_summary(p))
        
        # Keyword matching
        keywords = query_lower.split()
        for p in self.products:
            name_lower = p["name"].lower()
            desc_lower = p["description"].lower()
            if any(kw in name_lower or kw in desc_lower for kw in keywords if len(kw) > 3):
                if p["code"] not in [r.code for r in relevant]:
                    relevant.append(self._to_summary(p))
        
        return relevant[:6]  # Limit to top 6
    
    def _to_summary(self, p: Dict) -> ProductSummary:
        """Convert full product to summary"""
        specs = p.get("specifications", {})
        
        # Extract key specs
        key_specs = {}
        if "capacity" in specs:
            key_specs["capacity"] = specs["capacity"]
        if "dimensions" in specs:
            key_specs["dimensions"] = specs["dimensions"]
        if "noise_level" in specs:
            key_specs["noise"] = specs["noise_level"]
        
        # Infer best_for
        best_for = []
        name_lower = p["name"].lower()
        if "1000" in name_lower:
            best_for.append("1000 sq ft data centers")
        if "2000" in name_lower:
            best_for.append("2000 sq ft data centers")
        if "500" in name_lower:
            best_for.append("edge locations")
        if "rack" in name_lower:
            best_for.append("rack-mount setups")
        
        return ProductSummary(
            code=p["code"],
            name=p["name"],
            category=p["category"],
            price=p["price"],
            key_specs=key_specs,
            best_for=best_for or ["general use"],
            complementary=p.get("complementary_products", [])
        )
    
    def format_for_prompt(self, products: List[ProductSummary]) -> str:
        """Format product summaries for inclusion in LLM prompt"""
        lines = ["\nRelevant Products:"]
        for p in products:
            lines.extend([
                f"\n{p.name} [{p.code}]",
                f"  Category: {p.category} | Price: ${p.price:.0f}",
                f"  Specs: {', '.join(f'{k}={v}' for k,v in p.key_specs.items())}",
                f"  Best for: {', '.join(p.best_for)}",
            ])
        return "\n".join(lines)
    
    def get_system_prompt(self) -> str:
        """
        Generate system prompt with product context.
        This is included in every LLM call.
        """
        return f"""You are an AI Commerce Companion for a B2B infrastructure company.

{self._get_standard_guide()}

YOUR ROLE:
- Help customers find the right products for their infrastructure needs
- Ask clarifying questions when requirements are unclear
- Recommend complete solutions, not just individual products
- Explain technical concepts in accessible language
- Remember constraints mentioned by the user

RESPONSE STYLE:
- Be helpful and professional
- Explain your reasoning
- Use product names and codes accurately
- Suggest complementary products when relevant
- Warn about missing components in solutions

Always base recommendations on actual product specifications.
"""


# Singleton instance
_context_manager = None

def get_context_manager() -> ProductContextManager:
    """Get or create singleton context manager"""
    global _context_manager
    if _context_manager is None:
        import os
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        _context_manager = ProductContextManager(
            products_file=os.path.join(data_dir, "products.json"),
            categories_file=os.path.join(data_dir, "categories.json")
        )
    return _context_manager


if __name__ == "__main__":
    # Test context generation
    cm = get_context_manager()
    
    print("=== MINIMAL GUIDE ===")
    print(cm.get_context_guide("minimal"))
    print("\n\n=== STANDARD GUIDE (truncated) ===")
    guide = cm.get_context_guide("standard")
    print(guide[:2000] + "...")
    
    print("\n\n=== QUERY-SPECIFIC PRODUCTS ===")
    products = cm.get_products_for_query("cooling for 1000 sq ft")
    print(cm.format_for_prompt(products))
