"""PHASE B orchestrator — build all deterministic artifacts and reports.

Produces the machine-readable registries and the human-readable audit files
named in the Phase B directive (section 15).  Does NOT touch the atlas build or
git state.  Running twice on identical inputs yields identical outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any, Dict, List

import phase_b_source_catalog as pbc
import phase_b_observations as pbo
import phase_b_coordinate_systems as pcrs
import phase_b_identity as pid
import phase_b_idealization as pidea
import phase_b_relations as prel

HERE = os.path.dirname(os.path.abspath(__file__))

JSON_ARTIFACTS = {
    "phase_b_source_catalog.json": lambda d: d["catalog"],
    "phase_b_coordinate_system_registry.json": lambda d: d["crs"],
    "phase_b_observations.json": lambda d: d["observations"],
    "phase_b_entity_candidate_registry.json": lambda d: d["identity"],
    "phase_b_relation_candidates.json": lambda d: d["relations"],
    "phase_b_epistemic_report.json": lambda d: d["epistemic"],
    "phase_b_import_report.json": lambda d: d["import_report"],
    "phase_b_validation_report.json": lambda d: d["validation"],
    "phase_b_model_registry.json": lambda d: d["models"],
    "phase_b_spatial_coverage.json": lambda d: d["coverage"],
}


def _dump(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2,
                  sort_keys=True, allow_nan=False)
        handle.write("\n")


def _build_payload(include_models: bool = True) -> Dict[str, Any]:
    catalog = pbc.build_catalog()
    observations = pbo.build_observations()
    crs = pcrs.build_registry(observations["observations"])
    identity = pid.build_identity(observations["observations"])
    relations = prel.build_relations(observations["observations"])
    models = None
    if include_models:
        models = pidea.build_model_registry(observations["observations"])

    epistemic = {
        "report_id": "PHASE_B_EPISTEMIC_REPORT",
        "levels": [
            "FILE_PRESENT", "FILE_HASHED", "SOURCE_CONTENT_PARSED",
            "STRUCTURE_VALIDATED", "ORIGINAL_ARCHIVE_MATCHED",
            "SOURCE_DOCUMENT_IDENTIFIED", "SOURCE_PROVENANCE_VERIFIED",
            "COORDINATE_SYSTEM_DOCUMENTED", "COORDINATE_SYSTEM_VERIFIED",
            "INDEPENDENTLY_CORROBORATED", "GEOMETRY_VALIDATED",
            "MODEL_VALIDATED",
        ],
        "states": {
            "FILE_PRESENT": True,
            "FILE_HASHED": True,
            "SOURCE_CONTENT_PARSED": catalog["provenance_states"]["SOURCE_CONTENT_PARSED"],
            "STRUCTURE_VALIDATED": catalog["provenance_states"]["STRUCTURE_VALIDATED"],
            "ORIGINAL_ARCHIVE_MATCHED": catalog["provenance_states"]["ORIGINAL_ARCHIVE_MATCHED"],
            "SOURCE_DOCUMENT_IDENTIFIED": False,
            "SOURCE_PROVENANCE_VERIFIED": False,
            "COORDINATE_SYSTEM_DOCUMENTED": True,
            "COORDINATE_SYSTEM_VERIFIED": False,
            "INDEPENDENTLY_CORROBORATED": False,
            "GEOMETRY_VALIDATED": True,
            "MODEL_VALIDATED": False,
        },
        "independence_note": (
            "a structurally valid file is not a corroborated source; a "
            "mathematically correct model is not a validated historical object"),
    }
    coverage = {
        "report_id": "PHASE_B_SPATIAL_COVERAGE",
        "campaigns": observations["campaign_counts"],
        "campaign_extents": {
            relation["relation_id"]: relation["value"]
            for relation in relations["relations"]
            if relation["relation_kind"] == "within_campaign_plan_extent"},
        "coverage_note": (
            "extents describe where observations were taken, not the boundaries "
            "of monuments, sites or geological bodies"),
    }
    validation = {
        "report_id": "PHASE_B_VALIDATION_REPORT",
        "checks": {
            "expected_total_matches": catalog["counts"]["observed_total"] == 12078,
            "all_expected_sets_parsed": all(
                s["parsed"] for s in catalog["expected_set_status"].values()),
            "observation_ids_unique": (
                len({o["observation_id"] for o in observations["observations"]})
                == observations["observation_count"]),
            "no_kml_z_promoted": crs["observed_anomalies"]["kml_z_nonzero_records"] == 0,
            "all_observations_preserved": identity["totals"]["original_observations_removed"] == 0,
            "no_terrain_mesh": models is None or models["surfaces"]["terrain_mesh"] is None,
            "no_monument_surface": models is None or models["surfaces"]["monument_surface"] is None,
            "cross_campaign_transform_performed": False,
        },
        "negative_results": [
            "no source provenance independently corroborated",
            "no datum or coordinate system verified",
            "no terrain or monument surface constructed",
            "no identity confirmed between campaigns",
            "no acoustic/hydraulic/electromagnetic claim asserted",
        ],
    }
    import_report = {
        "report_id": "PHASE_B_IMPORT_REPORT",
        "source_counts": observations["campaign_counts"],
        "observation_count": observations["observation_count"],
        "idealization_model_count": models["model_count"] if models else None,
        "relation_count": relations["relation_count"],
        "entity_candidate_count": identity["totals"]["entity_candidates"],
        "import_contract": {
            "sources_copied": False,
            "source_bytes_modified": 0,
            "normalization_version": pbo.SCHEMA_VERSION,
            "parser_versions": {
                "catalog": "phase_b_catalog_v1",
                "observations": pbo.PARSER_VERSION,
                "identity": "phase_b_identity_v1",
                "relations": "phase_b_relations_v1",
                "models": pidea.MODEL_SCHEMA,
            },
        },
    }
    return {
        "catalog": catalog,
        "observations": observations,
        "crs": crs,
        "identity": identity,
        "relations": relations,
        "models": models,
        "epistemic": epistemic,
        "coverage": coverage,
        "validation": validation,
        "import_report": import_report,
    }


def build_all(include_models: bool = True) -> Dict[str, str]:
    payload = _build_payload(include_models=include_models)
    _dump(os.path.join(HERE, "phase_b_provenance_graph.json"), {
        "report_id": "PHASE_B_PROVENANCE_GRAPH",
        "nodes": [
            {"node_id": entry["name"], "kind": "source_file",
             "sha256": entry["raw_sha256"],
             "canonical_sha256": entry["canonical_json_sha256"]}
            for entry in payload["catalog"]["derived_files"]],
        "edges": payload["catalog"]["raw_archive_reconciliation"],
    })
    written: Dict[str, str] = {}
    for filename, getter in JSON_ARTIFACTS.items():
        value = getter(payload)
        if value is None:
            continue
        path = os.path.join(HERE, filename)
        _dump(path, value)
        written[filename] = hashlib.sha256(
            open(path, "rb").read()).hexdigest()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase B artifacts")
    parser.add_argument("--no-models", action="store_true",
                        help="skip expensive large-set idealization")
    args = parser.parse_args()
    written = build_all(include_models=not args.no_models)
    for name, sha in sorted(written.items()):
        print("%s %s" % (sha[:12], name))


if __name__ == "__main__":
    main()
