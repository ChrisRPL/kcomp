from enum import Enum
from typing import Literal

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
    args: list[str]


class Condition(BaseModel):
    id: str
    predicate: Predicate
    polarity: Literal["positive", "negative"] = "positive"
    required_status: Literal["proven", "refuted", "known", "confirmed"] = "proven"
    provenance: list[Provenance]


class Action(BaseModel):
    id: str
    predicate: Predicate
    modality: Modality
    provenance: list[Provenance]


class ExceptionSpec(BaseModel):
    id: str
    condition: Condition
    effect: Literal[
        "defeat_rule", "replace_conclusion", "trigger_review", "unspecified"
    ]
    replacement_action_id: str | None = None
    provenance: list[Provenance]


class Rule(BaseModel):
    id: str
    conditions: list[Condition]
    conclusion: Action
    exceptions: list[ExceptionSpec] = []
    priority: int | None = None
    provenance: list[Provenance]
    confidence: float = Field(ge=0.0, le=1.0)


class Ambiguity(BaseModel):
    id: str
    code: str
    description: str
    related_node_ids: list[str]
    material: bool
    candidate_interpretations: list[str] = []
    provenance: list[Provenance]


class KnowledgeIR(BaseModel):
    document_id: str
    concepts: list[dict]
    definitions: list[dict]
    rules: list[Rule]
    ambiguities: list[Ambiguity]
