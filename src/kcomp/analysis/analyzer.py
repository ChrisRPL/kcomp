import networkx as nx
from typing import List, Dict, Any
from kcomp.ir.models import KnowledgeIR

class StaticAnalyzer:
    def __init__(self, ir: KnowledgeIR):
        self.ir = ir
        self.warnings: List[str] = []

    def analyze(self) -> List[str]:
        self.warnings = []
        self._check_undefined_concepts()
        self._check_cycles()
        return self.warnings

    def _check_undefined_concepts(self):
        # Gather all defined concept names
        defined_names = set(c.name for c in self.ir.concepts)
        defined_names.update(d.name for d in self.ir.definitions)
        
        # Also any predicate derived by a rule is technically defined
        defined_names.update(r.conclusion.predicate.name for r in self.ir.rules)

        for rule in self.ir.rules:
            # Check conditions
            for cond in rule.conditions:
                if cond.predicate.name not in defined_names:
                    self.warnings.append(f"Undefined concept '{cond.predicate.name}' in condition of rule {rule.id}")
            
            # Check conclusion
            if rule.conclusion.predicate.name not in defined_names:
                self.warnings.append(f"Undefined concept '{rule.conclusion.predicate.name}' in conclusion of rule {rule.id}")
            
            # Check exceptions
            for exc in rule.exceptions:
                if exc.condition.predicate.name not in defined_names:
                    self.warnings.append(f"Undefined concept '{exc.condition.predicate.name}' in exception of rule {rule.id}")


    def _check_cycles(self):
        # Build dependency graph
        # Node: Rule ID
        # Edge: Rule A -> Rule B (if Rule A's conclusion is used in Rule B's condition)
        
        # Map predicate name -> list of rule IDs that derive it
        derivation_map = {}
        for r in self.ir.rules:
            pred = r.conclusion.predicate.name
            derivation_map.setdefault(pred, []).append(r.id)
            
        G = nx.DiGraph()
        for r in self.ir.rules:
            G.add_node(r.id)
            
        for rule in self.ir.rules:
            for cond in rule.conditions:
                pred = cond.predicate.name
                if pred in derivation_map:
                    for derived_by_rule in derivation_map[pred]:
                        # derived_by_rule -> rule
                        G.add_edge(derived_by_rule, rule.id)
        
        try:
            cycle = nx.find_cycle(G, orientation="original")
            cycle_nodes = [u for u, v, d in cycle]
            self.warnings.append(f"Dependency cycle detected among rules: {' -> '.join(cycle_nodes)}")
        except nx.NetworkXNoCycle:
            pass
