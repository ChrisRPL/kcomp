from typing import Literal

import instructor
from ollama import Client
from pydantic import BaseModel, Field


class Fact(BaseModel):
    case_id: str
    predicate: str = Field(
        description="The name of the predicate, e.g. 'permanent_employee'"
    )
    args: list[str] = Field(
        description="The arguments, typically the case subject, e.g. ['alice']"
    )
    polarity: Literal["positive", "negative"] = Field(
        description="Whether the fact is explicitly true (positive) or explicitly false (negative)"
    )


class CaseFacts(BaseModel):
    case_id: str
    facts: list[Fact]


class CaseParser:
    def __init__(
        self, model_name: str = "llama3.1:8b", host: str = "http://localhost:11434"
    ):
        self.client = instructor.from_ollama(
            Client(host=host), mode=instructor.Mode.JSON
        )
        self.model_name = model_name

    def parse_case(
        self,
        case_id: str,
        case_text: str,
        context_predicates: list[str] | None = None,
    ) -> CaseFacts:
        pred_hint = ""
        if context_predicates:
            pred_hint = f"\nFor context, the policy uses these predicates: {', '.join(context_predicates)}\nTry to use these if they match."

        prompt = f"""
        You are a Case Fact Extractor. Extract the explicit facts from the given case text.
        Do not infer unstated facts. If something is unknown, do not output it as negative.
        {pred_hint}
        
        Case ID: {case_id}
        Case Text:
        {case_text}
        """

        try:
            extracted = self.client.chat.completions.create(
                model=self.model_name,
                response_model=CaseFacts,
                messages=[{"role": "user", "content": prompt}],
                max_retries=2,
            )
            # Ensure case_id is consistent
            extracted.case_id = case_id
            for f in extracted.facts:
                f.case_id = case_id
            return extracted
        except Exception as e:
            print(f"Failed to extract facts for case {case_id}: {e}")
            return CaseFacts(case_id=case_id, facts=[])
