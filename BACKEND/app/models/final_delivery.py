"""Contratos de evidência declarada; nenhuma nota é atribuída automaticamente."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

class Evidence(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    execution_id: str = Field(min_length=1, max_length=100)
    executed_at: str = Field(min_length=1, max_length=100)
    case_id: str = Field(min_length=1, max_length=30)
    release_id: str | None = Field(default=None, max_length=100)
    origin: Literal["t5", "t6", "unknown"] = "unknown"
    purpose: Literal["evaluation", "smoke"] = "evaluation"
    scene_id: str | None = Field(default=None, max_length=30)
    candidate: str = Field(max_length=80)
    mode: Literal["real", "invalid_router", "invalid_specialist"]
    model: str = Field(max_length=100)
    question: str = Field(max_length=2000)
    answer: str = Field(max_length=50000)
    status: str = Field(max_length=100)
    valid: StrictBool
    latency_ms: float = Field(ge=0, le=3600000)
    success: StrictBool | None = None
    critical: StrictBool | None = None
    cost_usd: float | None = Field(default=None, ge=0, le=1000)
    cost_source: str = Field(default="", max_length=1000)
    configuration: dict = Field(default_factory=dict)
    sources: list[dict] = Field(default_factory=list, max_length=20)
    attempts: list[dict] = Field(default_factory=list, max_length=10)
    document: dict | None = None

class HumanReview(BaseModel):
    execution_id: str = Field(min_length=1, max_length=100)
    evaluator: str = Field(min_length=1, max_length=100)
    scores: list[StrictInt] = Field(min_length=7, max_length=7)
    notes: str = Field(min_length=1, max_length=5000)
    recorded_at: str = Field(min_length=1, max_length=100)

class RiskReview(BaseModel):
    id: str = Field(max_length=30)
    owner: str = Field(default="", max_length=100)
    controlled: StrictBool | None = None
    evidence_ids: list[str] = Field(default_factory=list, max_length=40)
    notes: str = Field(default="", max_length=2000)

class FinalDecision(BaseModel):
    choice: Literal["pendente", "aprovado", "aprovado com ressalvas", "reprovado"] = "pendente"
    responsible: str = Field(default="", max_length=100)
    rationale: str = Field(default="", max_length=5000)
    condition: str = Field(default="", max_length=2000)
    owner: str = Field(default="", max_length=100)
    deadline: str = Field(default="", max_length=30)

class DeliveryInput(BaseModel):
    schema_version: int = 1
    release_id: str | None = Field(default=None, max_length=100)
    runs: list[Evidence] = Field(default_factory=list, max_length=200)
    reviews: list[HumanReview] = Field(default_factory=list, max_length=100)
    risks: list[RiskReview] = Field(default_factory=list, max_length=5)
    decision: FinalDecision = Field(default_factory=FinalDecision)
    regression_analysis: str = Field(default="", max_length=5000)
    retrospective: str = Field(default="", max_length=5000)
    contributions: str = Field(default="", max_length=5000)
    demo_team: str = Field(default="", max_length=2000)
    demo_minutes: int | None = Field(default=None, ge=1, le=120)
    rehearsal_notes: str = Field(default="", max_length=5000)
    contingency: str = Field(default="", max_length=2000)

class ExecuteCase(BaseModel):
    case_id: str = Field(max_length=30)
    release_id: str = Field(min_length=1, max_length=100)
    purpose: Literal["evaluation", "smoke"] = "evaluation"
    scene_id: str | None = Field(default=None, max_length=30)
