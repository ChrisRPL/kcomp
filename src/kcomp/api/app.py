import os

import janus_swi as janus
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from ollama import Client
from pydantic import BaseModel

from kcomp.backends.prolog.compiler import PrologCompiler
from kcomp.runtime.case_parser import CaseParser
from kcomp.semantic.compiler import SemanticCompiler

app = FastAPI(title="Knowledge Compiler API")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


class CompileRequest(BaseModel):
    document_id: str
    text: str


class CompileResponse(BaseModel):
    success: bool
    ir_json: str
    prolog_code: str


@app.post("/api/compile", response_model=CompileResponse)
def compile_policy(req: CompileRequest):
    sem_comp = SemanticCompiler()
    try:
        # Extract IR
        ir = sem_comp.compile_document(req.document_id, req.text)
        # Compile to Prolog
        prolog_comp = PrologCompiler(ir)
        prolog_code = prolog_comp.compile()
        # Save to file
        os.makedirs("src/kcomp/prolog/generated", exist_ok=True)
        file_path = f"src/kcomp/prolog/generated/{req.document_id}.pl"
        with open(file_path, "w") as f:
            f.write(prolog_code)

        return CompileResponse(
            success=True, ir_json=ir.model_dump_json(indent=2), prolog_code=prolog_code
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ReasonRequest(BaseModel):
    case_id: str
    scenario_text: str
    document_id: str
    context_predicates: list[str] = []


class ReasonResponse(BaseModel):
    status: str
    trace_positive: str | None
    trace_negative: str | None
    extracted_proposition: str | None
    extracted_facts: list[dict]

@app.post("/api/reason", response_model=ReasonResponse)
def reason(req: ReasonRequest):
    # Setup prolog
    janus.query_once("consult('src/kcomp/prolog/core.pl')")
    janus.query_once("consult('src/kcomp/prolog/truth_status.pl')")
    janus.query_once(f"consult('src/kcomp/prolog/generated/{req.document_id}.pl')")

    # Parse facts and proposition
    parser = CaseParser()
    case_facts = parser.parse_case(req.case_id, req.scenario_text, req.context_predicates)
    
    proposition = case_facts.proposition_to_prove
    if not proposition:
        proposition = "unknown_proposition"

    # Load facts into Prolog
    janus.query_once("retractall(core:case_fact(_,_,_))")
    for fact in case_facts.facts:
        args_str = f"({', '.join(fact.args)})" if fact.args else ""
        fact_term = f"{fact.predicate}{args_str}"
        janus.query_once(
            f"assertz(core:case_fact({fact.case_id}, {fact_term}, {fact.polarity}))"
        )

    # Evaluate
    res = janus.query_once(
        f"truth_status:truth_status({req.case_id}, {proposition}, Result)"
    )

    if res and "Result" in res:
        result_dict = res["Result"]
        return ReasonResponse(
            status=result_dict.get("status", "unknown"),
            trace_positive=result_dict.get("trace_positive"),
            trace_negative=result_dict.get("trace_negative"),
            extracted_proposition=proposition,
            extracted_facts=[f.model_dump() for f in case_facts.facts]
        )

    return ReasonResponse(status="unknown", trace_positive=None, trace_negative=None, extracted_proposition=proposition, extracted_facts=[f.model_dump() for f in case_facts.facts])


class BaselineRequest(BaseModel):
    policy_text: str
    scenario_text: str


class BaselineResponse(BaseModel):
    answer: str


@app.post("/api/reason_baseline", response_model=BaselineResponse)
def reason_baseline(req: BaselineRequest):
    client = Client(host="http://localhost:11434")
    prompt = f"""
    Given the following policy:
    {req.policy_text}
    
    And the following scenario and question:
    {req.scenario_text}
    
    Determine if the action asked about in the scenario is permitted/obligated/prohibited according to the policy.
    
    Provide your reasoning, and then conclude with STATUS: [PROVEN/REFUTED/UNKNOWN/CONFLICT].
    """
    try:
        response = client.chat(
            model="llama3.1:8b", messages=[{"role": "user", "content": prompt}]
        )
        return BaselineResponse(answer=response["message"]["content"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
