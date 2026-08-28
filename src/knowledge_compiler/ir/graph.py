import networkx as nx
from typing import List
from knowledge_compiler.ir.models import KnowledgeIR

class GraphBuilder:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def build_from_ir(self, ir: KnowledgeIR):
        # Add Document node
        self.graph.add_node(ir.document_id, type="Document")

        # Add Concept nodes
        for concept in ir.concepts:
            concept_id = concept.get("id")
            if concept_id:
                self.graph.add_node(concept_id, type="Concept", payload=concept)

        # Add Rules, Conditions, Actions
        for rule in ir.rules:
            rule_id = rule.id
            self.graph.add_node(rule_id, type="Rule", payload=rule.model_dump())
            self.graph.add_edge(ir.document_id, rule_id, type="CONTAINS")

            for condition in rule.conditions:
                cond_id = condition.id
                self.graph.add_node(cond_id, type="Condition", payload=condition.model_dump())
                self.graph.add_edge(rule_id, cond_id, type="REQUIRES")

            action_id = rule.conclusion.id
            self.graph.add_node(action_id, type="Action", payload=rule.conclusion.model_dump())
            self.graph.add_edge(rule_id, action_id, type="IMPLIES")

            for exception in rule.exceptions:
                exc_id = exception.id
                self.graph.add_node(exc_id, type="Exception", payload=exception.model_dump())
                self.graph.add_edge(rule_id, exc_id, type="EXCEPTS")

            if rule.priority is not None:
                # Assuming priority references are handled separately or we add an explicit property
                pass

        # Add Ambiguities
        for ambiguity in ir.ambiguities:
            ambig_id = ambiguity.id
            self.graph.add_node(ambig_id, type="Ambiguity", payload=ambiguity.model_dump())
            for related_node in ambiguity.related_node_ids:
                self.graph.add_edge(related_node, ambig_id, type="HAS_AMBIGUITY")

    def get_graph(self) -> nx.MultiDiGraph:
        return self.graph

    def persist_to_db(self, db, document_id: str):
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("type", "Unknown")
            payload = data.get("payload", {})
            db.insert_node(node_id, document_id, node_type, payload)

        for src, tgt, key, data in self.graph.edges(keys=True, data=True):
            edge_type = data.get("type", "Unknown")
            payload = data.get("payload", {})
            # Using a hash or composite key for edge ID
            edge_id = f"{src}_{tgt}_{edge_type}_{key}"
            db.insert_edge(edge_id, src, tgt, edge_type, payload)
