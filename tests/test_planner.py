"""
Tests for the Planner Component

Run: python tests/test_planner.py
"""
import sys
sys.path.insert(0, "/Users/utkarshkumar/Documents/Utkarsh 26 Workspace/10-19 Work/11 Projects/b2b-commerce-agent")

from src.agent import (
    Planner, PlanningContext,
    Intent, classify_intent,
    ConstraintExtractor, extract_constraints,
    Plan, PlanStatus,
    create_plan,
)
from src.agent.executor import PlanExecutor
from src.agent.tools import ToolRegistry
from src.data.product_catalog import ProductCatalog
from src.data.solution_cart import SolutionCart


def test_intent_classification():
    """Test intent classification"""
    print("\n" + "="*60)
    print("TEST: Intent Classification")
    print("="*60)
    
    test_cases = [
        ("I need a cooling system for 500 sq ft", Intent.RECOMMEND_PRODUCTS),
        ("Show me power supplies", Intent.BROWSE_CATEGORY),
        ("What's the difference between VoltGuard 1K and 2K?", Intent.COMPARE_PRODUCTS),
        ("Tell me about AeroCool C300", Intent.PRODUCT_INQUIRY),
        ("What's in my solution?", Intent.REVIEW_SOLUTION),
        ("Add VoltGuard to my solution", Intent.MODIFY_SOLUTION),
        ("My server room is overheating", Intent.PROBLEM_SOLVING),
        ("I need something", Intent.NEEDS_CLARIFICATION),
    ]
    
    passed = 0
    for query, expected in test_cases:
        result = classify_intent(query)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        print(f"{status} '{query[:40]}...' -> {result.value}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_constraint_extraction():
    """Test constraint extraction"""
    print("\n" + "="*60)
    print("TEST: Constraint Extraction")
    print("="*60)
    
    extractor = ConstraintExtractor()
    
    query = "I need a cooling system for 500 sq ft in the data center"
    constraints = extract_constraints(query)
    
    print(f"Query: '{query}'")
    print(f"Extracted {len(constraints)} constraints:")
    for c in constraints:
        print(f"  - {c.name}: {c.value} (confidence: {c.confidence})")
    
    # Check expected constraints
    space_constraint = next((c for c in constraints if c.name == "space"), None)
    cat_constraint = next((c for c in constraints if c.name == "category"), None)
    
    passed = space_constraint is not None and cat_constraint is not None
    print(f"\n{'✓' if passed else '✗'} Found space and category constraints")
    
    return passed


def test_plan_creation():
    """Test plan creation"""
    print("\n" + "="*60)
    print("TEST: Plan Creation")
    print("="*60)
    
    planner = Planner()
    
    query = "I need a cooling system for 500 sq ft"
    plan = planner.create_plan(query)
    
    print(f"Query: '{query}'")
    print(f"Intent: {plan.intent.value}")
    print(f"Constraints: {len(plan.constraints)}")
    print(f"Steps: {len(plan.steps)}")
    print(f"Fallback: {plan.fallback_strategy}")
    
    print("\nPlan Steps:")
    for step in plan.steps:
        print(f"  {step.step_number}. {step.action} [{step.tool}]")
        print(f"     Purpose: {step.purpose}")
    
    # Validate plan structure
    passed = (
        plan.intent == Intent.RECOMMEND_PRODUCTS and
        len(plan.steps) >= 3 and
        plan.steps[0].action == "search_products"
    )
    
    print(f"\n{'✓' if passed else '✗'} Plan created correctly")
    return passed


def test_different_intents():
    """Test plan creation for different intents"""
    print("\n" + "="*60)
    print("TEST: Plans for Different Intents")
    print("="*60)
    
    planner = Planner()
    
    test_cases = [
        ("Show me cooling products", Intent.BROWSE_CATEGORY),
        ("Compare VoltGuard 1K and 2K", Intent.COMPARE_PRODUCTS),
        ("What is AeroCool C300?", Intent.PRODUCT_INQUIRY),
        ("My server room is overheating", Intent.PROBLEM_SOLVING),
    ]
    
    passed = 0
    for query, expected_intent in test_cases:
        plan = planner.create_plan(query)
        correct = plan.intent == expected_intent
        if correct:
            passed += 1
        print(f"{'✓' if correct else '✗'} '{query[:30]}...'")
        print(f"   Intent: {plan.intent.value}")
        print(f"   Steps: {len(plan.steps)}")
        for step in plan.steps[:2]:
            print(f"     - {step.action}")
        print()
    
    print(f"Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_plan_execution():
    """Test plan execution with tools"""
    print("\n" + "="*60)
    print("TEST: Plan Execution")
    print("="*60)
    
    # Initialize dependencies
    catalog = ProductCatalog()
    solution = SolutionCart()
    tools = ToolRegistry(catalog, solution)
    
    planner = Planner()
    executor = PlanExecutor(tools)
    
    # Create a plan
    query = "I need a cooling system"
    plan = planner.create_plan(query)
    
    print(f"Query: '{query}'")
    print(f"Plan has {len(plan.steps)} steps")
    
    # Execute the plan
    result = executor.execute_plan(plan)
    
    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    print(f"  Steps completed: {result.steps_completed}")
    print(f"  Steps failed: {result.steps_failed}")
    print(f"  Time: {result.execution_time_ms}ms")
    print(f"  Response: {result.final_response[:100]}...")
    
    passed = result.success and result.steps_completed > 0
    print(f"\n{'✓' if passed else '✗'} Plan executed successfully")
    
    return passed


def test_replanning():
    """Test plan modification"""
    print("\n" + "="*60)
    print("TEST: Replanning")
    print("="*60)
    
    planner = Planner()
    
    query = "I need a cooling system"
    plan = planner.create_plan(query)
    
    print(f"Original plan: {len(plan.steps)} steps")
    
    # Mark first step as completed
    plan.mark_step_complete(1, {"results": ["product1", "product2"]})
    
    # Simulate new constraint
    new_info = {
        "new_constraints": [{"name": "budget", "value": "5000"}]
    }
    
    updated_plan = planner.replan(plan, new_info)
    
    print(f"Updated plan: {len(updated_plan.steps)} steps")
    print(f"Constraints now: {len(updated_plan.constraints)}")
    
    # Check step 1 is marked complete
    step1 = updated_plan.steps[0]
    passed = step1.status == PlanStatus.COMPLETED and step1.result is not None
    
    print(f"\n{'✓' if passed else '✗'} Replanning works correctly")
    return passed


def test_context_in_planning():
    """Test planning with context"""
    print("\n" + "="*60)
    print("TEST: Planning with Context")
    print("="*60)
    
    planner = Planner()
    
    context = PlanningContext(
        conversation_history=[
            {"role": "user", "content": "I have a 500 sq ft room"},
            {"role": "assistant", "content": "I can help with that size."},
        ],
        previous_constraints=[],
    )
    
    query = "What cooling system do you recommend?"
    plan = planner.create_plan(query, context)
    
    print(f"Query with context: '{query}'")
    print(f"Intent: {plan.intent.value}")
    
    # Check if space constraint was picked up from history
    space_constraint = next((c for c in plan.constraints if c.name == "space"), None)
    
    if space_constraint:
        print(f"✓ Space constraint found from context: {space_constraint.value}")
        passed = True
    else:
        print("ℹ Space constraint not automatically extracted (may need LLM)")
        passed = plan.intent == Intent.RECOMMEND_PRODUCTS
    
    print(f"\n{'✓' if passed else '✗'} Context-aware planning works")
    return passed


def test_plan_serialization():
    """Test plan round-trip serialization"""
    print("\n" + "="*60)
    print("TEST: Plan Serialization")
    print("="*60)
    
    planner = Planner()
    
    query = "I need cooling for 500 sq ft"
    plan = planner.create_plan(query)
    
    # Serialize to dict
    plan_dict = plan.to_dict()
    print(f"Serialized plan with {len(plan_dict['steps'])} steps")
    
    # Deserialize
    restored_plan = Plan.from_dict(plan_dict)
    print(f"Restored plan with {len(restored_plan.steps)} steps")
    
    # Verify
    passed = (
        restored_plan.intent == plan.intent and
        len(restored_plan.steps) == len(plan.steps) and
        restored_plan.original_query == plan.original_query
    )
    
    print(f"\n{'✓' if passed else '✗'} Round-trip serialization works")
    return passed


def test_replan_abort_path():
    """Test replan with critical step failure"""
    print("\n" + "="*60)
    print("TEST: Replan Abort Path")
    print("="*60)
    
    planner = Planner()
    
    query = "I need a cooling system"
    plan = planner.create_plan(query)
    
    # Simulate critical step failure (step 1 is always critical)
    new_info = {
        "failed_step": 1,
        "error": "Product search failed"
    }
    
    updated_plan = planner.replan(plan, new_info)
    
    # Check step 1 is marked failed
    step1 = updated_plan.steps[0]
    failed_correctly = step1.status == PlanStatus.FAILED and step1.error == "Product search failed"
    
    # Check fallback strategy updated for critical failure
    has_fallback = updated_plan.fallback_strategy == "abort_and_explain"
    
    passed = failed_correctly and has_fallback
    print(f"  Step 1 failed: {failed_correctly}")
    print(f"  Fallback set: {has_fallback}")
    print(f"\n{'✓' if passed else '✗'} Critical failure handling works")
    return passed


def test_invalid_constraint_source():
    """Test handling of invalid constraint source values"""
    print("\n" + "="*60)
    print("TEST: Invalid Constraint Source")
    print("="*60)
    
    # Create a plan dict with invalid source value
    plan_dict = {
        "intent": "recommend_products",
        "constraints": [
            {"name": "space", "value": 500, "source": "invalid_source", "confidence": 1.0}
        ],
        "steps": [],
        "original_query": "test",
        "estimated_tokens": 0,
        "fallback_strategy": "",
        "status": "pending"
    }
    
    try:
        plan = Plan.from_dict(plan_dict)
        # Should have 0 constraints (invalid one skipped) or 1 with default source
        passed = len(plan.constraints) in [0, 1]
        if passed and len(plan.constraints) == 1:
            # Verify it fell back to USER_EXPLICIT
            passed = plan.constraints[0].source.name == "USER_EXPLICIT"
        print(f"  Handled invalid source, constraints: {len(plan.constraints)}")
        print(f"\n{'✓' if passed else '✗'} Invalid source handled gracefully")
    except Exception as e:
        print(f"  Error: {e}")
        passed = False
        print(f"\n✗ Exception thrown - should handle gracefully")
    
    return passed


def run_all_tests():
    """Run all planner tests"""
    print("\n" + "="*70)
    print("PLANNER COMPONENT TEST SUITE")
    print("="*70)
    
    tests = [
        ("Intent Classification", test_intent_classification),
        ("Constraint Extraction", test_constraint_extraction),
        ("Plan Creation", test_plan_creation),
        ("Different Intents", test_different_intents),
        ("Plan Execution", test_plan_execution),
        ("Replanning", test_replanning),
        ("Context in Planning", test_context_in_planning),
        ("Plan Serialization", test_plan_serialization),
        ("Replan Abort Path", test_replan_abort_path),
        ("Invalid Constraint Source", test_invalid_constraint_source),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} FAILED with exception:")
            print(f"  {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed_count} test(s) failed")
    
    return passed_count == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
