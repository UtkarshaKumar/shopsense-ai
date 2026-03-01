"""
Intent Classification for the Planner

Maps user queries to actionable intents.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Pattern
import re


class Intent(Enum):
    """Enumeration of possible user intents"""
    RECOMMEND_PRODUCTS = "recommend_products"
    BROWSE_CATEGORY = "browse_category"
    COMPARE_PRODUCTS = "compare_products"
    PRODUCT_INQUIRY = "product_inquiry"
    REVIEW_SOLUTION = "review_solution"
    MODIFY_SOLUTION = "modify_solution"
    PROBLEM_SOLVING = "problem_solving"
    NEEDS_CLARIFICATION = "needs_clarification"


@dataclass
class IntentPattern:
    """Pattern for matching an intent"""
    intent: Intent
    patterns: List[Pattern]
    keywords: List[str]
    confidence_threshold: float = 0.7


class IntentClassifier:
    """
    Classifies user queries into intents.
    
    Uses a hybrid approach:
    1. Regex patterns for explicit matches
    2. Keyword scoring for fuzzy matches
    3. Context awareness for disambiguation
    """
    
    INTENT_PATTERNS: Dict[Intent, Dict] = {
        Intent.RECOMMEND_PRODUCTS: {
            "patterns": [
                r"i need\s+(?:a|an)?\s*(.+)",
                r"recommend\s+(?:a|an)?\s*(.+)",
                r"what\s+(.+)\s+(?:should|do)\s+i\s+(?:get|use|buy)",
                r"(.+)\s+for\s+(\d+)\s*(?:sq\s*ft|square\s*feet)",
                r"(?:looking|searching)\s+for\s+(.+)",
                r"suggest\s+(?:a|an)?\s*(.+)",
            ],
            "keywords": ["need", "recommend", "suggest", "what", "looking", "searching"],
            "weight": 1.0,
        },
        Intent.BROWSE_CATEGORY: {
            "patterns": [
                r"show\s+(?:me\s+)?(?:all\s+)?(.+)",
                r"what\s+(.+)\s+do\s+you\s+(?:have|carry|offer)",
                r"list\s+(?:all\s+)?(.+)",
                r"(?:show|display)\s+(?:me\s+)?(?:the\s+)?(.+)\s+options",
            ],
            "keywords": ["show", "list", "what", "options", "all"],
            "weight": 1.0,
        },
        Intent.COMPARE_PRODUCTS: {
            "patterns": [
                r"compare\s+(.+)\s+(?:and|vs|versus)\s+(.+)",
                r"(.+)\s+(?:vs|versus)\s+(.+)",
                r"difference\s+(?:between\s+)?(.+)\s+(?:and\s+)?(.+)",
                r"which\s+(?:is\s+)?better[,:]?\s+(.+)\s+(?:or|vs)\s+(.+)",
            ],
            "keywords": ["compare", "vs", "versus", "difference", "better", "which"],
            "weight": 1.0,
        },
        Intent.PRODUCT_INQUIRY: {
            "patterns": [
                r"(?:how\s+much\s+(?:is|does)|what\s+(?:is\s+)?(?:the\s+)?price\s+(?:of\s+)?)?(.+)\s+cost",
                r"how\s+much\s+(?:is|for)\s+(.+)",
                r"tell\s+(?:me\s+)?(?:about\s+)?(.+)",
                r"(?:what\s+are|tell\s+me)\s+(?:the\s+)?specs\s+(?:for\s+)?(.+)",
                r"details\s+(?:for\s+)?(?:about\s+)?(.+)",
                r"what['\s]?is\s+(.+)",
                r"info\s+(?:on|about)\s+(.+)",
            ],
            "keywords": ["how much", "price", "cost", "specs", "details", "tell me", "what is", "what's", "info"],
            "weight": 1.0,
        },
        Intent.REVIEW_SOLUTION: {
            "patterns": [
                r"what['']?s\s+in\s+(?:my\s+)?solution",
                r"show\s+(?:me\s+)?(?:my\s+)?(?:cart|solution|selection)",
                r"what\s+have\s+i\s+(?:selected|chosen|added)",
                r"review\s+(?:my\s+)?solution",
            ],
            "keywords": ["solution", "cart", "selected", "chosen", "added", "review"],
            "weight": 1.0,
        },
        Intent.MODIFY_SOLUTION: {
            "patterns": [
                r"(?:add|include)\s+(.+)\s+(?:to\s+)?(?:my\s+)?solution",
                r"(?:remove|delete)\s+(.+)\s+(?:from\s+)?(?:my\s+)?solution",
                r"clear\s+(?:my\s+)?solution",
                r"take\s+out\s+(.+)",
            ],
            "keywords": ["add", "remove", "delete", "clear", "include", "take out"],
            "weight": 1.0,
        },
        Intent.PROBLEM_SOLVING: {
            "patterns": [
                r"my\s+(.+)\s+(?:is|are)\s+(?:overheating|too\s+hot|having\s+issues|not\s+working)",
                r"i\s+have\s+(?:a|an)\s+problem\s+with\s+(.+)",
                r"help\s+(?:me\s+)?(?:with\s+)?(.+)",
                r"what\s+should\s+i\s+do\s+about\s+(.+)",
            ],
            "keywords": ["overheating", "problem", "help", "issue", "not working"],
            "weight": 1.0,
        },
    }
    
    # Categories for context
    CATEGORIES = ["cooling", "power", "monitoring", "distribution", "ups"]
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self.compiled_patterns: Dict[Intent, List[Pattern]] = {}
        for intent, config in self.INTENT_PATTERNS.items():
            self.compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in config["patterns"]
            ]
    
    def classify(self, query: str, conversation_context: Optional[Dict] = None) -> Intent:
        """
        Classify user query into an intent.
        
        Args:
            query: User's natural language query
            conversation_context: Previous conversation state (for context-aware classification)
            
        Returns:
            Classified intent
        """
        query_lower = query.lower().strip()
        
        # Check for vague queries first
        vague_words = ["something", "anything", "whatever", "stuff"]
        specific_product_words = ["cooling", "power", "monitor", "server", "rack", "ups", "system", "device", "unit", "equipment"]
        
        if any(w in query_lower for w in vague_words):
            # If no specific category or product mentioned, it's too vague
            if not any(w in query_lower for w in specific_product_words):
                return Intent.NEEDS_CLARIFICATION
        
        # Check for "what is" patterns for product inquiry
        # But first check it's not a solution/cart query
        if "in my solution" in query_lower or "in my cart" in query_lower:
            pass  # Let it go to normal scoring
        elif re.search(r"^what['\s]?is\s+(.+)", query_lower) or re.search(r"^what['\s]?s\s+(.+)", query_lower):
            # Check if it's asking about a product (not a concept)
            potential_product = re.sub(r"^what['\s]?is\s+", "", query_lower)
            potential_product = re.sub(r"^what['\s]?s\s+", "", potential_product)
            # If it looks like a product name or has no question words, treat as inquiry
            if not any(w in potential_product for w in ["the", "your", "this", "how", "why", "in my"]):
                return Intent.PRODUCT_INQUIRY
        
        # Score each intent
        scores: Dict[Intent, float] = {}
        
        for intent, patterns in self.compiled_patterns.items():
            score = 0.0
            
            # Check regex patterns (high confidence)
            for pattern in patterns:
                if pattern.search(query_lower):
                    score += 1.0
            
            # Check keywords (lower confidence)
            keywords = self.INTENT_PATTERNS[intent]["keywords"]
            for keyword in keywords:
                if keyword in query_lower:
                    score += 0.3
            
            # Apply intent weight
            weight = self.INTENT_PATTERNS[intent].get("weight", 1.0)
            scores[intent] = score * weight
        
        # Get highest scoring intent
        if not scores:
            return Intent.NEEDS_CLARIFICATION
        
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # Check if score meets threshold
        threshold = self.INTENT_PATTERNS[best_intent].get("confidence_threshold", 0.5)
        if best_score < threshold:
            return Intent.NEEDS_CLARIFICATION
        
        # Check for ambiguity (close scores)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) < 0.2:
            # Too close to call, needs clarification
            return Intent.NEEDS_CLARIFICATION
        
        return best_intent
    
    def extract_targets(self, query: str, intent: Intent) -> List[str]:
        """
        Extract target entities from query based on intent.
        
        For example:
        - "Compare A and B" → ["A", "B"]
        - "Add X to solution" → ["X"]
        """
        targets = []
        
        if intent not in self.compiled_patterns:
            return targets
        
        patterns = self.compiled_patterns[intent]
        for pattern in patterns:
            match = pattern.search(query.lower())
            if match:
                # Extract all groups
                groups = match.groups()
                targets.extend([g.strip() for g in groups if g])
        
        return targets


# Convenience function
def classify_intent(query: str, context: Optional[Dict] = None) -> Intent:
    """Quick intent classification"""
    classifier = IntentClassifier()
    return classifier.classify(query, context)
