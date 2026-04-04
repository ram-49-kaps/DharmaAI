"""
Dharma Knowledge Graph (DKG)
─────────────────────────────
An in‑memory knowledge graph mapping the conceptual relationships
between Indian Knowledge System (IKS) concepts, modern Indian law,
and key legal principles.

The graph is used to *enrich* RAG context — when a user query matches
a node, the graph returns semantically related concepts that would
be missed by pure vector‑similarity search.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional


# ── Data structures ─────────────────────────────────────────────────

@dataclass
class KGNode:
    """A concept in the Dharma Knowledge Graph."""
    id: str
    label: str
    category: str          # "iks", "modern_law", "legal_principle", "framework"
    description: str = ""
    era: str = ""          # e.g. "ancient", "colonial", "contemporary"
    source_text: str = ""  # canonical source

    def to_context(self) -> str:
        """Return a concise text snippet for RAG enrichment."""
        parts = [f"{self.label} ({self.category})"]
        if self.description:
            parts.append(self.description)
        if self.source_text:
            parts.append(f"Source: {self.source_text}")
        return " — ".join(parts)


@dataclass
class KGEdge:
    """A directed relationship between two KG nodes."""
    source: str
    target: str
    relation: str          # e.g. "source_of", "modern_equivalent", "enforced_by"
    description: str = ""


# ── THE GRAPH ───────────────────────────────────────────────────────

class DharmaKnowledgeGraph:
    """
    Pre‑populated knowledge graph of IKS ↔ Modern Law relationships.
    Designed for fast in‑memory lookups — no external DB needed.
    """

    def __init__(self):
        self._nodes: Dict[str, KGNode] = {}
        self._edges: List[KGEdge] = []
        self._adjacency: Dict[str, List[KGEdge]] = {}
        self._reverse:   Dict[str, List[KGEdge]] = {}
        self._build()

    # ── Internal builder ────────────────────────────────────────────

    def _add_node(self, node: KGNode):
        self._nodes[node.id] = node

    def _add_edge(self, edge: KGEdge):
        self._edges.append(edge)
        self._adjacency.setdefault(edge.source, []).append(edge)
        self._reverse.setdefault(edge.target, []).append(edge)

    def _build(self):
        # ── IKS CONCEPTS ────────────────────────────────────────────
        self._add_node(KGNode(
            id="dharma", label="Dharma", category="iks",
            description="The universal moral law — righteous duty governing individual "
                        "conduct and social order. It is the foundational concept of "
                        "Indian jurisprudence, encompassing ethical, moral, and legal obligations.",
            era="ancient", source_text="Dharmaśāstras (Manu, Yājñavalkya, Nārada)"
        ))
        self._add_node(KGNode(
            id="danda", label="Danda", category="iks",
            description="Literally 'rod' or 'punishment'. The Kautilyan theory of "
                        "state-sanctioned sanction — the coercive power of the state "
                        "used to enforce Dharma and maintain social order. Four types: "
                        "verbal censure, fine, corporal punishment, death penalty.",
            era="ancient", source_text="Arthashastra, Book IV (Kautilya)"
        ))
        self._add_node(KGNode(
            id="purushartha", label="Puruṣārtha", category="iks",
            description="The four aims of human life — Dharma (righteousness), Artha "
                        "(material wealth), Kama (desire), Moksha (liberation). Together "
                        "they form a situational ethics framework. Daya Krishna's model "
                        "argues these are evolving and contextual, not fixed hierarchy.",
            era="ancient", source_text="Vedic / Upanishadic tradition; Daya Krishna's reinterpretation"
        ))
        self._add_node(KGNode(
            id="arthashastra", label="Arthashastra", category="iks",
            description="Ancient Indian treatise on statecraft by Kautilya (c. 3rd century BCE). "
                        "Contains detailed provisions on Danda (punishment), taxation, trade "
                        "regulation, contracts, property, inheritance, and judicial procedure.",
            era="ancient", source_text="Kautilya, Arthashastra"
        ))
        self._add_node(KGNode(
            id="dharmashastra", label="Dharmaśāstra", category="iks",
            description="Ancient legal treatises codifying Dharma-based law. Manusmriti "
                        "(c. 200 BCE–200 CE), Yajnavalkyasmriti (c. 100–300 CE), "
                        "Naradasmriti (procedural law). Four sources: Sruti, Smriti, "
                        "Sadachara, Atmatushti.",
            era="ancient", source_text="Manusmriti, Yajnavalkyasmriti, Naradasmriti"
        ))
        self._add_node(KGNode(
            id="nyaya", label="Nyāya (Justice)", category="iks",
            description="Indian philosophical concept of justice and logical reasoning. "
                        "Nyaya Shastra provides the logical framework for legal argumentation "
                        "in classical Indian jurisprudence.",
            era="ancient", source_text="Nyaya Sutras (Gautama)"
        ))

        # ── LEGAL FRAMEWORKS ────────────────────────────────────────
        self._add_node(KGNode(
            id="irac", label="IRAC", category="framework",
            description="Issue–Rule–Application–Conclusion. Standard Western legal "
                        "reasoning framework for structured case analysis.",
            era="contemporary", source_text="Legal education standard"
        ))
        self._add_node(KGNode(
            id="idar", label="IDAR", category="framework",
            description="Issue–Dharma–Application of Danda–Resolution. Dharma-based "
                        "variant of IRAC that bridges ancient Indian jurisprudence with "
                        "modern legal analysis. Uses Dharma as the applicable rule and "
                        "Danda as the sanction mechanism.",
            era="contemporary", source_text="DharmaAI IKS integration"
        ))

        # ── MODERN INDIAN LAW ──────────────────────────────────────
        self._add_node(KGNode(
            id="article21", label="Article 21", category="modern_law",
            description="Right to Life and Personal Liberty — 'No person shall be "
                        "deprived of his life or personal liberty except according to "
                        "procedure established by law.' Interpreted expansively to include "
                        "right to livelihood, privacy, dignity, education.",
            era="contemporary", source_text="Constitution of India, Part III"
        ))
        self._add_node(KGNode(
            id="article14", label="Article 14", category="modern_law",
            description="Equality before law — the State shall not deny to any person "
                        "equality before the law or equal protection of the laws.",
            era="contemporary", source_text="Constitution of India, Part III"
        ))
        self._add_node(KGNode(
            id="basic_structure", label="Basic Structure Doctrine", category="legal_principle",
            description="Parliament can amend the Constitution but cannot alter its "
                        "Basic Structure — judicial review, separation of powers, "
                        "federalism, secularism are inviolable.",
            era="contemporary", source_text="Kesavananda Bharati v. State of Kerala (1973)"
        ))
        self._add_node(KGNode(
            id="due_process", label="Due Process", category="legal_principle",
            description="Any law depriving life or liberty must be just, fair, and "
                        "reasonable — both substantive and procedural due process. "
                        "Articles 14, 19, 21 form a 'golden triangle'.",
            era="contemporary", source_text="Maneka Gandhi v. Union of India (1978)"
        ))
        self._add_node(KGNode(
            id="ipc", label="Indian Penal Code 1860", category="modern_law",
            description="India's principal criminal code defining offences and "
                        "punishments. Replaced by Bharatiya Nyaya Sanhita 2023.",
            era="colonial", source_text="Act No. 45 of 1860"
        ))
        self._add_node(KGNode(
            id="bns", label="Bharatiya Nyaya Sanhita 2023", category="modern_law",
            description="Replaces the IPC. Modernises criminal law, introduces "
                        "organised crime, terrorism provisions. Aligns with "
                        "constitutional values.",
            era="contemporary", source_text="Act No. 45 of 2023"
        ))
        self._add_node(KGNode(
            id="ica", label="Indian Contract Act 1872", category="modern_law",
            description="Governs the law of contracts — offer, acceptance, "
                        "consideration, capacity, free consent, and remedies.",
            era="colonial", source_text="Act No. 9 of 1872"
        ))
        self._add_node(KGNode(
            id="mens_rea", label="Mens Rea", category="legal_principle",
            description="'Guilty mind' — the criminal intent or knowledge of "
                        "wrongdoing. Most criminal offences require both Actus Reus "
                        "and Mens Rea.",
            era="colonial", source_text="Common law / IPC"
        ))
        self._add_node(KGNode(
            id="stare_decisis", label="Stare Decisis", category="legal_principle",
            description="Doctrine of precedent — courts must follow earlier decisions "
                        "of higher courts on the same point of law.",
            era="contemporary", source_text="Judicial practice"
        ))

        # ── RELATIONSHIPS ───────────────────────────────────────────

        # Dharma relationships
        self._add_edge(KGEdge("dharma", "danda",
            "enforced_by", "Danda is the instrument of enforcement for Dharma"))
        self._add_edge(KGEdge("dharma", "purushartha",
            "component_of", "Dharma is the first of the four Puruṣārthas"))
        self._add_edge(KGEdge("dharma", "dharmashastra",
            "codified_in", "Dharma is codified in the Dharmaśāstras"))
        self._add_edge(KGEdge("dharma", "article21",
            "modern_equivalent", "Dharma's duty-of-care maps to Article 21's right to life with dignity"))
        self._add_edge(KGEdge("dharma", "article14",
            "modern_equivalent", "Dharma's concept of Samata (equality) maps to Article 14"))
        self._add_edge(KGEdge("dharma", "idar",
            "applied_through", "Dharma is used as the 'Rule' step in the IDAR framework"))

        # Danda relationships
        self._add_edge(KGEdge("danda", "arthashastra",
            "detailed_in", "Arthashastra Book IV provides the theory of Danda"))
        self._add_edge(KGEdge("danda", "ipc",
            "modern_equivalent", "IPC's punishment framework is the modern form of Danda"))
        self._add_edge(KGEdge("danda", "bns",
            "modern_equivalent", "BNS 2023 modernises the Danda framework"))
        self._add_edge(KGEdge("danda", "idar",
            "applied_through", "Danda is used as the 'Application' step in IDAR"))
        self._add_edge(KGEdge("danda", "mens_rea",
            "requires", "Danda (punishment) in Arthashastra also considers intent"))

        # Puruṣārtha relationships
        self._add_edge(KGEdge("purushartha", "dharma",
            "includes", "Dharma (righteousness) is the first aim"))
        self._add_edge(KGEdge("purushartha", "ica",
            "contextualises", "Artha (wealth) aim connects to contract law"))
        self._add_edge(KGEdge("purushartha", "basic_structure",
            "philosophically_grounds", "Puruṣārtha's holistic ethics parallels constitutional morality"))

        # Arthashastra relationships
        self._add_edge(KGEdge("arthashastra", "dharma",
            "operationalises", "Arthashastra operationalises Dharma through state machinery"))
        self._add_edge(KGEdge("arthashastra", "ica",
            "precursor_of", "Book III covers contracts, property — precursor to ICA"))

        # Framework relationships
        self._add_edge(KGEdge("irac", "idar",
            "variant_of", "IDAR is a Dharma-based variant of IRAC"))
        self._add_edge(KGEdge("idar", "dharma",
            "uses", "IDAR uses Dharma as the applicable rule"))
        self._add_edge(KGEdge("idar", "danda",
            "uses", "IDAR applies Danda as the sanction mechanism"))

        # Modern law cross-links
        self._add_edge(KGEdge("basic_structure", "article21",
            "protects", "Basic Structure Doctrine protects fundamental rights"))
        self._add_edge(KGEdge("due_process", "article21",
            "interprets", "Due process gives substantive meaning to Article 21"))
        self._add_edge(KGEdge("ipc", "bns",
            "replaced_by", "IPC 1860 replaced by BNS 2023"))
        self._add_edge(KGEdge("stare_decisis", "basic_structure",
            "established", "Basic Structure is binding precedent via stare decisis"))
        self._add_edge(KGEdge("dharmashastra", "nyaya",
            "complemented_by", "Nyāya provides logical reasoning for Dharmaśāstra jurisprudence"))

    # ── Public query API ────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[KGNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[KGNode]:
        return list(self._nodes.values())

    def get_related(self, node_id: str, max_depth: int = 2) -> List[KGNode]:
        """BFS traversal to find related concepts up to max_depth hops."""
        if node_id not in self._nodes:
            return []

        visited: Set[str] = {node_id}
        queue: List[tuple] = [(node_id, 0)]
        related: List[KGNode] = []

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Outgoing edges
            for edge in self._adjacency.get(current, []):
                if edge.target not in visited:
                    visited.add(edge.target)
                    related.append(self._nodes[edge.target])
                    queue.append((edge.target, depth + 1))

            # Incoming edges
            for edge in self._reverse.get(current, []):
                if edge.source not in visited:
                    visited.add(edge.source)
                    related.append(self._nodes[edge.source])
                    queue.append((edge.source, depth + 1))

        return related

    def get_relationships(self, node_id: str) -> List[dict]:
        """Return all direct relationships for a node (both directions)."""
        rels = []
        for edge in self._adjacency.get(node_id, []):
            target = self._nodes.get(edge.target)
            if target:
                rels.append({
                    "direction": "outgoing",
                    "relation": edge.relation,
                    "node": target.label,
                    "description": edge.description
                })
        for edge in self._reverse.get(node_id, []):
            source = self._nodes.get(edge.source)
            if source:
                rels.append({
                    "direction": "incoming",
                    "relation": edge.relation,
                    "node": source.label,
                    "description": edge.description
                })
        return rels

    def match_query(self, query: str) -> List[KGNode]:
        """
        Simple keyword matching to find relevant KG nodes from a user query.
        Returns matched nodes sorted by relevance.
        """
        query_lower = query.lower()
        scored: List[tuple] = []

        # Keyword → node_id mapping for fuzzy matching
        keyword_map = {
            "dharma": ["dharma", "dharmashastra", "idar"],
            "danda": ["danda", "arthashastra", "idar"],
            "purushartha": ["purushartha", "dharma"],
            "purushaartha": ["purushartha"],
            "purusartha": ["purushartha"],
            "arthashastra": ["arthashastra", "danda"],
            "kautilya": ["arthashastra", "danda"],
            "chanakya": ["arthashastra", "danda"],
            "dharmashastra": ["dharmashastra", "dharma"],
            "manusmriti": ["dharmashastra"],
            "manu": ["dharmashastra"],
            "yajnavalkya": ["dharmashastra"],
            "narada": ["dharmashastra"],
            "nyaya": ["nyaya", "dharmashastra"],
            "irac": ["irac", "idar"],
            "idar": ["idar", "dharma", "danda"],
            "article 21": ["article21", "due_process", "dharma"],
            "article 14": ["article14", "dharma"],
            "right to life": ["article21", "due_process"],
            "equality": ["article14"],
            "basic structure": ["basic_structure", "stare_decisis"],
            "kesavananda": ["basic_structure"],
            "maneka gandhi": ["due_process", "article21"],
            "due process": ["due_process", "article21"],
            "ipc": ["ipc", "bns", "danda"],
            "penal code": ["ipc", "bns"],
            "bns": ["bns", "ipc"],
            "nyaya sanhita": ["bns"],
            "contract": ["ica", "arthashastra"],
            "contract act": ["ica"],
            "mens rea": ["mens_rea", "ipc", "danda"],
            "guilty mind": ["mens_rea"],
            "precedent": ["stare_decisis", "basic_structure"],
            "stare decisis": ["stare_decisis"],
            "punishment": ["danda", "ipc", "bns"],
            "sanction": ["danda"],
            "situational ethics": ["purushartha"],
            "daya krishna": ["purushartha"],
        }

        matched_ids: Set[str] = set()
        for keyword, node_ids in keyword_map.items():
            if keyword in query_lower:
                for nid in node_ids:
                    matched_ids.add(nid)

        # Also do a basic label/description match
        for node_id, node in self._nodes.items():
            if node_id not in matched_ids:
                if node.label.lower() in query_lower or query_lower in node.description.lower():
                    matched_ids.add(node_id)

        return [self._nodes[nid] for nid in matched_ids if nid in self._nodes]

    def enrich_context(self, query: str, max_nodes: int = 5) -> str:
        """
        Given a user query, find matching KG nodes + their relationships,
        and return enriched context text to be injected alongside RAG results.
        """
        matched = self.match_query(query)
        if not matched:
            return ""

        sections = []
        seen_ids: Set[str] = set()

        for node in matched[:max_nodes]:
            if node.id in seen_ids:
                continue
            seen_ids.add(node.id)

            # Node context
            parts = [f"[KG] {node.to_context()}"]

            # Direct relationships
            rels = self.get_relationships(node.id)
            if rels:
                rel_strs = []
                for r in rels[:4]:
                    arrow = "→" if r["direction"] == "outgoing" else "←"
                    rel_strs.append(f"  {arrow} {r['relation'].replace('_', ' ')}: "
                                    f"{r['node']} ({r['description']})")
                parts.append("Connections:\n" + "\n".join(rel_strs))

            sections.append("\n".join(parts))

        return "\n\n".join(sections)

    def get_graph_summary(self) -> dict:
        """Return stats for API/debug endpoints."""
        categories = {}
        for n in self._nodes.values():
            categories[n.category] = categories.get(n.category, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "categories": categories,
            "nodes": [{"id": n.id, "label": n.label, "category": n.category}
                      for n in self._nodes.values()],
        }


# ── Singleton ───────────────────────────────────────────────────────

_graph: Optional[DharmaKnowledgeGraph] = None

def get_knowledge_graph() -> DharmaKnowledgeGraph:
    global _graph
    if _graph is None:
        _graph = DharmaKnowledgeGraph()
    return _graph
