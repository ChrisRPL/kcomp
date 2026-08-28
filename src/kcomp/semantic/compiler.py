import instructor
from ollama import Client
from typing import List, Dict, Any
from kcomp.ir.models import KnowledgeIR, Rule, Condition, Action, ExceptionSpec, Provenance, Predicate, Ambiguity
import re

class SemanticCompiler:
    def __init__(self, model_name: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        # Setup ollama client with instructor
        # Ollama supports tool calling and structured outputs well with llama3.1
        self.client = instructor.from_ollama(
            Client(host=host),
            mode=instructor.Mode.JSON
        )
        self.model_name = model_name

    def segment_document(self, text: str) -> List[Dict[str, Any]]:
        """
        Splits a markdown document into clauses/paragraphs.
        For MVP, we assume clauses are separated by double newlines.
        """
        clauses = []
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        char_idx = 0
        for i, para in enumerate(paragraphs):
            para_len = len(para)
            if para_len > 0:
                clauses.append({
                    "id": f"C{i+1}",
                    "text": para,
                    "start_char": char_idx,
                    "end_char": char_idx + para_len
                })
            # Add len of the paragraph and the two newlines
            char_idx += para_len + 2 
            
        return clauses

    def compile_document(self, document_id: str, text: str) -> KnowledgeIR:
        clauses = self.segment_document(text)
        
        ir = KnowledgeIR(
            document_id=document_id,
            concepts=[],
            definitions=[],
            rules=[],
            ambiguities=[]
        )
        
        # Compile each clause and aggregate
        for clause in clauses:
            clause_ir = self.extract_ir_from_clause(document_id, clause)
            if clause_ir:
                ir.rules.extend(clause_ir.rules)
                ir.concepts.extend(clause_ir.concepts)
                ir.definitions.extend(clause_ir.definitions)
                ir.ambiguities.extend(clause_ir.ambiguities)
                
        return ir

    def extract_ir_from_clause(self, document_id: str, clause: dict) -> KnowledgeIR:
        prompt = f"""
        You are a semantic compiler for formal operational text.
        Your task is NOT to answer the policy question, but to produce a typed intermediate representation.

        Rules:
        1. Preserve the meaning of the source as literally as practical.
        2. Do not infer missing obligations, permissions, prohibitions, consequences, priorities, thresholds, or exceptions.
        3. "Unknown" is not false.
        4. Distinguish MUST/SHALL from MAY and MUST NOT.
        5. For provenance, set document_id="{document_id}", clause_id="{clause['id']}", start_char={clause['start_char']}, end_char={clause['end_char']}, quote=the exact text.

        Source Clause:
        {clause['text']}
        """

        try:
            # We use instructor to extract the KnowledgeIR
            extracted = self.client.chat.completions.create(
                model=self.model_name,
                response_model=KnowledgeIR,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_retries=2
            )
            # Ensure the document_id is correctly set
            extracted.document_id = document_id
            return extracted
        except Exception as e:
            print(f"Failed to extract IR for clause {clause['id']}: {e}")
            return None
