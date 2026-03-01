"""
Intent Classification Evaluation Tests

Verifies agent correctly understands user intent.
"""
import pytest
from typing import Dict, Any, List


# Test data: Query → Expected Intent
INTENT_TEST_CASES = [
    {
        "query": "I need cooling for 1000 sq ft",
        "expected_intent": "recommend_products",
        "expected_category": "cooling",
        "expected_constraints": {"space": "1000 sq ft"},
    },
    {
        "query": "Show me all your UPS systems",
        "expected_intent": "browse_category",
        "expected_category": "power",
    },
    {
        "query": "Compare the VoltGuard 3000VA and PowerShield 6000VA",
        "expected_intent": "compare_products",
        "expected_products": ["PW-UPS-3000", "PW-UPS-6000"],
    },
    {
        "query": "What's in my solution?",
        "expected_intent": "review_solution",
    },
    {
        "query": "Add AeroCool Liquid C1000 to my cart",
        "expected_intent": "modify_solution",
        "expected_action": "add",
        "expected_product": "CS-LC-1000",
    },
    {
        "query": "What cooling do you recommend for a data center?",
        "expected_intent": "recommend_products",
        "expected_category": "cooling",
        "needs_clarification": True,  # Missing space size
    },
    {
        "query": "How much is the InfraWatch Pro?",
        "expected_intent": "product_inquiry",
        "expected_product": "MN-IC-PRO",
        "expected_info": "price",
    },
    {
        "query": "I have a small server room that's overheating",
        "expected_intent": "problem_solving",
        "inferred_need": "cooling",
        "inferred_space": "small server room",  # 200-500 sq ft
    },
    {
        "query": "Do you have anything for 500 square feet?",
        "expected_intent": "recommend_products",
        "expected_constraints": {"space": "500 sq ft"},
    },
    {
        "query": "Show me monitoring solutions",
        "expected_intent": "browse_category",
        "expected_category": "monitoring",
    },
]


class TestIntentClassification:
    """Test suite for intent classification"""
    
    @pytest.mark.parametrize("test_case", INTENT_TEST_CASES)
    def test_intent_classification(self, test_case: Dict[str, Any]):
        """
        Test that agent correctly classifies user intent.
        
        This is a placeholder - actual implementation would:
        1. Pass query to agent
        2. Get intent classification
        3. Compare to expected
        """
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        
        # TODO: Implement actual test
        # intent = agent.classify_intent(query)
        # assert intent.name == expected_intent
        
        # For now, just document expected behavior
        pytest.skip(f"TODO: Implement intent classification for '{query[:30]}...'")
    
    def test_ambiguous_query_needs_clarification(self):
        """
        Test that agent asks for clarification on ambiguous queries.
        
        Query: "I need something" is too vague.
        Agent should ask: "What category are you interested in?"
        """
        ambiguous_queries = [
            "I need something",
            "Show me products",
            "What do you have?",
            "Help me",
        ]
        
        for query in ambiguous_queries:
            # TODO: agent should return "needs_clarification" intent
            pass
        
        pytest.skip("TODO: Implement clarification detection")
    
    def test_constraint_extraction(self):
        """
        Test that agent correctly extracts constraints from queries.
        """
        test_cases = [
            {
                "query": "I need quiet cooling for 1000 sq ft near offices",
                "expected_constraints": {
                    "space": "1000 sq ft",
                    "noise_max": "70dB",  # implied by "quiet" and "offices"
                    "location": "near offices",
                }
            },
            {
                "query": "UPS for 3 racks under $2000",
                "expected_constraints": {
                    "rack_count": 3,
                    "budget_max": 2000,
                }
            },
        ]
        
        for tc in test_cases:
            # TODO: Verify constraint extraction
            pass
        
        pytest.skip("TODO: Implement constraint extraction tests")


# Smoke tests for CI (fast)
INTENT_SMOKE_TESTS = [
    ("I need cooling", "recommend_products"),
    ("Show me UPS", "browse_category"),
    ("What's in my solution?", "review_solution"),
]


class TestIntentSmoke:
    """Quick smoke tests for CI"""
    
    @pytest.mark.parametrize("query,expected_intent", INTENT_SMOKE_TESTS)
    def test_basic_intent(self, query: str, expected_intent: str):
        """Quick check that basic intents work"""
        pytest.skip("TODO: Implement smoke tests")


# Benchmark / regression tests
class TestIntentRegression:
    """Regression tests - known queries that should always work"""
    
    def test_cooling_queries(self):
        """Test various cooling-related queries"""
        cooling_queries = [
            "cooling for 1000 sq ft",
            "liquid cooling system",
            "server room AC",
            "data center cooling",
            "in-row cooling",
        ]
        
        for query in cooling_queries:
            # All should classify as cooling recommendation
            pass
        
        pytest.skip("TODO: Implement regression tests")
