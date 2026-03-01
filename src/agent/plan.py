"""
Plan Data Structures

Defines Plan and PlanStep classes for the Planner.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .intent import Intent
from .constraints import Constraint


class PlanStatus(Enum):
    """Status of a plan or plan step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """
    A single step in an execution plan.
    
    Each step represents one action the agent should take.
    """
    step_number: int
    action: str
    tool: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    purpose: str = ""
    expected_outcome: str = ""
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "step_number": self.step_number,
            "action": self.action,
            "tool": self.tool,
            "parameters": self.parameters,
            "purpose": self.purpose,
            "expected_outcome": self.expected_outcome,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlanStep":
        """Create from dictionary"""
        return cls(
            step_number=data["step_number"],
            action=data["action"],
            tool=data["tool"],
            parameters=data.get("parameters", {}),
            purpose=data.get("purpose", ""),
            expected_outcome=data.get("expected_outcome", ""),
            status=PlanStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            execution_time_ms=data.get("execution_time_ms"),
        )


@dataclass
class Plan:
    """
    A complete execution plan.
    
    Contains the intent, constraints, and ordered steps
    needed to fulfill a user request.
    """
    intent: Intent
    constraints: List[Constraint] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    original_query: str = ""
    estimated_tokens: int = 0
    fallback_strategy: str = ""
    status: PlanStatus = PlanStatus.PENDING
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps"""
        if self.created_at is None:
            from datetime import datetime
            self.created_at = datetime.utcnow().isoformat()
    
    def get_current_step(self) -> Optional[PlanStep]:
        """Get the first pending step"""
        for step in self.steps:
            if step.status == PlanStatus.PENDING:
                return step
        return None
    
    def get_completed_steps(self) -> List[PlanStep]:
        """Get all completed steps"""
        return [s for s in self.steps if s.status == PlanStatus.COMPLETED]
    
    def get_pending_steps(self) -> List[PlanStep]:
        """Get all pending steps"""
        return [s for s in self.steps if s.status == PlanStatus.PENDING]
    
    def mark_step_complete(self, step_number: int, result: Any):
        """Mark a step as completed with result"""
        for step in self.steps:
            if step.step_number == step_number:
                step.status = PlanStatus.COMPLETED
                step.result = result
                break
    
    def mark_step_failed(self, step_number: int, error: str):
        """Mark a step as failed with error"""
        for step in self.steps:
            if step.step_number == step_number:
                step.status = PlanStatus.FAILED
                step.error = error
                break
    
    def is_complete(self) -> bool:
        """Check if all steps are completed or failed"""
        return all(
            s.status in (PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.SKIPPED)
            for s in self.steps
        )
    
    def get_progress(self) -> tuple[int, int]:
        """Get progress as (completed, total)"""
        completed = len([s for s in self.steps if s.status == PlanStatus.COMPLETED])
        return completed, len(self.steps)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "intent": self.intent.value,
            "constraints": [
                {
                    "name": c.name,
                    "value": c.value,
                    "source": c.source.value,
                    "confidence": c.confidence,
                }
                for c in self.constraints
            ],
            "steps": [s.to_dict() for s in self.steps],
            "original_query": self.original_query,
            "estimated_tokens": self.estimated_tokens,
            "fallback_strategy": self.fallback_strategy,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Plan":
        """Create from dictionary"""
        # Import here to avoid circular dependency
        from .constraints import ConstraintSource
        
        constraints = []
        for c in data.get("constraints", []):
            try:
                source_val = c.get("source", "user_explicit")
                if isinstance(source_val, str):
                    try:
                        source = ConstraintSource(source_val)
                    except ValueError:
                        # Unknown source value, default to user_explicit
                        source = ConstraintSource.USER_EXPLICIT
                else:
                    source = ConstraintSource.USER_EXPLICIT
                
                constraints.append(Constraint(
                    name=c["name"],
                    value=c["value"],
                    source=source,
                    confidence=c.get("confidence", 1.0),
                ))
            except (ValueError, KeyError):
                # Skip invalid constraints
                continue
        
        plan = cls(
            intent=Intent(data["intent"]),
            constraints=constraints,
            steps=[PlanStep.from_dict(s) for s in data.get("steps", [])],
            original_query=data.get("original_query", ""),
            estimated_tokens=data.get("estimated_tokens", 0),
            fallback_strategy=data.get("fallback_strategy", ""),
            status=PlanStatus(data.get("status", "pending")),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
        )
        return plan
    
    def __str__(self) -> str:
        """String representation"""
        completed, total = self.get_progress()
        return f"Plan({self.intent.value}, {completed}/{total} steps, status={self.status.value})"


# Import at bottom to avoid circular dependency
