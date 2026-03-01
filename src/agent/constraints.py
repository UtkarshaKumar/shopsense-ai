"""
Constraint Extraction

Extracts constraints from user queries for filtering and recommendations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import re


class ConstraintSource(Enum):
    """Where the constraint came from"""
    USER_EXPLICIT = "user_explicit"      # User directly stated
    USER_INFERRED = "user_inferred"      # Inferred from context
    CONTEXT = "context"                   # From previous conversation
    DEFAULT = "default"                   # System default


@dataclass
class Constraint:
    """Represents a single constraint"""
    name: str
    value: Any
    source: ConstraintSource
    confidence: float = 1.0  # 0.0 to 1.0
    raw_text: Optional[str] = None  # Original text that created this
    
    def __hash__(self):
        return hash((self.name, str(self.value)))


class ConstraintExtractor:
    """
    Extracts constraints from natural language queries.
    
    Handles:
    - Space/size requirements
    - Budget constraints
    - Noise/environment constraints
    - Form factor preferences
    - Category specifications
    """
    
    # Constraint extraction patterns
    PATTERNS = {
        "space": {
            "patterns": [
                r"(\d+(?:,\d+)?)\s*(?:sq\s*ft|sqft|sf|square\s*feet?)",
                r"(\d+(?:,\d+)?)\s*(?:square\s*meters?|sqm)",
                r"(\d+(?:,\d+)?)\s*(?:sq\s*m)",
            ],
            "unit": "sq_ft",
            "converter": lambda x: int(x.replace(",", "")),
        },
        "budget_max": {
            "patterns": [
                r"(?:under|less than|below|max|maximum)\s*(?:\$)?(\d+(?:,\d+)?(?:\.\d+)?)",
                r"(?:budget|spend)\s*(?:of\s*)?(?:\$)?(\d+(?:,\d+)?(?:\.\d+)?)",
                r"(?:\$)?(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:or less|max|maximum)",
            ],
            "unit": "USD",
            "converter": lambda x: float(x.replace(",", "")),
        },
        "rack_count": {
            "patterns": [
                r"(\d+)\s*(?:rack|racks)",
                r"(\d+)\s*U\s+(?:rack|racks?)",
            ],
            "unit": "racks",
            "converter": int,
        },
        "power_draw": {
            "patterns": [
                r"(\d+(?:\.\d+)?)\s*(?:kW|KW|kilowatt)",
                r"(\d+)\s*(?:W|watt|watts)",
            ],
            "unit": "kW",
            "converter": lambda x: float(x) / 1000 if float(x) > 100 else float(x),
        },
    }
    
    # Inferred constraints from keywords
    INFERRED_CONSTRAINTS = {
        "noise_max": {
            "keywords": ["quiet", "silent", "low noise", "near offices", "office"],
            "value": "65dB",
            "condition": lambda ctx: "office" in ctx.get("location", "") or "quiet" in ctx.get("requirements", []),
        },
        "form_factor": {
            "keywords": {
                "rack": "rack_mount",
                "tower": "tower",
                "wall": "wall_mount",
                "floor": "floor_stand",
            },
        },
        "environment": {
            "keywords": {
                "edge": "edge_location",
                "data center": "data_center",
                "server room": "server_room",
                "remote": "remote_site",
            },
        },
    }
    
    # Category mappings
    CATEGORY_KEYWORDS = {
        "cooling": ["cooling", "ac", "air conditioning", "chiller", "thermal", "temperature"],
        "power": ["power", "ups", "backup", "battery", "electricity"],
        "monitoring": ["monitoring", "sensor", "tracking", "alert", "temperature monitoring"],
        "distribution": ["distribution", "pdu", "power distribution", "outlet", "socket"],
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns"""
        self.compiled_patterns = {}
        for constraint_type, config in self.PATTERNS.items():
            self.compiled_patterns[constraint_type] = [
                re.compile(p, re.IGNORECASE) for p in config["patterns"]
            ]
    
    def extract(self, query: str, conversation_context: Optional[Dict] = None) -> List[Constraint]:
        """
        Extract all constraints from a query.
        
        Args:
            query: User's natural language query
            conversation_context: Previous conversation state
            
        Returns:
            List of extracted constraints
        """
        constraints = []
        query_lower = query.lower()
        
        # Extract explicit constraints using patterns
        constraints.extend(self._extract_explicit(query))
        
        # Extract inferred constraints from keywords
        constraints.extend(self._extract_inferred(query, conversation_context or {}))
        
        # Extract category constraints
        category = self._extract_category(query)
        if category:
            constraints.append(Constraint(
                name="category",
                value=category,
                source=ConstraintSource.USER_EXPLICIT,
                raw_text=query
            ))
        
        # Remove duplicates (keep highest confidence)
        return self._deduplicate(constraints)
    
    def _extract_explicit(self, query: str) -> List[Constraint]:
        """Extract explicit constraints using regex patterns"""
        constraints = []
        
        for constraint_type, patterns in self.compiled_patterns.items():
            config = self.PATTERNS[constraint_type]
            
            for pattern in patterns:
                match = pattern.search(query)
                if match:
                    try:
                        raw_value = match.group(1)
                        converted_value = config["converter"](raw_value)
                        
                        constraints.append(Constraint(
                            name=constraint_type,
                            value=converted_value,
                            source=ConstraintSource.USER_EXPLICIT,
                            confidence=1.0,
                            raw_text=match.group(0)
                        ))
                    except (ValueError, IndexError):
                        continue
        
        return constraints
    
    def _extract_inferred(self, query: str, context: Dict) -> List[Constraint]:
        """Extract constraints inferred from keywords"""
        constraints = []
        query_lower = query.lower()
        
        # Noise constraints
        noise_config = self.INFERRED_CONSTRAINTS["noise_max"]
        if any(kw in query_lower for kw in noise_config["keywords"]):
            # Check if condition is met
            condition_fn = noise_config.get("condition")
            if condition_fn is None or condition_fn(context):
                constraints.append(Constraint(
                    name="noise_max",
                    value=noise_config["value"],
                    source=ConstraintSource.USER_INFERRED,
                    confidence=0.8,
                    raw_text=f"Detected keywords: {noise_config['keywords']}"
                ))
        
        # Form factor constraints
        form_config = self.INFERRED_CONSTRAINTS["form_factor"]
        for keyword, value in form_config["keywords"].items():
            if keyword in query_lower:
                constraints.append(Constraint(
                    name="form_factor",
                    value=value,
                    source=ConstraintSource.USER_INFERRED,
                    confidence=0.7,
                    raw_text=f"Detected: {keyword}"
                ))
        
        # Environment constraints
        env_config = self.INFERRED_CONSTRAINTS["environment"]
        for keyword, value in env_config["keywords"].items():
            if keyword in query_lower:
                constraints.append(Constraint(
                    name="environment",
                    value=value,
                    source=ConstraintSource.USER_INFERRED,
                    confidence=0.75,
                    raw_text=f"Detected: {keyword}"
                ))
        
        return constraints
    
    def _extract_category(self, query: str) -> Optional[str]:
        """Extract category from query"""
        query_lower = query.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return category
        
        return None
    
    def _deduplicate(self, constraints: List[Constraint]) -> List[Constraint]:
        """Remove duplicate constraints, keeping highest confidence"""
        seen = {}
        
        for constraint in constraints:
            key = (constraint.name, str(constraint.value))
            if key not in seen or seen[key].confidence < constraint.confidence:
                seen[key] = constraint
        
        return list(seen.values())
    
    def merge_with_context(
        self,
        new_constraints: List[Constraint],
        existing_constraints: List[Constraint]
    ) -> List[Constraint]:
        """
        Merge new constraints with existing ones from conversation context.
        
        New explicit constraints override old ones.
        Old constraints persist unless explicitly changed.
        """
        constraint_map = {(c.name, str(c.value)): c for c in existing_constraints}
        
        for new_c in new_constraints:
            key = (new_c.name, str(new_c.value))
            
            if key in constraint_map:
                # Update if new constraint has higher confidence or is explicit
                existing = constraint_map[key]
                if (new_c.source == ConstraintSource.USER_EXPLICIT and 
                    existing.source != ConstraintSource.USER_EXPLICIT):
                    constraint_map[key] = new_c
                elif new_c.confidence > existing.confidence:
                    constraint_map[key] = new_c
            else:
                constraint_map[key] = new_c
        
        return list(constraint_map.values())
    
    def format_for_display(self, constraints: List[Constraint]) -> str:
        """Format constraints for display to user"""
        if not constraints:
            return "No specific constraints"
        
        lines = ["Current constraints:"]
        
        for c in sorted(constraints, key=lambda x: x.name):
            source_indicator = {
                ConstraintSource.USER_EXPLICIT: "✓",
                ConstraintSource.USER_INFERRED: "~",
                ConstraintSource.CONTEXT: "→",
                ConstraintSource.DEFAULT: "•",
            }.get(c.source, "•")
            
            lines.append(f"  {source_indicator} {c.name}: {c.value}")
        
        return "\n".join(lines)


# Convenience function
def extract_constraints(query: str, context: Optional[Dict] = None) -> List[Constraint]:
    """Quick constraint extraction"""
    extractor = ConstraintExtractor()
    return extractor.extract(query, context)
