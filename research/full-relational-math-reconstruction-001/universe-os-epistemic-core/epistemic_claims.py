"""Claim, Belief Structure, Conflict, Destroy Conditions and verification.

§18.2-18.5 of Issue #7: a claim is a first-class entity, its status is distinct
from its epistemic type, its justification is a readable structure (not a
score), conflicts are never averaged away, and prediction-registered destroy
conditions fire by rule without erasing the earlier claim version.

No ASTRAEA adapter, real source, GUI, trading runtime or network call exists
here.  All fixtures are synthetic and must be marked as such.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from epistemic_types import (
    ATTACK_EDGES,
    CLAIM_REQUIRED_FIELDS,
    CLAIM_STATUSES,
    COMPARISON_OPERATORS,
    CONFLICT_DIVERGENCE_TYPES,
    CONFLICT_STATES,
    DEPENDENCY_EDGES,
    EPISTEMIC_TYPES,
    EPISTEMIC_VERSION,
    REVIEW_ACTIONS,
    EpistemicContractError,
    digest,
    frozen,
    require,
)

PRIMARY_NODE_TYPES = ("Source", "Dataset", "Observation", "Measurement")

ACTION_TO_STATUS = {
    "review_required": "disputed",
    "suspend": "suspended",
    "dispute": "disputed",
    "reject": "rejected",
    "accept_within_scope": "accepted_within_scope",
}


# ---------------------------------------------------------------------------
# 18.2 Claim Object
# ---------------------------------------------------------------------------

def create_claim(
    graph: Any,
    claim_id: str,
    *,
    statement: str,
    subject: str,
    predicate: str,
    object_value: Any,
    scope: Dict[str, Any],
    epistemic_type: str,
    sources: Sequence[str],
    transformation_chain: Sequence[str] = (),
    supporting_arguments: Sequence[str] = (),
    contradicting_arguments: Sequence[str] = (),
    assumptions: Sequence[str] = (),
    status: str = "draft",
    author: str = "unspecified",
    created_at: str = "unknown",
    method_version: str = EPISTEMIC_VERSION,
    revision_conditions: Sequence[str] = (),
    prediction: Optional[str] = None,
    conflict_ids: Sequence[str] = (),
    synthetic: bool = False,
    node_type: str = "Claim",
    scope_note: Optional[str] = None,
) -> Dict[str, Any]:
    require(node_type in ("Claim", "Hypothesis"), "claims must be Claim or Hypothesis")
    require(bool(statement), "claim statement required")
    require(epistemic_type in EPISTEMIC_TYPES, f"unknown epistemic type {epistemic_type!r}")
    require(status in CLAIM_STATUSES, f"unknown claim status {status!r}")
    require(isinstance(scope, dict) and bool(scope), "claim scope is mandatory")
    require(bool(created_at) and created_at != "unknown" or synthetic,
            "claim needs a creation date unless it is a synthetic fixture")
    payload = {
        "claim_id": claim_id,
        "statement": statement,
        "subject": subject,
        "predicate": predicate,
        "object_value": frozen(object_value),
        "scope": frozen(scope),
        "epistemic_type": epistemic_type,
        "sources": list(sources),
        "transformation_chain": list(transformation_chain),
        "supporting_arguments": list(supporting_arguments),
        "contradicting_arguments": list(contradicting_arguments),
        "assumptions": list(assumptions),
        "status": status,
        "author": author,
        "created_at": created_at,
        "method_version": method_version,
        "revision_conditions": list(revision_conditions),
        "prediction": prediction,
        "conflict_ids": list(conflict_ids),
        "scope_note": scope_note,
    }
    require(all(field in payload for field in CLAIM_REQUIRED_FIELDS),
            "claim payload is missing a required field")
    return graph.add_node(
        claim_id, node_type, payload,
        provenance={"sources": list(sources), "created_at": created_at},
        scope=scope,
        author=author,
        epistemic_status=status,
        synthetic=synthetic,
    )


def claim_versions(graph: Any, claim_id: str) -> List[Dict[str, Any]]:
    versions = graph.versions(claim_id)
    require(bool(versions), f"unknown claim {claim_id!r}")
    require(versions[0]["node_type"] in ("Claim", "Hypothesis"), "node is not a claim")
    return versions


def supersede_claim(graph: Any, claim_id: str, **changes: Any) -> Dict[str, Any]:
    """A changed statement/scope/ground creates a new claim version with a diff."""
    old = graph.current(claim_id)
    require(old is not None and old["node_type"] in ("Claim", "Hypothesis"),
            f"unknown claim {claim_id!r}")
    payload = dict(old["payload"])
    forbidden_promotion = {"epistemic_type": "measured"}
    for key, value in changes.items():
        if key in forbidden_promotion and payload.get("epistemic_type") == "hypothesis":
            require(value != forbidden_promotion[key],
                    "a hypothesis cannot be silently promoted to a measurement")
        payload[key] = frozen(value)
    new_version = graph.update_node(
        claim_id, payload,
        provenance=old["provenance"],
        scope=payload["scope"],
        author=changes.get("author", old["author"]),
        epistemic_status=payload["status"],
        synthetic=old["synthetic"],
    )
    graph.record_event(
        "claim_revised",
        {
            "claim_id": claim_id,
            "from_version": old["version"],
            "to_version": new_version["version"],
            "changed_fields": sorted(k for k in changes if k in payload),
        },
        actor=changes.get("author", old["author"]),
    )
    return new_version


# ---------------------------------------------------------------------------
# 18.3 Belief Structure Passport -- readable structure, never a number
# ---------------------------------------------------------------------------

def belief_structure(graph: Any, claim_id: str) -> Dict[str, Any]:
    claim = graph.current(claim_id)
    require(claim is not None and claim["node_type"] in ("Claim", "Hypothesis"),
            f"unknown claim {claim_id!r}")
    supports = graph.incoming(claim_id, ("supports",))
    attacks = graph.incoming(claim_id, ATTACK_EDGES)

    def is_primary(node_id: str) -> bool:
        node = graph.current(node_id)
        if node is None or node["node_type"] not in PRIMARY_NODE_TYPES:
            return False
        # A publication that merely reuses a dataset is not a new primary basis.
        return not graph.outgoing(node_id, DEPENDENCY_EDGES)

    support_chains: List[Dict[str, Any]] = []
    primary: Set[str] = set()
    for edge in supports:
        argument_id = edge["from_id"]
        closure = graph.dependency_closure(argument_id)
        bases = sorted(node_id for node_id in closure if is_primary(node_id))
        primary.update(bases)
        support_chains.append({
            "argument": argument_id,
            "scope": edge["scope"],
            "dependency_chain": sorted(closure),
            "primary_bases": bases,
        })

    shared: Dict[str, List[str]] = {}
    for chain in support_chains:
        for base in chain["primary_bases"]:
            shared.setdefault(base, []).append(chain["argument"])
    critical_nodes = sorted(base for base, users in shared.items() if len(users) > 1)

    reviews = [
        edge["to_id"] for edge in graph.outgoing(claim_id, ("reviewed_by",))
    ]

    return {
        "claim_id": claim_id,
        "claim_version": claim["version"],
        "rule_version": EPISTEMIC_VERSION,
        "structural_only": True,
        "quantitative_score": None,
        "support_chains": support_chains,
        "contradictions": [
            {"argument": e["from_id"], "scope": e["scope"], "kind": e["edge_type"]}
            for e in attacks
        ],
        "alternatives": list(claim["payload"].get("contradicting_arguments", [])),
        "assumptions": list(claim["payload"].get("assumptions", [])),
        "independent_primary_bases": sorted(primary),
        "critical_nodes": critical_nodes,
        "reviews": sorted(set(reviews)),
        "prediction": claim["payload"].get("prediction"),
        "status": claim["payload"].get("status", "unknown"),
        "epistemic_type": claim["payload"].get("epistemic_type", "unknown"),
        "grounding_digest": digest({"claim": claim_id, "chains": support_chains}),
    }


def assert_no_score(structure: Dict[str, Any]) -> bool:
    require(structure.get("quantitative_score") is None,
            "belief structure must not be reduced to a numeric score")
    forbidden = ("confidence_percent", "trust_score", "belief_probability", "overall_score")
    require(not any(key in structure for key in forbidden),
            "a universal confidence score is forbidden")
    return True


def impact_analysis(
    graph: Any,
    claim_id: str,
    removed_node_id: str,
    *,
    emit_review: bool = True,
    actor: str = "epistemic_core",
) -> Dict[str, Any]:
    """Structural impact of disqualifying a critical node (18.3)."""
    before = belief_structure(graph, claim_id)
    remaining = [c for c in before["support_chains"]
                 if removed_node_id not in c["dependency_chain"]]
    lost = [c for c in before["support_chains"]
            if removed_node_id in c["dependency_chain"]]
    result = {
        "claim_id": claim_id,
        "removed_node": removed_node_id,
        "support_chains_before": len(before["support_chains"]),
        "support_chains_after": len(remaining),
        "lost_support": [c["argument"] for c in lost],
        "review_required": bool(lost),
        "remaining_primary_bases": sorted(
            {base for c in remaining for base in c["primary_bases"]}),
        "quantitative_percent": None,
        "structural_only": True,
    }
    if lost and emit_review:
        graph.record_event(
            "claim_review_triggered",
            {"claim_id": claim_id, "removed_node": removed_node_id,
             "lost_support": result["lost_support"]},
            actor=actor,
        )
    return result


# ---------------------------------------------------------------------------
# 18.4 Conflict Object
# ---------------------------------------------------------------------------

class ConflictRegistry:
    def open(
        self,
        graph: Any,
        conflict_id: str,
        claim_ids: Sequence[str],
        *,
        divergence_type: str,
        comparability: Dict[str, Any],
        author: str = "unspecified",
        synthetic: bool = False,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        require(len(claim_ids) >= 2, "a conflict needs at least two claims")
        require(divergence_type in CONFLICT_DIVERGENCE_TYPES,
                f"unknown divergence type {divergence_type!r}")
        claims = []
        for claim_id in claim_ids:
            node = graph.current(claim_id)
            require(node is not None and node["node_type"] in ("Claim", "Hypothesis"),
                    f"unknown claim {claim_id!r}")
            claims.append(node)
        sides = [
            {
                "claim_id": c["node_id"],
                "value": c["payload"]["object_value"],
                "provenance": c["provenance"],
                "version": c["version"],
            }
            for c in claims
        ]
        source_sets = [set(c["payload"].get("sources", [])) for c in claims]
        shared = sorted(set.intersection(*source_sets)) if source_sets else []
        payload = {
            "conflict_id": conflict_id,
            "disputed_claims": list(claim_ids),
            "versions": sides,
            "divergence_type": divergence_type,
            "comparability": frozen(comparability),
            "shared_sources": shared,
            "resolutions": [],
            "status": "open",
            "note": note,
        }
        record = graph.add_node(
            conflict_id, "Conflict", payload,
            provenance={"claim_versions": [c["version"] for c in claims]},
            author=author,
            epistemic_status="open",
            synthetic=synthetic,
        )
        for claim_id in claim_ids:
            graph.add_edge(conflict_id, claim_id, "applies_to", author=author, synthetic=synthetic)
        for i in range(len(claim_ids) - 1):
            graph.add_edge(
                claim_ids[i], claim_ids[i + 1], "contradicts", scope=conflict_id,
                author=author, synthetic=synthetic,
            )
        return record

    def resolve(
        self,
        graph: Any,
        conflict_id: str,
        *,
        scope: Dict[str, Any],
        reason: str,
        reviewer: str,
        evidence_ids: Sequence[str],
        author: str = "unspecified",
    ) -> Dict[str, Any]:
        record = graph.current(conflict_id)
        require(record is not None and record["node_type"] == "Conflict",
                f"unknown conflict {conflict_id!r}")
        require(bool(scope) and bool(reason) and bool(reviewer),
                "a scoped resolution needs scope, reason and reviewer")
        require(bool(evidence_ids), "a resolution needs explicit evidence references")
        forbidden = ("averaged_value", "mean", "average", "chosen_value")
        require(not any(key in scope for key in forbidden),
                "conflicts cannot be closed by averaging or silently choosing a value")
        payload = dict(record["payload"])
        resolution = {
            "scope": frozen(scope),
            "reason": reason,
            "reviewer": reviewer,
            "evidence_ids": list(evidence_ids),
            "sequence": len(payload["resolutions"]) + 1,
        }
        payload["resolutions"] = list(payload["resolutions"]) + [resolution]
        payload["status"] = "resolved_with_scope" if len(payload["resolutions"]) >= 1 else "partially_resolved"
        if scope.get("partial") is True:
            payload["status"] = "partially_resolved"
        updated = graph.update_node(
            conflict_id, payload,
            provenance=record["provenance"],
            author=author or reviewer,
            epistemic_status=payload["status"],
            synthetic=record["synthetic"],
        )
        graph.record_event(
            "conflict_resolved_with_scope",
            {"conflict_id": conflict_id, "scope": frozen(scope), "reviewer": reviewer},
            actor=reviewer,
        )
        return updated

    def reopen(
        self,
        graph: Any,
        conflict_id: str,
        *,
        reason: str,
        actor: str,
        new_evidence: Sequence[str] = (),
    ) -> Dict[str, Any]:
        record = graph.current(conflict_id)
        require(record is not None and record["node_type"] == "Conflict",
                f"unknown conflict {conflict_id!r}")
        require(bool(reason) and bool(actor), "reopening needs a reason and an actor")
        payload = dict(record["payload"])
        payload["status"] = "open"
        payload.setdefault("reopenings", []).append(
            {"reason": reason, "actor": actor, "new_evidence": list(new_evidence)}
        )
        updated = graph.update_node(
            conflict_id, payload,
            provenance=record["provenance"],
            author=actor,
            epistemic_status="open",
            synthetic=record["synthetic"],
        )
        graph.record_event("conflict_reopened",
                           {"conflict_id": conflict_id, "reason": reason}, actor=actor)
        return updated


# ---------------------------------------------------------------------------
# 18.5 Revision / Destroy Conditions
# ---------------------------------------------------------------------------

class ConditionRegistry:
    def register(
        self,
        graph: Any,
        condition_id: str,
        *,
        observable: str,
        target: str,
        comparison: str,
        threshold: Any,
        units: str,
        uncertainty: Dict[str, Any],
        source_requirements: Sequence[str],
        controls: Sequence[str],
        expected_action: str,
        preregistration_date: str,
        claim_id: str,
        machine_checkable: bool = True,
        author: str = "unspecified",
        synthetic: bool = False,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        require(comparison in COMPARISON_OPERATORS, f"unknown comparison {comparison!r}")
        require(expected_action in REVIEW_ACTIONS, f"unknown action {expected_action!r}")
        require(bool(observable) and bool(target) and bool(units),
                "condition needs observable, target and units")
        require(bool(preregistration_date), "preregistration date is mandatory")
        require(graph.current(claim_id) is not None, f"unknown claim {claim_id!r}")
        payload = {
            "condition_id": condition_id,
            "observable": observable,
            "target": target,
            "comparison": comparison,
            "threshold": threshold,
            "units": units,
            "uncertainty": frozen(uncertainty),
            "source_requirements": list(source_requirements),
            "controls": list(controls),
            "expected_action": expected_action,
            "preregistration_date": preregistration_date,
            "claim_id": claim_id,
            "machine_checkable": bool(machine_checkable),
            "note": note,
        }
        record = graph.add_node(
            condition_id, "Condition", payload,
            provenance={"preregistered": True, "date": preregistration_date},
            author=author,
            epistemic_status="preregistered",
            synthetic=synthetic,
        )
        graph.add_edge(condition_id, claim_id, "tests", author=author, synthetic=synthetic)
        return record

    def evaluate(
        self,
        graph: Any,
        condition_id: str,
        observation: Dict[str, Any],
        *,
        version: Optional[int] = None,
        actor: str = "epistemic_core",
    ) -> Dict[str, Any]:
        versions = graph.versions(condition_id)
        require(bool(versions), f"unknown condition {condition_id!r}")
        condition = versions[(version or len(versions)) - 1]
        payload = condition["payload"]
        result: Dict[str, Any] = {
            "condition_id": condition_id,
            "condition_version": condition["version"],
            "observed_value": observation.get("value"),
            "threshold": payload["threshold"],
            "fired": False,
            "status": "not_fired",
        }
        if not payload["machine_checkable"]:
            result["status"] = "human_review_required"
            graph.record_event(
                "condition_human_review_required",
                {"condition_id": condition_id, "reason": "not machine_checkable"},
                actor=actor,
            )
            return result
        if observation.get("units") != payload["units"]:
            result["status"] = "units_mismatch"
            return result
        missing = [
            requirement for requirement in payload["source_requirements"]
            if observation.get(requirement) is not True
        ]
        if missing:
            result["status"] = "human_review_required"
            result["missing_requirements"] = missing
            graph.record_event(
                "condition_human_review_required",
                {"condition_id": condition_id, "missing": missing},
                actor=actor,
            )
            return result
        value = observation.get("value")
        require(isinstance(value, (int, float)) and not isinstance(value, bool),
                "a machine-checkable observation needs a numeric value")
        threshold = payload["threshold"]
        operators = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        fired = operators[payload["comparison"]](value, threshold)
        result["fired"] = fired
        if not fired:
            return result
        claim_id = payload["claim_id"]
        old = graph.current(claim_id)
        require(old is not None, f"unknown linked claim {claim_id!r}")
        new_status = ACTION_TO_STATUS[payload["expected_action"]]
        new_payload = dict(old["payload"])
        new_payload["status"] = new_status
        graph.update_node(
            claim_id, new_payload,
            provenance=old["provenance"],
            author=actor,
            epistemic_status=new_status,
            synthetic=old["synthetic"],
        )
        graph.record_event(
            "destroy_condition_triggered",
            {
                "condition_id": condition_id,
                "condition_version": condition["version"],
                "claim_id": claim_id,
                "action": payload["expected_action"],
                "new_status": new_status,
            },
            actor=actor,
        )
        result["status"] = "triggered"
        result["claim_status"] = new_status
        return result

    def amend(self, graph: Any, condition_id: str, **changes: Any) -> Dict[str, Any]:
        """Post-hoc changes create a new version; the registered test stays."""
        current = graph.current(condition_id)
        require(current is not None and current["node_type"] == "Condition",
                f"unknown condition {condition_id!r}")
        payload = dict(current["payload"])
        payload.update(changes)
        payload["amended_after_result"] = True
        return graph.update_node(
            condition_id, payload,
            provenance=current["provenance"],
            author=changes.get("author", current["author"]),
            epistemic_status=current["epistemic_status"],
            synthetic=current["synthetic"],
        )


# ---------------------------------------------------------------------------
# 18.9 / 18.11 Independent verification and claim gates
# ---------------------------------------------------------------------------

REQUIRED_REVIEW_CHECKS = ("primary_sources", "dependencies", "rubric_applicability")


def independent_verification(
    graph: Any,
    claim_id: str,
    *,
    reviewer: str,
    checks: Sequence[str],
    evidence_refs: Sequence[str],
    author: str = "unspecified",
    synthetic: bool = False,
) -> Dict[str, Any]:
    claim = graph.current(claim_id)
    require(claim is not None and claim["node_type"] in ("Claim", "Hypothesis"),
            f"unknown claim {claim_id!r}")
    claim_author = claim["payload"].get("author", "unspecified")
    require(reviewer != claim_author, "self-assessment is not an independent verification")
    require(all(check in checks for check in REQUIRED_REVIEW_CHECKS),
            f"reviewer must check {REQUIRED_REVIEW_CHECKS}")
    require(bool(evidence_refs), "reviewer must cite concrete evidence references")
    review_id = f"REVIEW_{claim_id}_{len(graph.incoming(claim_id, ('reviewed_by',))) + 1}"
    record = graph.add_node(
        review_id, "Review",
        {
            "review_id": review_id,
            "claim_id": claim_id,
            "claim_version": claim["version"],
            "reviewer": reviewer,
            "claim_author": claim_author,
            "checks": list(checks),
            "evidence_refs": list(evidence_refs),
            "independent": True,
            "self_assessment": False,
            "human_review": False,
        },
        provenance={"evidence_refs": list(evidence_refs)},
        author=reviewer,
        epistemic_status="independent_verification",
        synthetic=synthetic,
    )
    graph.add_edge(claim_id, review_id, "reviewed_by", author=reviewer, synthetic=synthetic)
    return record


def claim_gate(graph: Any, claim_id: str, *, requires_independent: bool = True) -> Dict[str, Any]:
    claim = graph.current(claim_id)
    require(claim is not None, f"unknown claim {claim_id!r}")
    status = claim["payload"]["status"]
    reasons: List[str] = []
    if status in ("rejected", "suspended", "superseded", "draft"):
        reasons.append(f"claim status {status!r} does not pass the gate")
    if requires_independent:
        reviews = [
            graph.current(e["to_id"]) for e in graph.outgoing(claim_id, ("reviewed_by",))
        ]
        independent = [
            r for r in reviews if r and r["payload"].get("independent") is True
            and r["payload"].get("reviewer") != claim["payload"].get("author")
        ]
        if not independent:
            reasons.append("no independent verification")
    open_conflicts = [
        c for c in graph.nodes("Conflict")
        if claim_id in c["payload"].get("disputed_claims", [])
        and c["payload"]["status"] in ("open", "under_review")
    ]
    if open_conflicts:
        reasons.append("open conflict: " + ", ".join(c["node_id"] for c in open_conflicts))
    fired = [
        c for c in graph.nodes("Condition")
        if c["payload"].get("claim_id") == claim_id
        and any(e["event_type"] == "destroy_condition_triggered"
                and e["payload"].get("claim_id") == claim_id
                for e in graph.events())
    ]
    if fired:
        reasons.append("destroy condition fired")
    return {"claim_id": claim_id, "passed": not reasons, "reasons": reasons}
