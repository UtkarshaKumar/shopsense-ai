"""
Planner - The Brain of the Agent

Takes user input and generates execution plans.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from .intent import Intent, IntentClassifier, classify_intent
from .constraints import Constraint, ConstraintExtractor, ConstraintSource, extract_constraints
from .plan import Plan, PlanStep, PlanStatus


@dataclass
class PlanningContext:
    """Context available during planning"""
    conversation_history: List[Dict[str, str]] = None
    previous_constraints: List[Constraint] = None
    user_preferences: Dict[str, Any] = None
    session_id: str = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.previous_constraints is None:
            self.previous_constraints = []
        if self.user_preferences is None:
            self.user_preferences = {}


class Planner:
    """
    The main planner that orchestrates intent classification,
    constraint extraction, and plan generation.
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.constraint_extractor = ConstraintExtractor()
    
    def create_plan(
        self,
        query: str,
        context: Optional[PlanningContext] = None
    ) -> Plan:
        """
        Create an execution plan from a user query.
        
        Args:
            query: User's natural language query
            context: Optional planning context with history
            
        Returns:
            A complete execution plan
        """
        if context is None:
            context = PlanningContext()
        
        # Step 1: Classify intent
        intent = self.intent_classifier.classify(query, {
            "history": context.conversation_history,
            "preferences": context.user_preferences,
        })
        
        # Step 2: Extract constraints
        new_constraints = self.constraint_extractor.extract(query, {
            "history": context.conversation_history,
        })
        
        # Step 3: Merge with existing constraints
        all_constraints = self.constraint_extractor.merge_with_context(
            new_constraints,
            context.previous_constraints
        )
        
        # Step 4: Generate plan based on intent
        steps = self._generate_steps(intent, query, all_constraints)
        
        # Step 5: Create plan object
        plan = Plan(
            intent=intent,
            constraints=all_constraints,
            steps=steps,
            original_query=query,
            estimated_tokens=self._estimate_tokens(steps),
            fallback_strategy=self._get_fallback_strategy(intent),
        )
        
        return plan
    
    def replan(
        self,
        current_plan: Plan,
        new_info: Dict[str, Any],
        context: Optional[PlanningContext] = None
    ) -> Plan:
        """
        Modify an existing plan based on new information.
        
        Args:
            current_plan: The plan to modify
            new_info: New information (e.g., user clarification, tool result)
            context: Planning context
            
        Returns:
            Updated plan
        """
        # Mark completed steps
        if "completed_step" in new_info:
            step_num = new_info["completed_step"]
            result = new_info.get("result")
            current_plan.mark_step_complete(step_num, result)
        
        # Handle failed steps
        if "failed_step" in new_info:
            step_num = new_info["failed_step"]
            error = new_info.get("error", "Unknown error")
            current_plan.mark_step_failed(step_num, error)
            
            # If critical step failed, might need to abort or replan
            if self._is_critical_step(current_plan, step_num):
                current_plan.fallback_strategy = "abort_and_explain"
        
        # Handle new constraints from user
        if "new_constraints" in new_info:
            for constraint_data in new_info["new_constraints"]:
                constraint = Constraint(
                    name=constraint_data["name"],
                    value=constraint_data["value"],
                    source=ConstraintSource.USER_EXPLICIT,
                )
                current_plan.constraints.append(constraint)
            
            # Re-evaluate remaining steps
            remaining_steps = current_plan.get_pending_steps()
            for step in remaining_steps:
                if not self._step_matches_constraints(step, current_plan.constraints):
                    step.status = PlanStatus.SKIPPED
        
        return current_plan
    
    def _generate_steps(
        self,
        intent: Intent,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate plan steps based on intent"""
        
        step_generators = {
            Intent.RECOMMEND_PRODUCTS: self._generate_recommendation_steps,
            Intent.BROWSE_CATEGORY: self._generate_browse_steps,
            Intent.COMPARE_PRODUCTS: self._generate_comparison_steps,
            Intent.PRODUCT_INQUIRY: self._generate_inquiry_steps,
            Intent.REVIEW_SOLUTION: self._generate_review_steps,
            Intent.MODIFY_SOLUTION: self._generate_modify_steps,
            Intent.PROBLEM_SOLVING: self._generate_problem_solving_steps,
            Intent.NEEDS_CLARIFICATION: self._generate_clarification_steps,
        }
        
        generator = step_generators.get(intent, self._generate_default_steps)
        return generator(query, constraints)
    
    def _generate_recommendation_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for product recommendation"""
        steps = []
        step_num = 1
        
        # Get category from constraints
        category = None
        for c in constraints:
            if c.name == "category":
                category = c.value
                break
        
        # Step 1: Search products
        search_params = {"query": query}
        if category:
            search_params["category"] = category
        
        steps.append(PlanStep(
            step_number=step_num,
            action="search_products",
            tool="search_products",
            parameters=search_params,
            purpose="Find products matching user requirements",
            expected_outcome="List of relevant products",
        ))
        step_num += 1
        
        # Step 2: Filter by constraints (if specific constraints exist)
        space_constraint = next((c for c in constraints if c.name == "space"), None)
        if space_constraint:
            steps.append(PlanStep(
                step_number=step_num,
                action="filter_by_space",
                tool="filter_products",
                parameters={"space": space_constraint.value},
                purpose=f"Filter products suitable for {space_constraint.value} sq ft",
                expected_outcome="Filtered product list",
            ))
            step_num += 1
        
        # Step 3: Check stock
        steps.append(PlanStep(
            step_number=step_num,
            action="check_availability",
            tool="check_stock",
            parameters={"for_recommended": True},
            purpose="Verify products are in stock",
            expected_outcome="Stock status for each product",
        ))
        step_num += 1
        
        # Step 4: Get complementary products
        steps.append(PlanStep(
            step_number=step_num,
            action="suggest_complementary",
            tool="get_complementary",
            parameters={},
            purpose="Suggest products to complete the solution",
            expected_outcome="List of complementary products",
        ))
        step_num += 1
        
        # Step 5: Format response
        # Step 5: Complete - no tool needed, just mark as complete
        steps.append(PlanStep(
            step_number=step_num,
            action="complete",
            tool="search_products",  # No-op, just return results
            parameters={},
            purpose="Format final recommendation for user",
            expected_outcome="User-friendly recommendation with explanation",
        ))
        
        return steps
    
    def _generate_browse_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for category browsing"""
        steps = []
        
        # Get category
        category = next((c.value for c in constraints if c.name == "category"), None)
        
        steps.append(PlanStep(
            step_number=1,
            action="get_category_products",
            tool="get_category_products",
            parameters={"category": category},
            purpose=f"Get all products in category: {category}",
            expected_outcome="List of products",
        ))
        
        steps.append(PlanStep(
            step_number=2,
            action="format_browse_results",
            tool="search_products",
            parameters={"format": "browse"},
            purpose="Format products for browsing",
            expected_outcome="Browseable product list",
        ))
        
        return steps
    
    def _generate_comparison_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for product comparison"""
        # Extract product targets
        targets = self.intent_classifier.extract_targets(query, Intent.COMPARE_PRODUCTS)
        
        steps = []
        
        for i, target in enumerate(targets[:3], 1):  # Max 3 products
            steps.append(PlanStep(
                step_number=i,
                action=f"get_product_details_{i}",
                tool="get_product_details",
                parameters={"identifier": target},
                purpose=f"Get details for {target}",
                expected_outcome="Product details",
            ))
        
        steps.append(PlanStep(
            step_number=len(steps) + 1,
            action="format_comparison",
            tool="search_products",
            parameters={"format": "comparison"},
            purpose="Format side-by-side comparison",
            expected_outcome="Comparison table with recommendations",
        ))
        
        return steps
    
    def _generate_inquiry_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for product inquiry"""
        targets = self.intent_classifier.extract_targets(query, Intent.PRODUCT_INQUIRY)
        target = targets[0] if targets else query
        
        return [
            PlanStep(
                step_number=1,
                action="get_product_details",
                tool="get_product_details",
                parameters={"identifier": target},
                purpose=f"Get details for {target}",
                expected_outcome="Complete product information",
            ),
            PlanStep(
                step_number=2,
                action="format_product_info",
                tool="search_products",
                parameters={"format": "detailed"},
                purpose="Format product information",
                expected_outcome="Formatted product details",
            ),
        ]
    
    def _generate_review_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for reviewing solution"""
        return [
            PlanStep(
                step_number=1,
                action="get_solution",
                tool="get_solution",
                parameters={},
                purpose="Retrieve current solution",
                expected_outcome="Current solution state",
            ),
            PlanStep(
                step_number=2,
                action="format_solution",
                tool="search_products",
                parameters={"format": "solution_summary"},
                purpose="Format solution for display",
                expected_outcome="Solution summary",
            ),
        ]
    
    def _generate_modify_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for modifying solution"""
        # Determine action (add/remove) and target
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["add", "include"]):
            action = "add"
        elif any(word in query_lower for word in ["remove", "delete", "take out"]):
            action = "remove"
        else:
            action = "unknown"
        
        targets = self.intent_classifier.extract_targets(query, Intent.MODIFY_SOLUTION)
        target = targets[0] if targets else None
        
        return [
            PlanStep(
                step_number=1,
                action=f"{action}_to_solution",
                tool=f"{action}_solution_item",
                parameters={"product_code": target},
                purpose=f"{action.capitalize()} {target} to/from solution",
                expected_outcome=f"Solution updated",
            ),
            PlanStep(
                step_number=2,
                action="check_completeness",
                tool="check_solution_completeness",
                parameters={},
                purpose="Check if solution is complete",
                expected_outcome="Completeness report",
            ),
        ]
    
    def _generate_problem_solving_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps for problem-solving queries"""
        return [
            PlanStep(
                step_number=1,
                action="analyze_problem",
                tool="analyze_query",
                parameters={"query": query},
                purpose="Understand the user's problem",
                expected_outcome="Problem analysis",
            ),
            PlanStep(
                step_number=2,
                action="search_solutions",
                tool="product_search",
                parameters={"query": query, "problem_solving": True},
                purpose="Find products that solve the problem",
                expected_outcome="Relevant solutions",
            ),
            PlanStep(
                step_number=3,
                action="format_solution",
                tool="search_products",
                parameters={"format": "problem_solution"},
                purpose="Present solution with explanation",
                expected_outcome="Problem-solving recommendation",
            ),
        ]
    
    def _generate_clarification_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Generate steps when clarification is needed"""
        return [
            PlanStep(
                step_number=1,
                action="analyze_ambiguity",
                tool="analyze_query",
                parameters={"query": query, "identify_missing": True},
                purpose="Identify what's missing from query",
                expected_outcome="List of clarifying questions",
            ),
            PlanStep(
                step_number=2,
                action="ask_clarification",
                tool="search_products",
                parameters={"format": "clarification"},
                purpose="Ask user for clarification",
                expected_outcome="Clarifying question presented to user",
            ),
        ]
    
    def _generate_default_steps(
        self,
        query: str,
        constraints: List[Constraint]
    ) -> List[PlanStep]:
        """Default steps when intent is unclear"""
        return self._generate_clarification_steps(query, constraints)
    
    def _estimate_tokens(self, steps: List[PlanStep]) -> int:
        """Estimate token usage for plan execution"""
        # Rough estimate: 100 tokens per step
        return len(steps) * 100
    
    def _get_fallback_strategy(self, intent: Intent) -> str:
        """Get fallback strategy for intent"""
        strategies = {
            Intent.RECOMMEND_PRODUCTS: "search_broader_category",
            Intent.BROWSE_CATEGORY: "show_all_products",
            Intent.COMPARE_PRODUCTS: "show_individual_products",
            Intent.PRODUCT_INQUIRY: "search_similar_products",
            Intent.NEEDS_CLARIFICATION: "ask_generic_questions",
        }
        return strategies.get(intent, "ask_for_clarification")
    
    def _is_critical_step(self, plan: Plan, step_number: int) -> bool:
        """Check if a step is critical (failure aborts plan)"""
        # First step is usually critical
        if step_number == 1:
            return True
        # Steps that get product details are critical
        for step in plan.steps:
            if step.step_number == step_number:
                return "get_product" in step.action or "search" in step.action
        return False
    
    def _step_matches_constraints(self, step: PlanStep, constraints: List[Constraint]) -> bool:
        """Check if a step still matches current constraints"""
        # Simplified check - could be more sophisticated
        return True


# Convenience function
def create_plan(query: str, context: Optional[PlanningContext] = None) -> Plan:
    """Quick plan creation"""
    planner = Planner()
    return planner.create_plan(query, context)
