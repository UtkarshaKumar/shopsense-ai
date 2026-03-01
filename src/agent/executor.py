"""
Executor - Runs plan steps using tools

Executes plans step by step and collects results.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time

from .plan import Plan, PlanStep, PlanStatus
from .tools import ToolRegistry, ToolResult


@dataclass
class ExecutionResult:
    """Result of executing a plan"""
    success: bool
    plan: Plan
    steps_completed: int
    steps_failed: int
    final_response: str = ""
    error: Optional[str] = None
    execution_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "final_response": self.final_response,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


class PlanExecutor:
    """Executes plans step by step"""
    
    def __init__(self, tools: ToolRegistry):
        self.tools = tools
        self.step_hooks: List[Callable] = []
    
    def add_step_hook(self, hook: Callable):
        """Add a callback for step execution"""
        self.step_hooks.append(hook)
    
    def execute_plan(
        self,
        plan: Plan,
        context: Optional[Dict] = None
    ) -> ExecutionResult:
        """
        Execute all steps in a plan.
        
        Args:
            plan: The plan to execute
            context: Optional execution context
            
        Returns:
            ExecutionResult with completion status
        """
        start_time = time.time()
        context = context or {}
        
        plan.status = PlanStatus.IN_PROGRESS
        
        completed = 0
        failed = 0
        
        for step in plan.steps:
            if step.status == PlanStatus.PENDING:
                result = self._execute_step(step, context)
                
                if result.success:
                    completed += 1
                else:
                    failed += 1
                    
                    # Check if critical step failed
                    if self._is_critical_failure(step, plan):
                        plan.status = PlanStatus.FAILED
                        break
        
        # Determine final status
        if plan.status != PlanStatus.FAILED:
            if failed == 0:
                plan.status = PlanStatus.COMPLETED
            elif completed > 0:
                plan.status = PlanStatus.COMPLETED  # Partial success
            else:
                plan.status = PlanStatus.FAILED
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return ExecutionResult(
            success=plan.status == PlanStatus.COMPLETED,
            plan=plan,
            steps_completed=completed,
            steps_failed=failed,
            final_response=self._generate_response(plan),
            execution_time_ms=execution_time,
        )
    
    def execute_step(
        self,
        plan: Plan,
        step_number: int,
        context: Optional[Dict] = None
    ) -> ToolResult:
        """
        Execute a single step in a plan.
        
        Args:
            plan: The plan containing the step
            step_number: Which step to execute
            context: Optional execution context
            
        Returns:
            ToolResult from step execution
        """
        step = None
        for s in plan.steps:
            if s.step_number == step_number:
                step = s
                break
        
        if not step:
            return ToolResult(
                success=False,
                data=None,
                error=f"Step {step_number} not found"
            )
        
        return self._execute_step(step, context or {})
    
    def _execute_step(
        self,
        step: PlanStep,
        context: Dict
    ) -> ToolResult:
        """Execute a single step"""
        step.status = PlanStatus.IN_PROGRESS
        start_time = time.time()
        
        try:
            # Execute the tool
            result = self.tools.execute(step.tool, step.parameters)
            
            execution_time = int((time.time() - start_time) * 1000)
            step.execution_time_ms = execution_time
            
            if result.success:
                step.status = PlanStatus.COMPLETED
                step.result = result.data
            else:
                step.status = PlanStatus.FAILED
                step.error = result.error
            
            # Call hooks
            for hook in self.step_hooks:
                hook(step, result)
            
            return result
            
        except Exception as e:
            step.status = PlanStatus.FAILED
            step.error = str(e)
            step.execution_time_ms = int((time.time() - start_time) * 1000)
            
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _is_critical_failure(self, step: PlanStep, plan: Plan) -> bool:
        """Check if a step failure is critical"""
        # First step failure is usually critical
        if step.step_number == 1:
            return True
        # Product lookup failures are critical
        if "get_product" in step.action or "search" in step.action:
            return True
        return False
    
    def _generate_response(self, plan: Plan) -> str:
        """Generate a human-readable response from plan execution"""
        if plan.status == PlanStatus.FAILED:
            # Find first failed step
            for step in plan.steps:
                if step.status == PlanStatus.FAILED:
                    return f"I encountered an issue while trying to {step.action}: {step.error or 'Unknown error'}"
            return "I'm sorry, I couldn't complete your request due to an unexpected issue."
        
        # Generate success response based on intent
        if plan.intent.value == "recommend_products":
            return self._format_recommendation_response(plan)
        elif plan.intent.value == "browse_category":
            return self._format_browse_response(plan)
        elif plan.intent.value == "compare_products":
            return self._format_comparison_response(plan)
        elif plan.intent.value == "product_inquiry":
            return self._format_inquiry_response(plan)
        elif plan.intent.value == "review_solution":
            return self._format_solution_response(plan)
        else:
            return "I've processed your request. Is there anything else you'd like to know?"
    
    def _format_recommendation_response(self, plan: Plan) -> str:
        """Format recommendation response"""
        for step in plan.steps:
            if step.action == "search_products" and step.result and isinstance(step.result, list):
                products = step.result
                if products:
                    names = [p.name for p in products[:3]]
                    count = len(products)
                    query = plan.original_query.lower()
                    # Extract space constraint if present
                    space_ctx = ""
                    for c in plan.constraints:
                        if c.name == "space":
                            space_ctx = f" for your {c.value:,} sq ft space"
                            break
                    cat_ctx = ""
                    for c in plan.constraints:
                        if c.name == "category":
                            cat_ctx = f" in the {c.value} category"
                            break
                    return (
                        f"I've found {count} product{'s' if count != 1 else ''}{space_ctx}{cat_ctx}. "
                        f"My top picks are: **{names[0]}**"
                        + (f", {names[1]}" if len(names) > 1 else "")
                        + (f", and {names[2]}" if len(names) > 2 else "")
                        + ". You can add them to your solution bundle on the right, or ask me to compare options."
                    )
        return (
            "I've curated a set of products based on your requirements. "
            "Explore the recommendations on the right — click any card to see full specs, "
            "or ask me to narrow down by budget, capacity, or features."
        )

    def _format_browse_response(self, plan: Plan) -> str:
        """Format browse response"""
        for step in plan.steps:
            if step.result and isinstance(step.result, list):
                products = step.result
                if products:
                    category = products[0].category.value.title() if products else "this category"
                    return (
                        f"Here are {len(products)} {category} products available. "
                        f"Use the category tabs on the right to filter further, "
                        f"or ask me to recommend the best fit for your setup."
                    )
        return "Here are the products I found. Use the tabs to filter by category."

    def _format_comparison_response(self, plan: Plan) -> str:
        """Format comparison response"""
        products = []
        for step in plan.steps:
            if "get_product" in step.action and step.result and hasattr(step.result, "sku"):
                products.append(step.result)

        if len(products) >= 2:
            p1, p2 = products[0], products[1]
            price_diff = abs((p1.price or 0) - (p2.price or 0))
            cheaper = p1 if (p1.price or 0) < (p2.price or 0) else p2
            pricier = p2 if cheaper == p1 else p1
            return (
                f"Comparing **{p1.name}** vs **{p2.name}**: "
                f"The {cheaper.name} is ${price_diff:,.0f} less expensive. "
                f"Both products are displayed on the right with full specs. "
                f"Would you like me to highlight specific differences, like capacity or noise levels?"
            )
        elif len(products) == 1:
            return f"I found **{products[0].name}**. Could you clarify the second product to compare it against?"
        return "I couldn't locate those products. Could you provide the product names or SKUs?"

    def _format_inquiry_response(self, plan: Plan) -> str:
        """Format product inquiry response"""
        for step in plan.steps:
            if step.action == "get_product_details" and step.result and hasattr(step.result, "name"):
                product = step.result
                price_str = f"${product.price:,.0f}" if product.price else "pricing on request"
                stock_str = "in stock" if product.in_stock else "currently out of stock"
                return (
                    f"**{product.name}** ({product.sku}) — {price_str}, {stock_str}. "
                    f"{product.description[:120]}... "
                    f"Full specs are shown in the product panel. Would you like to add it to your solution?"
                )
        return "Here are the product details you requested. Check the right panel for full specifications."

    def _format_solution_response(self, plan: Plan) -> str:
        """Format solution review response"""
        for step in plan.steps:
            if step.action == "get_solution" and step.result is not None:
                items = step.result
                if items:
                    return (
                        f"Your current solution has **{len(items)} item{'s' if len(items) != 1 else ''}**. "
                        f"The solution bundle is shown at the bottom of the product panel. "
                        f"Would you like me to check completeness or suggest complementary products?"
                    )
                else:
                    return (
                        "Your solution is currently empty. "
                        "Ask me to recommend products for your data center, or browse by category and click "
                        "\"+ Add to Solution\" on any product card."
                    )
        return "Here's your current solution overview — check the bundle panel below the product grid."
