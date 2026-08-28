from kcomp.analysis.analyzer import StaticAnalyzer
from kcomp.ir.models import (
    Action,
    Condition,
    ExceptionSpec,
    KnowledgeIR,
    Modality,
    Predicate,
    Provenance,
    Rule,
)


def build_test_ir() -> KnowledgeIR:
    prov = Provenance(
        document_id="d1", clause_id="c1", start_char=0, end_char=0, quote=""
    )

    r1 = Rule(
        id="r1",
        conditions=[
            Condition(
                id="c1", predicate=Predicate(name="b", args=[]), provenance=[prov]
            )
        ],
        conclusion=Action(
            id="a1",
            predicate=Predicate(name="a", args=[]),
            modality=Modality.CLASSIFICATION,
            provenance=[prov],
        ),
        confidence=1.0,
        provenance=[prov],
        exceptions=[
            ExceptionSpec(
                id="e1_spec",
                effect="defeat_rule",
                condition=Condition(
                    id="e1",
                    predicate=Predicate(name="unknown_pred", args=[]),
                    provenance=[prov],
                ),
                provenance=[prov],
            )
        ],
    )

    r2 = Rule(
        id="r2",
        conditions=[
            Condition(
                id="c2", predicate=Predicate(name="a", args=[]), provenance=[prov]
            )
        ],
        conclusion=Action(
            id="a2",
            predicate=Predicate(name="b", args=[]),
            modality=Modality.CLASSIFICATION,
            provenance=[prov],
        ),
        confidence=1.0,
        provenance=[prov],
    )

    return KnowledgeIR(
        document_id="d1", concepts=[], definitions=[], rules=[r1, r2], ambiguities=[]
    )


def test_static_analyzer():
    ir = build_test_ir()
    analyzer = StaticAnalyzer(ir)
    warnings = analyzer.analyze()

    # We expect:
    # 1. Undefined concept 'unknown_pred'
    # 2. Cycle a -> b -> a (r2 -> r1 -> r2)

    assert any("unknown_pred" in w for w in warnings)
    assert any("cycle" in w.lower() for w in warnings)
    assert len(warnings) == 2
