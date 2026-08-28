from enum import Enum
from typing import Literal, List, Optional
from pydantic import BaseModel, Field

class Modality(str, Enum):
    OBLIGATION = "obligation"
    PERMISSION = "permission"
    PROHIBITION = "prohibition"
    RECOMMENDATION = "recommendation"
    DEFINITION = "definition"
    CLASSIFICATION = "classification"
    PROCEDURAL = "procedural"

class Provenance(BaseModel):
    document_id: str
    clause_id: str
    start_char: int
    end_char: int
    quote: str

class Predicate(BaseModel):
    name: str
    args: List[str]

class Condition(BaseModel):
    id: str
    predicate: Predicate
    polarity: Literal["positive", "negative"] = "positive"
    required_status: Literal["proven", "refuted", "known", "confirmed"] = "proven"
    provenance: List[Provenance]

class Action(BaseModel):
    id: str
    predicate: Predicate
    modality: Modality
    provenance: List[Provenance]

class ExceptionSpec(BaseModel):
    id: str
    condition: Condition
    effect: Literal["defeat_rule", "replace_conclusion", "trigger_review", "unspecified"]
    replacement_action_id: Optional[str] = None
    provenance: List[Provenance]

class Rule(BaseModel):
    id: str
    conditions: List[Condition]
    conclusion: Action
    exceptions: List[ExceptionSpec] = []
    priority: Optional[int] = None
    provenance: List[Provenance]
    confidence: float = Field(ge=0.0, le=1.0)

class Ambiguity(BaseModel):
    id: str
    code: str
    description: str
    related_node_ids: List[str]
    material: bool
    candidate_interpretations: List[str] = []
    provenance: List[Provenance]

class KnowledgeIR(BaseModel):
    document_id: str
    concepts: List[dict]
    definitions: List[dict]
    rules: List[Rule]
    ambiguities: List[Ambiguity]
