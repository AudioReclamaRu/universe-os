"""Canonical, append-only Knowledge Graph and its lazy passport projections.

The graph is the single source of truth required by Issue #7 §18.1/§18.8.
Fifteen-odd passports are *projections*, never independent documents.  Edges are
typed and directed; a universal "related_to" link is rejected.  Corrections and
reviews create new versions and events -- previous records are never rewritten.

Edge direction convention (fixed and checked):
  * dependency edges go from the dependent node to its prerequisite
    (``C derived_from B`` => C -> B);
  * support/attack edges go from the argument to the claim
    (``A supports C`` => A -> C).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from epistemic_types import (
    DEPENDENCY_EDGES,
    EDGE_TYPES,
    FORBIDDEN_EDGE_TYPES,
    NODE_TYPES,
    PASSPORT_KINDS,
    PASSPORT_STATES,
    EpistemicContractError,
    digest,
    frozen,
    require,
)


class KnowledgeGraph:
    """Append-only typed graph with canonical IDs and explicit versions."""

    def __init__(self, graph_id: str = "UNIVERSE_EPISTEMIC_GRAPH") -> None:
        self.graph_id = graph_id
        self._nodes: Dict[str, List[Dict[str, Any]]] = {}
        self._edges: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []
        # Optional link to the ontology passport.  When set, class registration
        # becomes a graph event and can therefore be audited by the same
        # validator as every other mutation (enforcement audit, 2026-11-24).
        self.ontology: Optional[Any] = None

    # -- writing -----------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        node_type: str,
        payload: Dict[str, Any],
        *,
        provenance: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
        author: str = "unspecified",
        epistemic_status: Optional[str] = None,
        synthetic: bool = False,
        supersedes: Optional[int] = None,
    ) -> Dict[str, Any]:
        require(isinstance(node_id, str) and bool(node_id.strip()), "node_id required")
        require(node_type in NODE_TYPES, f"unknown node_type {node_type!r}")
        require(isinstance(payload, dict), "payload must be a mapping")
        existing = self._nodes.get(node_id, [])
        version = len(existing) + 1
        require(
            supersedes is None or supersedes == version - 1,
            "supersedes must point at the immediately previous version",
        )
        record = {
            "node_id": node_id,
            "node_type": node_type,
            "version": version,
            "payload": frozen(payload),
            "provenance": frozen(provenance or {}),
            "scope": frozen(scope or {}),
            "author": author,
            "epistemic_status": epistemic_status,
            "synthetic": bool(synthetic),
            "supersedes": supersedes,
            "sequence": len(self._events),
        }
        self._nodes.setdefault(node_id, []).append(record)
        self._event("node_added", {"node_id": node_id, "version": version})
        return frozen(record)

    def update_node(self, node_id: str, payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Create a new version; the old version stays in the history."""
        current = self.current(node_id)
        require(current is not None, f"unknown node {node_id!r}")
        merged = dict(current["payload"])
        if kwargs.pop("merge", False):
            merged.update(payload)
        else:
            merged = dict(payload)
        kwargs.setdefault("provenance", current["provenance"])
        kwargs.setdefault("scope", current["scope"])
        kwargs.setdefault("author", current["author"])
        kwargs.setdefault("epistemic_status", current["epistemic_status"])
        kwargs.setdefault("synthetic", current["synthetic"])
        return self.add_node(
            node_id, current["node_type"], merged,
            supersedes=current["version"], **kwargs,
        )

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str,
        *,
        scope: str = "global",
        provenance: Optional[Dict[str, Any]] = None,
        author: str = "unspecified",
        synthetic: bool = False,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        require(edge_type not in FORBIDDEN_EDGE_TYPES, "untyped universal edges are forbidden")
        require(edge_type in EDGE_TYPES, f"unknown edge_type {edge_type!r}")
        require(self.current(from_id) is not None, f"unknown source node {from_id!r}")
        require(self.current(to_id) is not None, f"unknown target node {to_id!r}")
        for edge in self._edges:
            duplicate = (
                edge["from_id"] == from_id and edge["to_id"] == to_id
                and edge["edge_type"] == edge_type and edge["scope"] == scope
            )
            require(not duplicate, "duplicate typed edge")
        edge = {
            "edge_id": f"E{len(self._edges) + 1:06d}",
            "from_id": from_id,
            "to_id": to_id,
            "edge_type": edge_type,
            "scope": scope,
            "provenance": frozen(provenance or {}),
            "author": author,
            "synthetic": bool(synthetic),
            "note": note,
            "sequence": len(self._events),
        }
        self._edges.append(edge)
        self._event("edge_added", {"edge_id": edge["edge_id"], "edge_type": edge_type})
        return frozen(edge)

    def record_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        actor: str = "unspecified",
        approval_gate: Optional[str] = None,
        synthetic: bool = False,
    ) -> Dict[str, Any]:
        require(bool(event_type), "event_type required")
        event = {
            "event_id": f"V{len(self._events) + 1:06d}",
            "event_type": event_type,
            "payload": frozen(payload),
            "actor": actor,
            "approval_gate": approval_gate,
            # Events must carry the synthetic marker too: without it a
            # synthetic control could masquerade as an evaluated principle.
            "synthetic": bool(synthetic),
            "sequence": len(self._events),
        }
        self._events.append(event)
        return frozen(event)

    def _event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.record_event(event_type, payload)

    # -- reading -----------------------------------------------------------

    def current(self, node_id: str) -> Optional[Dict[str, Any]]:
        versions = self._nodes.get(node_id)
        return frozen(versions[-1]) if versions else None

    def versions(self, node_id: str) -> List[Dict[str, Any]]:
        return frozen(self._nodes.get(node_id, []))

    def nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        result = [versions[-1] for versions in self._nodes.values()]
        if node_type is not None:
            result = [n for n in result if n["node_type"] == node_type]
        return frozen(sorted(result, key=lambda n: n["node_id"]))

    def edges(
        self,
        edge_type: Optional[str] = None,
        *,
        from_id: Optional[str] = None,
        to_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        result = self._edges
        if edge_type is not None:
            result = [e for e in result if e["edge_type"] == edge_type]
        if from_id is not None:
            result = [e for e in result if e["from_id"] == from_id]
        if to_id is not None:
            result = [e for e in result if e["to_id"] == to_id]
        return frozen(result)

    def events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._events
        if event_type is not None:
            result = [e for e in result if e["event_type"] == event_type]
        return frozen(result)

    def incoming(self, node_id: str, edge_types: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
        result = [e for e in self._edges if e["to_id"] == node_id]
        if edge_types is not None:
            result = [e for e in result if e["edge_type"] in edge_types]
        return frozen(result)

    def outgoing(self, node_id: str, edge_types: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
        result = [e for e in self._edges if e["from_id"] == node_id]
        if edge_types is not None:
            result = [e for e in result if e["edge_type"] in edge_types]
        return frozen(result)

    def dependencies(self, node_id: str) -> Set[str]:
        return {e["to_id"] for e in self.outgoing(node_id, DEPENDENCY_EDGES)}

    def dependency_closure(self, node_id: str, *, include_self: bool = False) -> Set[str]:
        seen: Set[str] = {node_id}
        queue: List[str] = [node_id]
        while queue:
            current_id = queue.pop(0)
            for dependency in self.dependencies(current_id):
                if dependency not in seen:
                    seen.add(dependency)
                    queue.append(dependency)
        if not include_self:
            seen.discard(node_id)
        return seen

    def version_signature(self) -> Dict[str, Any]:
        """Everything that a cached projection or computation depends on."""
        return {
            "graph_id": self.graph_id,
            "nodes": {
                node_id: [v["version"] for v in versions]
                for node_id, versions in sorted(self._nodes.items())
            },
            "edges": [e["edge_id"] for e in self._edges],
            "events": [e["event_id"] for e in self._events],
        }

    def graph_digest(self) -> str:
        return digest(self.version_signature())

    def manifest(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for node in self.nodes():
            by_type[node["node_type"]] = by_type.get(node["node_type"], 0) + 1
        by_edge: Dict[str, int] = {}
        for edge in self._edges:
            by_edge[edge["edge_type"]] = by_edge.get(edge["edge_type"], 0) + 1
        return {
            "graph_id": self.graph_id,
            "nodes": len(self._nodes),
            "node_versions": sum(len(v) for v in self._nodes.values()),
            "nodes_by_type": by_type,
            "edges": len(self._edges),
            "edges_by_type": by_edge,
            "events": len(self._events),
            "graph_digest": self.graph_digest(),
        }


class PassportRegistry:
    """Materialises passport projections on demand; no duplicated source data."""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def materialize(
        self,
        graph: KnowledgeGraph,
        entity_id: str,
        kind: str,
        *,
        force: bool = False,
    ) -> Dict[str, Any]:
        require(kind in PASSPORT_KINDS, f"unknown passport kind {kind!r}")
        key = digest({"entity": entity_id, "kind": kind, "graph": graph.graph_digest()})
        if not force and key in self._cache:
            return frozen(self._cache[key])
        entity = graph.current(entity_id)
        if entity is None:
            return self._project(entity_id, kind, "not_created", {}, [], graph)
        if entity["node_type"] not in ("Entity", "EntityState", "Process", "ControlVolume"):
            return self._project(entity_id, kind, "not_applicable", {}, [], graph)

        related_edges = graph.incoming(entity_id) + graph.outgoing(entity_id)
        refs = sorted({e["from_id"] for e in related_edges} | {e["to_id"] for e in related_edges})
        refs = [ref for ref in refs if ref != entity_id]
        fields: Dict[str, Any] = {
            "entity_class": entity["payload"].get("entity_class"),
            "payload": frozen(entity["payload"]),
            "typed_edges": [
                {"type": e["edge_type"], "from": e["from_id"], "to": e["to_id"]}
                for e in related_edges
            ],
            "dependencies": sorted(graph.dependency_closure(entity_id)),
        }
        state = "partial" if related_edges or entity["payload"] else "unknown"
        if entity["payload"].get("passport_complete") is True:
            state = "complete"
        passport = self._project(entity_id, kind, state, fields, refs, graph)
        self._cache[key] = frozen(passport)
        return frozen(passport)

    def _project(
        self,
        entity_id: str,
        kind: str,
        state: str,
        fields: Dict[str, Any],
        refs: Sequence[str],
        graph: KnowledgeGraph,
    ) -> Dict[str, Any]:
        require(state in PASSPORT_STATES, f"unknown passport state {state!r}")
        return {
            "passport_id": f"{entity_id}:{kind}",
            "entity_id": entity_id,
            "kind": kind,
            "state": state,
            "fields": frozen(fields),
            "canonical_refs": list(refs),
            "source_graph_digest": graph.graph_digest(),
            "lazy": True,
        }

    def states_for(self, graph: KnowledgeGraph, entity_id: str) -> Dict[str, str]:
        """No passport is created by inspecting its state (18.8)."""
        return {kind: "not_created" for kind in PASSPORT_KINDS}

    def invalidate(self, node_id: str) -> int:
        """Drop only projections that reference the changed canonical node."""
        doomed = [
            key for key, passport in self._cache.items()
            if passport["entity_id"] == node_id or node_id in passport["canonical_refs"]
        ]
        for key in doomed:
            del self._cache[key]
        return len(doomed)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def cached(self) -> int:
        return len(self._cache)


class OntologyPassport:
    """Versioned class definitions; rejects wrong first-class entity typing."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self._classes: Dict[str, List[Dict[str, Any]]] = {}
        self._graph = graph
        if graph is not None:
            graph.ontology = self

    def register(
        self,
        class_id: str,
        *,
        membership_criteria: Sequence[str],
        allowed_properties: Sequence[str] = (),
        allowed_relations: Sequence[str] = (),
        allowed_states: Sequence[str] = (),
        author: str = "unspecified",
        migration_from: Optional[int] = None,
        graph: Optional[KnowledgeGraph] = None,
        approval_event: Optional[str] = None,
        extension_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        require(bool(class_id), "class_id required")
        require(bool(membership_criteria), "membership criteria required")
        versions = self._classes.get(class_id, [])
        version = len(versions) + 1
        require(
            migration_from is None or migration_from == version - 1,
            "ontology migration must point at the previous version",
        )
        definition = {
            "class_id": class_id,
            "version": version,
            "membership_criteria": list(membership_criteria),
            "allowed_properties": list(allowed_properties),
            "allowed_relations": list(allowed_relations),
            "allowed_states": list(allowed_states),
            "author": author,
            "migration_from": migration_from,
        }
        self._classes.setdefault(class_id, []).append(frozen(definition))
        result = frozen(definition)
        target = graph
        if target is None and hasattr(self, "_graph"):
            target = self._graph  # type: ignore[attr-defined]
        if target is not None:
            target.record_event(
                "ontology_class_registered",
                {"class_id": class_id, "version": version,
                 "migration_from": migration_from,
                 "approval_event": approval_event,
                 "extension_source": extension_source},
                actor=author,
            )
        return result

    def current(self, class_id: str) -> Optional[Dict[str, Any]]:
        versions = self._classes.get(class_id)
        return frozen(versions[-1]) if versions else None

    def change_criteria(
        self,
        graph: KnowledgeGraph,
        class_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """A criterion change is versioned and triggers an impact review (18.9)."""
        current = self.current(class_id)
        require(current is not None, f"unknown ontology class {class_id!r}")
        result = self.register(
            class_id,
            membership_criteria=kwargs.get("membership_criteria", current["membership_criteria"]),
            allowed_properties=kwargs.get("allowed_properties", current["allowed_properties"]),
            allowed_relations=kwargs.get("allowed_relations", current["allowed_relations"]),
            allowed_states=kwargs.get("allowed_states", current["allowed_states"]),
            author=kwargs.get("author", "unspecified"),
            migration_from=current["version"],
            graph=graph,
        )
        affected = [
            n["node_id"] for n in graph.nodes()
            if n["payload"].get("entity_class") == class_id
        ]
        graph.record_event(
            "ontology_impact_review",
            {"class_id": class_id, "new_version": result["version"], "affected": affected},
            actor=kwargs.get("author", "unspecified"),
        )
        return result

    def validate(self, graph: KnowledgeGraph) -> List[str]:
        violations: List[str] = []
        physical_types = {"Entity", "EntityState"}
        non_physical = {"Claim", "Hypothesis", "Conflict", "Review", "Decision"}
        for node in graph.nodes():
            kind = node["node_type"]
            payload = node["payload"]
            if kind in physical_types or kind == "Process":
                class_id = payload.get("entity_class")
                if class_id is None:
                    violations.append(f"{node['node_id']}: entity_class missing")
                elif self.current(class_id) is None:
                    violations.append(f"{node['node_id']}: unregistered class {class_id!r}")
            if kind in non_physical and "entity_class" in payload:
                violations.append(f"{node['node_id']}: epistemic object typed as physical entity")
            # A flow is a Process/Relation with defined bounds, not a rock.
            if "flow_kind" in payload and kind == "Entity":
                violations.append(f"{node['node_id']}: energy flow recorded as Entity")
        for edge in graph.edges():
            for endpoint in (edge["from_id"], edge["to_id"]):
                node = graph.current(endpoint)
                if node is None or not node["payload"].get("entity_class"):
                    continue
                definition = self.current(node["payload"]["entity_class"])
                if definition and definition["allowed_relations"]:
                    if edge["edge_type"] not in definition["allowed_relations"]:
                        violations.append(
                            f"{edge['edge_id']}: relation {edge['edge_type']} not allowed for "
                            f"{node['node_id']}"
                        )
        return violations

    def manifest(self) -> Dict[str, Any]:
        return {
            "classes": {
                class_id: versions[-1]["version"]
                for class_id, versions in sorted(self._classes.items())
            },
            "total_versions": sum(len(v) for v in self._classes.values()),
        }


class IdentityRegistry:
    """Registered identity criteria; state change never silently changes Entity."""

    CONTINUITY_DIMENSIONS: Sequence[str] = (
        "material", "spatial", "structural", "functional", "genealogical",
    )

    def __init__(self) -> None:
        self._criteria: Dict[str, List[Dict[str, Any]]] = {}

    def register(
        self,
        class_id: str,
        *,
        required_traits: Sequence[str],
        secondary_traits: Sequence[str] = (),
        contingent_traits: Sequence[str] = (),
        continuity_dimensions: Sequence[str] = CONTINUITY_DIMENSIONS,
        author: str = "unspecified",
        changed_from: Optional[int] = None,
    ) -> Dict[str, Any]:
        require(bool(class_id), "class_id required")
        require(bool(required_traits), "identity criterion needs required traits")
        versions = self._criteria.get(class_id, [])
        version = len(versions) + 1
        require(
            changed_from is None or changed_from == version - 1,
            "identity criterion change must point at previous version",
        )
        criterion = {
            "class_id": class_id,
            "version": version,
            "required_traits": list(required_traits),
            "secondary_traits": list(secondary_traits),
            "contingent_traits": list(contingent_traits),
            "continuity_dimensions": list(continuity_dimensions),
            "author": author,
            "changed_from": changed_from,
        }
        self._criteria.setdefault(class_id, []).append(frozen(criterion))
        return frozen(criterion)

    def current(self, class_id: str) -> Optional[Dict[str, Any]]:
        versions = self._criteria.get(class_id)
        return frozen(versions[-1]) if versions else None

    def change_criteria(self, graph: KnowledgeGraph, class_id: str, **kwargs: Any) -> Dict[str, Any]:
        current = self.current(class_id)
        require(current is not None, f"unknown identity criterion {class_id!r}")
        result = self.register(
            class_id,
            required_traits=kwargs.get("required_traits", current["required_traits"]),
            secondary_traits=kwargs.get("secondary_traits", current["secondary_traits"]),
            contingent_traits=kwargs.get("contingent_traits", current["contingent_traits"]),
            continuity_dimensions=kwargs.get(
                "continuity_dimensions", current["continuity_dimensions"]),
            author=kwargs.get("author", "unspecified"),
            changed_from=current["version"],
        )
        affected = [
            n["node_id"] for n in graph.nodes()
            if n["payload"].get("entity_class") == class_id
        ]
        graph.record_event(
            "identity_impact_review",
            {"class_id": class_id, "new_version": result["version"], "affected": affected},
            actor=kwargs.get("author", "unspecified"),
        )
        return result

    def evaluate(
        self,
        graph: KnowledgeGraph,
        entity_id: str,
        *,
        observed_traits: Sequence[str],
        class_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        entity = graph.current(entity_id)
        require(entity is not None, f"unknown entity {entity_id!r}")
        class_id = class_id or entity["payload"].get("entity_class")
        criterion = self.current(class_id or "")
        require(criterion is not None, f"no identity criterion for {class_id!r}")
        observed = set(observed_traits)
        required = set(criterion["required_traits"])
        missing = sorted(required - observed)
        lineage_out = graph.outgoing(entity_id, ("split_from", "merged_from"))
        lineage_in = graph.incoming(entity_id, ("split_from", "merged_from", "same_lineage_as"))
        if lineage_out or lineage_in:
            decision = "new_lineage_branch"
            reasons = ["explicit split/merge/lineage relation is present"]
        elif not missing:
            decision = "same_entity"
            reasons = ["all required identity traits observed"]
        else:
            secondary = set(criterion["secondary_traits"])
            contingent = set(criterion["contingent_traits"])
            if all(t in secondary or t in contingent for t in missing):
                decision = "same_entity"
                reasons = ["missing traits are registered as secondary or contingent"]
            else:
                decision = "review_required"
                reasons = [f"required traits missing or unclassified: {missing}"]
        return {
            "entity_id": entity_id,
            "decision": decision,
            "reasons": reasons,
            "criterion_class": class_id,
            "criterion_version": criterion["version"],
            "continuity_dimensions": list(criterion["continuity_dimensions"]),
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            "criteria": {
                class_id: versions[-1]["version"]
                for class_id, versions in sorted(self._criteria.items())
            },
            "continuity_dimensions": list(self.CONTINUITY_DIMENSIONS),
        }
