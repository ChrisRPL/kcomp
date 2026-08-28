import sqlite3
import json
from typing import List, Dict, Any

class GraphDatabase:
    def __init__(self, db_path: str = "knowledge.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    node_type TEXT,
                    payload TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT,
                    target_id TEXT,
                    edge_type TEXT,
                    payload TEXT
                )
            """)

    def insert_node(self, node_id: str, document_id: str, node_type: str, payload: dict):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO nodes (id, document_id, node_type, payload) VALUES (?, ?, ?, ?)",
                (node_id, document_id, node_type, json.dumps(payload))
            )

    def insert_edge(self, edge_id: str, source_id: str, target_id: str, edge_type: str, payload: dict = None):
        if payload is None:
            payload = {}
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO edges (id, source_id, target_id, edge_type, payload) VALUES (?, ?, ?, ?, ?)",
                (edge_id, source_id, target_id, edge_type, json.dumps(payload))
            )

    def get_nodes(self, document_id: str = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM nodes"
        params = ()
        if document_id:
            query += " WHERE document_id = ?"
            params = (document_id,)
        
        cursor = self.conn.execute(query, params)
        nodes = []
        for row in cursor:
            node = dict(row)
            node["payload"] = json.loads(node["payload"])
            nodes.append(node)
        return nodes

    def get_edges(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM edges")
        edges = []
        for row in cursor:
            edge = dict(row)
            edge["payload"] = json.loads(edge["payload"])
            edges.append(edge)
        return edges
