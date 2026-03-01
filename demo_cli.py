#!/usr/bin/env python3
"""
Interactive Demo CLI for B2B Commerce Agent

Test the planner component interactively.
"""
import sys
sys.path.insert(0, "/Users/utkarshkumar/Documents/Utkarsh 26 Workspace/10-19 Work/11 Projects/b2b-commerce-agent")

from src.agent import Planner, PlanningContext, Intent, classify_intent, extract_constraints
from src.agent.executor import PlanExecutor
from src.agent.tools import ToolRegistry
from src.data.product_catalog import ProductCatalog
from src.data.solution_cart import SolutionCart


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_step(step, result=None):
    status_icon = "✓" if step.status.value == "completed" else "○" if step.status.value == "pending" else "✗"
    print(f"  {status_icon} Step {step.step_number}: {step.action}")
    if result:
        if result.success:
            if isinstance(result.data, list):
                print(f"      → Found {len(result.data)} items")
            elif hasattr(result.data, 'name'):
                print(f"      → {result.data.name}")
            else:
                print(f"      → {result.message}")
        else:
            print(f"      ✗ Error: {result.error}")


def demo_intent_classification():
    print_header("INTENT CLASSIFICATION DEMO")
    
    test_queries = [
        "I need cooling for 1000 sq ft",
        "Show me power supplies",
        "Compare AeroCool C1000 and C2000",
        "What's in my solution?",
        "Add VoltGuard to my cart",
    ]
    
    for query in test_queries:
        intent = classify_intent(query)
        print(f"  '{query}'")
        print(f"    → Intent: {intent.value}\n")


def demo_constraint_extraction():
    print_header("CONSTRAINT EXTRACTION DEMO")
    
    query = "I need a cooling system for 500 sq ft in a data center with low noise"
    constraints = extract_constraints(query)
    
    print(f"  Query: '{query}'\n")
    print(f"  Extracted {len(constraints)} constraints:")
    for c in constraints:
        print(f"    • {c.name}: {c.value} (confidence: {c.confidence})")


def demo_plan_creation():
    print_header("PLAN CREATION DEMO")
    
    planner = Planner()
    
    queries = [
        "I need a cooling system for 500 sq ft",
        "Show me power supplies",
        "What is AeroCool C1000?",
    ]
    
    for query in queries:
        print(f"\n  Query: '{query}'")
        plan = planner.create_plan(query)
        print(f"  Intent: {plan.intent.value}")
        print(f"  Steps ({len(plan.steps)}):")
        for step in plan.steps:
            print(f"    {step.step_number}. {step.action} [{step.tool}]")


def demo_full_execution():
    print_header("FULL PLAN EXECUTION DEMO")
    
    # Initialize
    catalog = ProductCatalog()
    solution = SolutionCart()
    tools = ToolRegistry(catalog, solution)
    planner = Planner()
    executor = PlanExecutor(tools)
    
    print("  Components initialized:")
    print(f"    • Catalog: {len(catalog.get_all())} products")
    print(f"    • Solution: {solution.get_count()} items")
    print(f"    • Tools: {len(tools.list_tools())} available")
    
    # Interactive loop
    print("\n  Enter a query (or 'quit' to exit):")
    
    while True:
        try:
            query = input("\n  > ").strip()
            if query.lower() in ('quit', 'exit', 'q'):
                break
            if not query:
                continue
            
            print(f"\n  Processing: '{query}'...")
            
            # Create plan
            plan = planner.create_plan(query)
            print(f"  Intent detected: {plan.intent.value}")
            print(f"  Plan: {len(plan.steps)} steps")
            
            # Execute
            result = executor.execute_plan(plan)
            
            print(f"\n  Execution: {result.steps_completed}/{result.steps_completed + result.steps_failed} steps")
            print(f"  Response: {result.final_response}")
            
            # Show results from completed steps
            for step in plan.get_completed_steps():
                if step.result:
                    if isinstance(step.result, list) and step.result:
                        print(f"\n  Products found:")
                        for item in step.result[:5]:
                            if hasattr(item, 'name'):
                                print(f"    • {item.name} ({item.sku})")
                    break
                    
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n  Demo complete!")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     B2B AI Commerce Companion - Planner Demo                 ║
║     localhost:8000 (Mock API running)                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        demo_full_execution()
    else:
        demo_intent_classification()
        demo_constraint_extraction()
        demo_plan_creation()
        
        print("\n" + "="*60)
        print("  Run with --full flag for interactive mode:")
        print("  python3 demo_cli.py --full")
        print("="*60)


if __name__ == "__main__":
    main()
