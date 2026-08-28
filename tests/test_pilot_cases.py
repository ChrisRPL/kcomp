import pytest
import janus_swi as janus
from knowledge_compiler.ir.models import KnowledgeIR, Rule, Condition, Action, Predicate, Provenance, Modality
from knowledge_compiler.backends.prolog.compiler import PrologCompiler

def build_pilot_ir() -> KnowledgeIR:
    prov = Provenance(document_id="doc_001", clause_id="C0", start_char=0, end_char=0, quote="")
    
    # R1: Permanent Employee if probation ended
    r1 = Rule(
        id="rc1",
        conditions=[
            Condition(id="c1", predicate=Predicate(name="probation_ended", args=["Person"]), provenance=[prov])
        ],
        conclusion=Action(id="a1", predicate=Predicate(name="permanent_employee", args=["Person"]), modality=Modality.CLASSIFICATION, provenance=[prov]),
        confidence=1.0,
        provenance=[prov]
    )
    
    # R2: May work remotely if permanent, manager approved, security training completed
    r2 = Rule(
        id="rc2",
        conditions=[
            Condition(id="c2", predicate=Predicate(name="permanent_employee", args=["Person"]), provenance=[prov]),
            Condition(id="c3", predicate=Predicate(name="manager_approved_remote_work", args=["Person"]), provenance=[prov]),
            Condition(id="c4", predicate=Predicate(name="security_training_completed", args=["Person"]), provenance=[prov])
        ],
        conclusion=Action(id="a2", predicate=Predicate(name="work_remotely", args=["Person"]), modality=Modality.PERMISSION, provenance=[prov]),
        confidence=1.0,
        provenance=[prov]
    )
    
    # R3: Essential staff may not work remotely during scheduled on-site duty
    r3 = Rule(
        id="rc3",
        conditions=[
            Condition(id="c5", predicate=Predicate(name="essential_on_site_staff", args=["Person"]), provenance=[prov]),
            Condition(id="c6", predicate=Predicate(name="scheduled_on_site_duty", args=["Person"]), provenance=[prov])
        ],
        conclusion=Action(id="a3", predicate=Predicate(name="work_remotely", args=["Person"]), modality=Modality.PROHIBITION, provenance=[prov]),
        confidence=1.0,
        provenance=[prov]
    )
    
    # R4: During office emergency, may work remotely
    r4 = Rule(
        id="rc4",
        conditions=[
            Condition(id="c7", predicate=Predicate(name="declared_office_emergency", args=[]), provenance=[prov])
        ],
        conclusion=Action(id="a4", predicate=Predicate(name="work_remotely", args=["Person"]), modality=Modality.PERMISSION, provenance=[prov]),
        confidence=1.0,
        provenance=[prov]
    )
    
    ir = KnowledgeIR(
        document_id="doc_001",
        concepts=[],
        definitions=[],
        rules=[r1, r2, r3, r4],
        ambiguities=[]
    )
    return ir

def setup_prolog():
    # Load core
    janus.query_once("consult('prolog/core.pl')")
    janus.query_once("consult('prolog/truth_status.pl')")
    
    # Compile IR and load
    ir = build_pilot_ir()
    compiler = PrologCompiler(output_dir="prolog/generated")
    path = compiler.compile(ir)
    
    # Manually add the override C5: R4 overrides R3
    compiler.add_override("doc_001", "rc4", "rc3")
    
    janus.query_once(f"consult('{path}')")

def add_fact(case: str, fact: str, val: bool):
    polarity = "positive" if val else "negative"
    janus.query_once(f"assertz(core:case_fact({case}, {fact}, {polarity}))")

def get_status(case: str, prop: str) -> str:
    res = janus.query_once(f"truth_status:status({case}, {prop}, Status)")
    return res["Status"] if res and res.get("truth") else "unknown"

def test_pilot_cases():
    setup_prolog()
    janus.query_once("retractall(core:case_fact(_,_,_))")
    
    # Case 1: Alice (normal, permitted)
    add_fact("alice", "probation_ended(alice)", True)
    add_fact("alice", "manager_approved_remote_work(alice)", True)
    add_fact("alice", "security_training_completed(alice)", True)
    add_fact("alice", "essential_on_site_staff(alice)", False)
    add_fact("alice", "scheduled_on_site_duty(alice)", False)
    add_fact("alice", "declared_office_emergency", False)
    assert get_status("alice", "permission(work_remotely(alice))") == "proven"

    # Case 2: Bob (essential onsite, prohibited)
    add_fact("bob", "probation_ended(bob)", True)
    add_fact("bob", "manager_approved_remote_work(bob)", True)
    add_fact("bob", "security_training_completed(bob)", True)
    add_fact("bob", "essential_on_site_staff(bob)", True)
    add_fact("bob", "scheduled_on_site_duty(bob)", True)
    add_fact("bob", "declared_office_emergency", False)
    assert get_status("bob", "prohibition(work_remotely(bob))") == "conflict"
    assert get_status("bob", "permission(work_remotely(bob))") == "conflict"
    
    # Case 3: Carol (emergency overrides prohibition)
    add_fact("carol", "probation_ended(carol)", True)
    add_fact("carol", "manager_approved_remote_work(carol)", True)
    add_fact("carol", "security_training_completed(carol)", True)
    add_fact("carol", "essential_on_site_staff(carol)", True)
    add_fact("carol", "scheduled_on_site_duty(carol)", True)
    add_fact("carol", "declared_office_emergency", True)
    assert get_status("carol", "permission(work_remotely(carol))") == "proven"
    # The prohibition is refuted because permission is proven and they are mutually exclusive.
    assert get_status("carol", "prohibition(work_remotely(carol))") == "refuted"

    # Case 4: Dave (security training unknown -> unknown permission)
    add_fact("dave", "probation_ended(dave)", True)
    add_fact("dave", "manager_approved_remote_work(dave)", True)
    # No fact about security training (unknown)
    add_fact("dave", "essential_on_site_staff(dave)", False)
    add_fact("dave", "scheduled_on_site_duty(dave)", False)
    add_fact("dave", "declared_office_emergency", False)
    assert get_status("dave", "permission(work_remotely(dave))") == "unknown"

    # Case 5: Eve (contractor -> unknown or refuted)
    add_fact("eve", "contractor(eve)", True)
    add_fact("eve", "equivalent_status_agreement(eve)", False)
    add_fact("eve", "manager_approved_remote_work(eve)", True)
    add_fact("eve", "security_training_completed(eve)", True)
    add_fact("eve", "essential_on_site_staff(eve)", False)
    add_fact("eve", "scheduled_on_site_duty(eve)", False)
    add_fact("eve", "declared_office_emergency", False)
    # Since we haven't modelled R7 in the pilot IR yet, she will just not be proven permanent_employee.
    assert get_status("eve", "permission(work_remotely(eve))") == "unknown"
