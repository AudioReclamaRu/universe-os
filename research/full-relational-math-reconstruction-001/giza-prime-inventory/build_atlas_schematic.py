"""Build a STATIC, OFFLINE, HONEST GIZA PRIME DUAL ATLAS.

LAYER 01 — RELATION SKELETON
---------------------------
A display of the current *state of evidence*, not a reconstruction of Giza.
The source register is empty, therefore this layer contains zero verified
sources, zero real objects, zero natural structures and zero relations.
Fourteen slots and nine relation families stay marked SCHEMATIC / NOT GEODETIC.
Its snapshot emits no coordinates and claims no geography.

LAYER 02 — SPATIAL 3D SKELETON
------------------------------
The committed GPMP control JSON is parsed into 41 source points (11 main,
30 secondary) with elevation taken only from the description.  KML Z = 0 is
rejected as a height; no datum conversion, terrain mesh or invented line is
produced.  Provenance states are kept separate: the file is present, parsed and
structure-validated, but not independently corroborated.

The script refuses to build if the inventory honesty gate fails or if the GPMP
source is structurally unexpected.  No network calls are made.  The relation
snapshot still emits no coordinates; the spatial snapshot is a separate inline
document.  Rebuild with:  python build_atlas_schematic.py
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
from typing import Any, Dict, Optional

import inventory_engine as ie
import gpmp_spatial_layer as gsl
import spatial_geometry as sg

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = "atlas_schematic.html"
IMPORT_REPORT = "dual_atlas_import_report.json"
EPISTEMIC_MANIFEST = os.path.normpath(os.path.join(
    HERE, os.pardir, "universe-os-epistemic-core", "epistemic_manifest.json"))
INPUT_FILES = (
    "inventory_source_contract.json",
    "object_registry.json",
    "relation_graph.json",
    "incompleteness_map.json",
)


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def build_snapshot() -> Dict[str, Any]:
    """Validate the registers first, then project only what they really assert."""
    if not ie.assert_inventory_honesty():
        raise ie.InventoryValidationError("inventory honesty gate failed; atlas not built")

    contract = ie.inventory_source_contract()
    registry = ie.object_registry()
    relations = ie.relation_graph()
    incompleteness = ie.incompleteness_map()
    with open(EPISTEMIC_MANIFEST, "r", encoding="utf-8") as handle:
        epistemic = json.load(handle)
    if epistemic.get("live_adapters") != 0:
        raise ie.InventoryValidationError("atlas refuses to render with a live adapter")

    slots = [{
        "slot_id": slot["slot_id"],
        "label": slot["label"],
        "category": slot["landscape_category"],
        "natural_structure": slot["natural_structure"],
        "coverage_status": slot["coverage_status"],
        "verified_object_count": slot["verified_object_count"],
        "known_gap": slot["known_gap"],
        "required_survey_layer": slot["required_survey_layer"],
    } for slot in registry["inventory_slots"]]

    return {
        "atlas_id": "GIZA_RELATION_FIRST_ATLAS_SCHEMATIC",
        "marking": "SCHEMATIC / NOT GEODETIC",
        "scientific_status": "evidence_gate_empty_no_reconstruction",
        "external_citations_attached": False,
        "input_sha256": dict(
            {name: _sha256(os.path.join(HERE, name)) for name in INPUT_FILES},
            epistemic_manifest=_sha256(EPISTEMIC_MANIFEST),
        ),
        "counts": {
            "verified_sources": contract["verified_source_count"],
            "real_objects": len(registry["objects"]),
            "natural_structures": len(registry["natural_structures"]),
            "relations": len(relations["relations"]),
            "inventory_slots": len(slots),
            "relation_classes": len(relations["relation_classes"]),
        },
        "coordinate_claims": False,
        "source_contract": {
            "required_fields": list(contract["required_source_fields"]),
            "accepted_types": list(contract["accepted_source_types"]),
            "gate": dict(contract["gate"]),
        },
        "slots": slots,
        "relation_classes": [{
            "class_id": name,
            "verified_relations": 0,
            "epistemic_statuses": list(relations["epistemic_statuses"]),
        } for name in relations["relation_classes"]],
        "relation_gate": dict(relations["ingestion_gate"]),
        "coverage_states": list(incompleteness["states"]),
        "coverage_completeness": incompleteness["coverage_completeness"],
        "modeling_tiers": {
            tier: {"requires": list(rules["requires"]), "rule": rules["rule"]}
            for tier, rules in registry["modeling_tiers"].items()
        },
        "honesty": {
            "assert_inventory_honesty": True,
            "no_preselected_core": registry["gate"]["no_preselected_core"],
            "no_fabricated_coordinates": registry["gate"]["no_fabricated_coordinates"],
            "absence_is_not_absence_from_system":
                registry["gate"]["absence_from_catalogue_is_not_absence_from_system"],
            "promotable_claims": 0 if contract["verified_source_count"] == 0 else None,
            "live_adapters": epistemic["live_adapters"],
            "cross_cases": dict(epistemic["cross_cases"]),
        },
    }


def build_spatial_snapshot() -> Dict[str, Any]:
    """Second layer: real GPMP control points, validated but not corroborated."""
    return gsl.build_spatial_snapshot()


def write_import_report(path: Optional[str] = None) -> str:
    """Machine-readable record of what the build actually imported."""
    spatial = build_spatial_snapshot()
    target = os.path.join(HERE, IMPORT_REPORT if path is None else path)
    payload = {
        "report_id": "GIZA_PRIME_DUAL_ATLAS_IMPORT_REPORT",
        "relation_layer": {
            "honesty_gate": ie.assert_inventory_honesty(),
            "verified_sources": 0,
            "real_objects": 0,
            "relations": 0,
        },
        "spatial_layer": spatial,
        "build_contract": {
            "source_points_only": True,
            "no_terrain_mesh": True,
            "no_fabricated_lines": True,
            "no_coordinate_conversion": True,
            "kml_z_is_elevation": False,
            "external_requests": 0,
            "generated_by": "build_atlas_schematic.py",
        },
    }
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2,
                  ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return target


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _slot_rows(snapshot: Dict[str, Any]) -> str:
    rows = []
    for slot in snapshot["slots"]:
        kind = "NAT" if slot["natural_structure"] else "ANT"
        rows.append(
            '<div class="srow">'
            '<span class="sid">%s</span>'
            '<span class="skind">%s</span>'
            '<span class="scov">%s</span>'
            '<span class="szero">%s</span>'
            '<span class="sgap">%s</span>'
            '</div>' % (
                _esc(slot["slot_id"]), _esc(kind), _esc(slot["coverage_status"]),
                _esc(slot["verified_object_count"]), _esc(slot["known_gap"]),
            )
        )
    return "".join(rows)


def _relation_rows(snapshot: Dict[str, Any]) -> str:
    rows = []
    for item in snapshot["relation_classes"]:
        rows.append(
            '<div class="rrow"><span>%s</span><span class="zero">0</span></div>'
            % _esc(item["class_id"])
        )
    return "".join(rows)


def _tier_rows(snapshot: Dict[str, Any]) -> str:
    rows = []
    for tier, rules in snapshot["modeling_tiers"].items():
        rows.append(
            '<div class="trow2"><span class="tname">%s</span>'
            '<span class="treq">%s</span></div>'
            % (_esc(tier.upper()), _esc(", ".join(rules["requires"]) or "none"))
        )
    return "".join(rows)


def _coverage_rows(snapshot: Dict[str, Any]) -> str:
    return "".join(
        '<div class="rrow"><span>%s</span><span class="zero">unknown</span></div>'
        % _esc(state) for state in snapshot["coverage_states"]
    )


def _gate_rows(snapshot: Dict[str, Any]) -> str:
    gate = snapshot["source_contract"]["gate"]
    rows = []
    for key, value in gate.items():
        if not isinstance(value, bool):
            continue  # descriptive fields such as 'rule' are not gate flags
        state = "TRUE" if value else "FALSE"
        css = "on" if value else "zero"
        rows.append('<div class="rrow"><span>%s</span><span class="%s">%s</span></div>'
                    % (_esc(key), css, state))
    return "".join(rows)


def render_html(snapshot: Dict[str, Any],
                spatial: Optional[Dict[str, Any]] = None) -> str:
    counts = snapshot["counts"]
    spatial = build_spatial_snapshot() if spatial is None else spatial
    # '<\/' prevents any register text from closing the inline JSON script tag.
    safe_json = json.dumps(
        snapshot, ensure_ascii=False, indent=2, sort_keys=True).replace("</", "<\\/")
    safe_spatial = json.dumps(
        spatial, ensure_ascii=False, indent=2, sort_keys=True).replace("</", "<\\/")
    ctx = {
        "SNAPSHOT": safe_json,
        "SPATIAL_SNAPSHOT": safe_spatial,
        "N_GPMP": str(spatial["counts"]["total"]),
        "N_MAIN": str(spatial["counts"]["main_traverse"]),
        "N_SECOND": str(spatial["counts"]["secondary_network"]),
        "SPATIAL_SHA": spatial["source"]["sha256_of_committed_json"][:12],
        "SLOT_ROWS": _slot_rows(snapshot),
        "RELATION_ROWS": _relation_rows(snapshot),
        "TIER_ROWS": _tier_rows(snapshot),
        "COVERAGE_ROWS": _coverage_rows(snapshot),
        "GATE_ROWS": _gate_rows(snapshot),
        "N_SLOTS": str(counts["inventory_slots"]),
        "N_REL_CLASSES": str(counts["relation_classes"]),
        "SHA": snapshot["input_sha256"]["object_registry.json"][:12],
    }
    template = TEMPLATE
    for key, value in ctx.items():
        template = template.replace("__%s__" % key, value)
    leftover = re.findall(r"__[A-Z][A-Z0-9_]*__", template)
    if leftover:
        raise ie.InventoryValidationError("unresolved template tokens: %s" % sorted(set(leftover)))
    return template


TEMPLATE = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>GIZA PRIME // DUAL ATLAS // RELATION + SPATIAL</title>
<!--
  Preferred design source: ASTRAEA-WARP v6.0 CLEAN/index.html (ASTREYA-HRONOS).
  Reused: palette, Martian Mono / Unbounded typography, numbered panels,
  scanline + vignette, thin gauges, terminal log, three-column telemetry grid.
  Deliberately NOT reused: live feed, trading controls, exchange API, weather claims.
  This file is a static snapshot. Rebuild: python build_atlas_schematic.py
-->
<style>
:root{
  --ink:#09090f;--panel:#0d0d18;--surface:#111120;--border:#1e1e35;
  --amber:#f5a623;--amber2:#ffcc44;--amber-d:#5a3800;
  --green:#39ff7a;--red:#ff3c54;--cyan:#00d4ff;--violet:#8855ff;
  --white:#e8e4d8;--dim:#2a2840;--pink:#ff88cc;
  --mono:'Martian Mono','Consolas',monospace;--head:'Unbounded','Arial Black',sans-serif;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;background:var(--ink);color:var(--amber);font-family:var(--mono);font-size:14px;overflow:hidden;cursor:crosshair;}
body::after{content:'';position:fixed;inset:0;z-index:9999;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.07) 2px,rgba(0,0,0,0.07) 4px);}
body::before{content:'';position:fixed;inset:0;z-index:9998;pointer-events:none;
  background:radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,0.55) 100%);}
body{display:grid;grid-template-rows:64px 1fr 28px;}

/* HEADER */
header{display:flex;align-items:center;justify-content:space-between;padding:0 20px;
  background:var(--panel);border-bottom:1px solid var(--border);position:relative;overflow:hidden;}
header::before{content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(245,166,35,0.025),transparent);
  animation:scanH 5s linear infinite;}
@keyframes scanH{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
.logo{font-family:var(--head);font-size:18px;font-weight:900;letter-spacing:5px;color:var(--amber);
  text-shadow:0 0 20px rgba(245,166,35,.45),0 0 60px rgba(245,166,35,.1);}
.logo span{color:var(--amber2);}
.logo sub{font-size:9px;color:var(--amber-d);letter-spacing:3px;vertical-align:middle;margin-left:10px;}
.hdr-kpis{display:flex;gap:1px;align-items:stretch;height:100%;}
.kpi{display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:0 14px;border-left:1px solid var(--border);min-width:86px;}
.kpi-v{font-family:var(--head);font-size:15px;font-weight:700;color:var(--amber2);letter-spacing:1px;line-height:1;}
.kpi-l{font-size:9px;letter-spacing:2px;color:var(--amber-d);margin-top:4px;}
.hdr-r{display:flex;align-items:center;gap:12px;font-size:11px;}
#conn-dot{width:8px;height:8px;border-radius:50%;background:#1a1a2a;}
#conn-lbl{color:var(--amber-d);letter-spacing:2px;}
#clock{color:var(--amber);letter-spacing:2px;font-weight:500;}

/* MAIN */
main{display:grid;grid-template-columns:340px 1fr 340px;gap:1px;background:var(--border);overflow:hidden;}
.col{display:flex;flex-direction:column;gap:1px;background:var(--border);overflow-y:auto;}
.pnl{background:var(--panel);padding:12px 14px;flex-shrink:0;}
.pnl.grow{flex:1;overflow:hidden;display:flex;flex-direction:column;}
.pnl-title{font-size:9px;letter-spacing:3px;color:var(--amber-d);border-bottom:1px solid var(--border);
  padding-bottom:7px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;}
.pnl-title em{font-style:normal;color:var(--amber);}
.row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;gap:8px;}
.lbl{font-size:11px;color:var(--amber-d);letter-spacing:1px;}
.val{font-size:12px;color:var(--amber);font-weight:500;}
.val.w{color:var(--white);}.val.r{color:var(--red);}.val.c{color:var(--cyan);}.val.v{color:var(--violet);}
.zero{color:var(--amber-d);}.on{color:var(--green);}
.banner{border:1px solid var(--amber2);padding:9px 12px;font-size:13px;color:var(--amber2);
  margin-bottom:10px;min-height:48px;line-height:1.6;word-break:break-word;
  background:rgba(255,204,68,.03);animation:glow 2.4s infinite alternate;}
@keyframes glow{from{box-shadow:none}to{box-shadow:0 0 12px rgba(255,204,68,.22)}}
.mono-line{font-size:10px;color:var(--amber-d);letter-spacing:1px;line-height:1.7;}
.gauge-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:8px;}
.gauge{background:rgba(245,166,35,.02);border:1px solid var(--border);padding:7px 9px;}
.gauge-lbl{font-size:9px;letter-spacing:1px;color:var(--amber-d);margin-bottom:4px;}
.gauge-bar{height:3px;background:var(--dim);margin-bottom:4px;}
.gauge-fill{height:3px;}
.gauge-val{font-size:11px;font-weight:500;}

/* SCHEMATIC MAP — central object fills the available space */
#center-col .map-panel{flex:1 1 auto;min-height:0;display:flex;flex-direction:column;}
.slot-panel{flex:1 1 auto;min-height:200px;display:flex;flex-direction:column;overflow:hidden;}
.term-panel{flex:0 0 auto;max-height:170px;display:flex;flex-direction:column;}
#map{display:block;width:100%;flex:1 1 auto;min-height:0;height:100%;}
.map-cap{font-size:10px;letter-spacing:1px;color:var(--amber-d);text-align:center;margin-top:6px;line-height:1.5;}
.slots{flex:1;overflow-y:auto;margin-top:8px;}
.slots::-webkit-scrollbar,#term::-webkit-scrollbar{width:3px;}
.slots::-webkit-scrollbar-thumb,#term::-webkit-scrollbar-thumb{background:var(--dim);}
.srow{display:grid;grid-template-columns:140px 30px 85px 24px 1fr;gap:6px;padding:5px 0;
  border-bottom:1px solid rgba(30,30,53,.5);font-size:10px;align-items:baseline;}
.sid{color:var(--white);}.skind{color:var(--violet);}.scov{color:var(--amber-d);}
.szero{color:var(--red);}.sgap{color:var(--amber-d);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.rrow{display:flex;justify-content:space-between;font-size:11px;padding:5px 0;gap:8px;
  border-bottom:1px solid rgba(30,30,53,.5);}
.trow2{display:flex;justify-content:space-between;font-size:10px;padding:6px 0;
  border-bottom:1px solid rgba(30,30,53,.5);gap:8px;}
.tname{color:var(--amber2);}.treq{color:var(--amber-d);text-align:right;line-height:1.4;}
#term{overflow-y:auto;flex:1;padding:6px;font-size:10px;line-height:1.7;}
.ll{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ll.ok{color:var(--dim);}.ll.sig{color:var(--amber);}.ll.err{color:rgba(255,60,84,.75);}
.ll.warn{color:rgba(245,166,35,.7);}.ll.sync{color:rgba(0,212,255,.8);}

/* FOOTER */
footer{display:flex;align-items:center;justify-content:space-between;padding:0 16px;
  background:var(--panel);border-top:1px solid var(--border);font-size:10px;
  letter-spacing:2px;color:var(--amber-d);}
.ft em{font-style:normal;color:var(--amber);}

/* DUAL-ATLAS LAYER TABS */
.layer-tabs{display:flex;gap:1px;flex:0 0 auto;padding:0;}
.ltab{font-family:var(--head);font-size:10px;font-weight:900;letter-spacing:2px;
  padding:11px 16px;color:var(--amber-d);cursor:pointer;user-select:none;
  border-right:1px solid var(--border);background:var(--panel);}
.ltab.active{color:var(--amber2);background:rgba(245,166,35,.06);
  box-shadow:inset 0 -2px 0 var(--amber2);}
.ltab:hover{color:var(--amber);}
.layer-view{flex:1 1 auto;min-height:0;display:flex;flex-direction:column;overflow:hidden;}
.layer-view.hidden{display:none;}

/* SPATIAL 3D SKELETON VIEW */
.spatial-grid{display:grid;grid-template-columns:270px 1fr 320px;gap:1px;
  background:var(--border);flex:1 1 auto;min-height:0;overflow:hidden;}
.sp-col{display:flex;flex-direction:column;gap:1px;background:var(--border);
  overflow-y:auto;min-height:0;}
#sp-center{overflow:hidden;}
.sp-canvas-panel{flex:1 1 auto;min-height:0;display:flex;flex-direction:column;overflow:hidden;}
#spatial-canvas{display:block;width:100%;flex:1 1 auto;min-height:0;height:100%;cursor:grab;}
#spatial-canvas.dragging{cursor:grabbing;}
.sp-cap{font-size:10px;letter-spacing:1px;color:var(--amber-d);text-align:center;
  margin-top:6px;line-height:1.5;}
.sp-controls{flex:0 0 auto;}
.sp-control{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
.sp-btn{font-size:10px;letter-spacing:1px;padding:6px 9px;border:1px solid var(--border);
  color:var(--amber-d);cursor:pointer;user-select:none;background:rgba(245,166,35,.02);}
.sp-btn:hover{color:var(--amber);border-color:var(--amber-d);}
.sp-btn.on{color:var(--green);border-color:rgba(57,255,122,.45);}
.sp-search{width:100%;min-height:30px;border:1px solid var(--border);padding:7px 8px;
  font-family:var(--mono);font-size:11px;color:var(--white);background:rgba(5,5,15,.6);
  outline:none;user-select:text;cursor:text;}
.sp-search:focus{border-color:var(--amber-d);}
.sp-list{flex:1;overflow-y:auto;margin-top:8px;}
.sp-list::-webkit-scrollbar{width:3px;}
.sp-list::-webkit-scrollbar-thumb{background:var(--dim);}
.plist-row{display:grid;grid-template-columns:78px 1fr 54px;gap:6px;padding:5px 4px;
  border-bottom:1px solid rgba(30,30,53,.5);font-size:10px;cursor:pointer;}
.plist-row:hover{background:rgba(245,166,35,.05);}
.plist-row.sel{background:rgba(245,166,35,.11);}
.plist-id{color:var(--white);}.plist-net{color:var(--violet);}
.plist-z{color:var(--green);text-align:right;}
.passport{font-size:11px;line-height:1.7;}
.passport .lbl{display:inline-block;min-width:118px;color:var(--amber-d);}
.passport .raw{word-break:break-all;font-size:9px;color:var(--amber-d);
  border:1px solid var(--border);padding:6px;margin-top:6px;line-height:1.5;}
.legend-row{display:flex;align-items:center;gap:8px;font-size:10px;padding:3px 0;color:var(--amber-d);}
.legend-mark{width:12px;height:12px;border:1px solid currentColor;flex:0 0 auto;}
.legend-mark.circle{border-radius:50%;background:var(--amber);color:var(--amber);}
.legend-mark.diamond{transform:rotate(45deg);border-color:var(--violet);}
.axis-key{font-size:9px;letter-spacing:1px;color:var(--amber-d);margin-top:6px;}
</style>
</head>
<body>

<header>
  <div>
    <div class="logo">GIZA<span> PRIME</span><sub>DUAL ATLAS / RELATION + SPATIAL</sub></div>
    <div style="font-size:9px;letter-spacing:2px;color:var(--amber-d);margin-top:3px;">SCHEMATIC / NOT GEODETIC // EVIDENCE-GATED // GPMP SOURCE POINTS ONLY</div>
  </div>
  <div class="hdr-kpis">
    <div class="kpi"><div class="kpi-v">0</div><div class="kpi-l">SRC VERIFIED</div></div>
    <div class="kpi"><div class="kpi-v">0</div><div class="kpi-l">REAL OBJECTS</div></div>
    <div class="kpi"><div class="kpi-v">0</div><div class="kpi-l">RELATIONS</div></div>
    <div class="kpi"><div class="kpi-v" style="color:var(--cyan)">__N_GPMP__</div><div class="kpi-l">GPMP PTS</div></div>
    <div class="kpi"><div class="kpi-v">__N_SLOTS__</div><div class="kpi-l">SLOTS</div></div>
    <div class="kpi"><div class="kpi-v" style="color:var(--violet)">SYMBOLIC</div><div class="kpi-l">TIER</div></div>
    <div class="kpi"><div class="kpi-v" style="font-size:12px;color:var(--red)">NOT_EVALUABLE</div><div class="kpi-l">CROSS CASES</div></div>
  </div>
  <div class="hdr-r">
    <div><div id="conn-dot"></div></div><span id="conn-lbl">STATIC SNAPSHOT</span>
    <span id="clock">SHA __SHA__</span>
  </div>
</header>

<main>
<div class="col">
  <div class="pnl">
    <div class="pnl-title">[ 01 ] <em>ATLAS STATE</em></div>
    <div class="banner">SCHEMATIC / NOT GEODETIC<br>Каркас ожидания данных, а не реконструкция Гизы.</div>
    <div class="row"><span class="lbl">VERIFIED SOURCES</span><span class="val r">0</span></div>
    <div class="row"><span class="lbl">REAL OBJECTS</span><span class="val r">0</span></div>
    <div class="row"><span class="lbl">NATURAL STRUCTURES</span><span class="val r">0</span></div>
    <div class="row"><span class="lbl">RELATIONS</span><span class="val r">0</span></div>
    <div class="row"><span class="lbl">MODEL TIER</span><span class="val v">symbolic</span></div>
    <div class="gauge-grid">
      <div class="gauge"><div class="gauge-lbl">SOURCE VERIFIED</div><div class="gauge-bar"><div class="gauge-fill" style="background:var(--red);width:0%"></div></div><div class="gauge-val" style="color:var(--red)">0 / 0</div></div>
      <div class="gauge"><div class="gauge-lbl">INVENTORIED</div><div class="gauge-bar"><div class="gauge-fill" style="background:var(--red);width:0%"></div></div><div class="gauge-val" style="color:var(--red)">0 / __N_SLOTS__</div></div>
    </div>
  </div>
  <div class="pnl">
    <div class="pnl-title">[ 02 ] <em>SOURCE GATE</em></div>
    <div class="mono-line">Только <span style="color:var(--green)">verified</span> источник допускает реальную запись. pending / rejected — не свидетельство.</div>
    <div style="margin-top:6px">__GATE_ROWS__</div>
  </div>
  <div class="pnl slot-panel">
    <div class="pnl-title">[ 06 ] <em>SLOT REGISTER</em><span>__N_SLOTS__ / 0 inventoried</span></div>
    <div style="display:grid;grid-template-columns:140px 30px 85px 24px 1fr;gap:6px;font-size:9px;letter-spacing:1px;color:var(--amber-d);padding-bottom:6px;border-bottom:1px solid var(--border)">
      <span>SLOT</span><span>KIND</span><span>COVERAGE</span><span>VERIFIED</span><span>KNOWN GAP</span>
    </div>
    <div class="slots">__SLOT_ROWS__</div>
  </div>
  <div class="pnl term-panel">
    <div class="pnl-title">[ 04 ] <em>EPISTEMIC TERMINAL</em></div>
    <div id="term">
      <div class="ll warn">// offline static snapshot — no feed attached</div>
      <div class="ll err">verified_sources = 0 → real registers stay empty</div>
      <div class="ll err">no coordinates, elevations or materials asserted</div>
      <div class="ll sig">inventory honesty gate: TRUE</div>
      <div class="ll ok">A_RICHAT / B_GIZA / C_ASTRAEA: not_evaluable</div>
      <div class="ll sync">rebuild: python build_atlas_schematic.py</div>
    </div>
  </div>
</div>

<div class="col" id="center-col">
  <div class="layer-tabs">
    <div class="ltab active" data-layer="relation">01 RELATION SKELETON</div>
    <div class="ltab" data-layer="spatial">02 SPATIAL 3D SKELETON</div>
  </div>
  <div class="layer-view" id="view-relation">
    <div class="pnl map-panel">
      <div class="pnl-title">[ 05 ] <em>RELATION MAP — SCHEMATIC</em><span id="map-count">0 relations</span></div>
      <canvas id="map"></canvas>
      <div class="map-cap">РАСПОЛОЖЕНИЕ УЗЛОВ НА ЭКРАНЕ НЕ ЯВЛЯЕТСЯ ГЕОГРАФИЧЕСКИМ. СВЯЗЕЙ НЕТ — ИСТОЧНИКИ НЕ ПРИСОЕДИНЕНЫ.</div>
    </div>
  </div>
  <div class="layer-view hidden" id="view-spatial">
    <div class="spatial-grid">
      <div class="sp-col">
        <div class="pnl">
          <div class="pnl-title">[ S1 ] <em>POINT INDEX</em><span>__N_GPMP__ / __N_MAIN__ + __N_SECOND__</span></div>
          <div class="sp-search" id="sp-search" contenteditable="true">SEARCH ID / NAME</div>
          <div class="mono-line" style="margin-top:6px">CONTROL STATIONS — NOT ARCHAEOLOGICAL OBJECTS</div>
        </div>
        <div class="pnl grow"><div class="sp-list" id="sp-list"></div></div>
      </div>
      <div class="sp-col" id="sp-center">
        <div class="pnl sp-canvas-panel">
          <div class="pnl-title">[ S2 ] <em>GPMP CONTROL NETWORK — 3D PROJECTION</em><span id="sp-count">__N_GPMP__ POINTS</span></div>
          <canvas id="spatial-canvas"></canvas>
          <div class="sp-cap">SOURCE POINTS / NOT A TERRAIN MODEL. GRID = GRAPHIC SUPPORT ONLY.</div>
        </div>
        <div class="pnl sp-controls">
          <div class="pnl-title">[ S3 ] <em>VIEW CONTROL</em></div>
          <div class="sp-control">
            <div class="sp-btn on" data-toggle="main">MAIN __N_MAIN__</div>
            <div class="sp-btn on" data-toggle="secondary">SECONDARY __N_SECOND__</div>
            <div class="sp-btn on" data-toggle="labels">LABELS</div>
            <div class="sp-btn on" data-toggle="grid">GRID</div>
            <div class="sp-btn" data-act="ex-down">EX DOWN</div>
            <div class="sp-btn" id="ex-value">EX 1.0</div>
            <div class="sp-btn" data-act="ex-up">EX UP</div>
            <div class="sp-btn" data-act="reset">RESET VIEW</div>
          </div>
          <div class="axis-key">VERTICAL EXAGGERATION DEFAULT = 1.0 · SOURCE VALUES UNCHANGED</div>
          <div class="legend-row"><span class="legend-mark circle"></span>MAIN TRAVERSE — CIRCLE</div>
          <div class="legend-row"><span class="legend-mark diamond"></span>SECONDARY NETWORK — DIAMOND</div>
          <div class="legend-row">X EASTING / Y NORTHING / Z ELEVATION</div>
        </div>
      </div>
      <div class="sp-col">
        <div class="pnl">
          <div class="pnl-title">[ S4 ] <em>SELECTED POINT PASSPORT</em></div>
          <div class="passport" id="sp-passport">SELECT A CONTROL POINT.</div>
        </div>
        <div class="pnl">
          <div class="pnl-title">[ S5 ] <em>SOURCE PROVENANCE</em></div>
          <div class="passport" id="sp-provenance"></div>
        </div>
        <div class="pnl grow">
          <div class="pnl-title">[ S6 ] <em>IDEALIZATION STATUS</em></div>
          <div class="passport" id="sp-models"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="col">
  <div class="pnl">
    <div class="pnl-title">[ 03 ] <em>MODELLING TIERS</em></div>
    __TIER_ROWS__
  </div>
  <div class="pnl">
    <div class="pnl-title">[ 07 ] <em>RELATION FAMILIES</em><span>__N_REL_CLASSES__</span></div>
    __RELATION_ROWS__
  </div>
  <div class="pnl">
    <div class="pnl-title">[ 08 ] <em>EPISTEMIC STATUSES</em></div>
    <div class="rrow"><span>established_documented</span><span class="zero">0</span></div>
    <div class="rrow"><span>inferred_indirect</span><span class="zero">0</span></div>
    <div class="rrow"><span>hypothesized_unverified</span><span class="zero">0</span></div>
    <div class="mono-line" style="margin-top:6px">Статусы не объединяются. Синтетика не становится established.</div>
  </div>
  <div class="pnl">
    <div class="pnl-title">[ 09 ] <em>COVERAGE / INCOMPLETENESS</em></div>
    __COVERAGE_ROWS__
    <div class="mono-line" style="margin-top:6px">Отсутствие в каталоге не есть отсутствие в системе.</div>
  </div>
  <div class="pnl grow">
    <div class="pnl-title">[ 10 ] <em>PROVENANCE OF THIS VIEW</em></div>
    <div class="row"><span class="lbl">ATLAS</span><span class="val w">GIZA_RELATION_FIRST_ATLAS_SCHEMATIC</span></div>
    <div class="row"><span class="lbl">EXTERNAL CITATIONS</span><span class="val r">false</span></div>
    <div class="row"><span class="lbl">COORDINATE CLAIMS</span><span class="val r">false</span></div>
    <div class="row"><span class="lbl">SOURCE SHA</span><span class="val c">__SHA__</span></div>
    <div class="row"><span class="lbl">LIVE ADAPTERS</span><span class="val r">0</span></div>
    <div class="row"><span class="lbl">PROMOTABLE CLAIMS</span><span class="val r">0</span></div>
    <div class="mono-line" style="margin-top:8px">Это средство отображения состояния доказательной базы. Оно не заменяет исследование Гизы.</div>
  </div>
</div>
</main>

<footer>
  <div class="ft">EQUIVALENT <em>NONE</em></div>
  <div class="ft">VERIFIED <em>0</em></div>
  <div class="ft">GEODETIC <em>NO</em></div>
  <div class="ft">MODE <em>NOT_EVALUABLE</em></div>
  <div style="margin-left:auto;color:var(--border);letter-spacing:2px;">GIZA PRIME // DUAL ATLAS // RELATION + SPATIAL // OFFLINE</div>
</footer>

<script id="spatial-snapshot" type="application/json">
__SPATIAL_SNAPSHOT__
</script>
<script id="atlas-snapshot" type="application/json">
__SNAPSHOT__
</script>
<script>
/* No network, no timers, no controls. Display-only rendering of a validated snapshot. */
const ATLAS = JSON.parse(document.getElementById('atlas-snapshot').textContent);
(function draw(){
  const cv = document.getElementById('map');
  const ctx = cv.getContext('2d');
  const W = cv.width = cv.offsetWidth || 900;
  const H = cv.height = cv.offsetHeight || 500;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle='rgba(5,5,15,0.4)'; ctx.fillRect(0,0,W,H);
  const cx=W/2, cy=H/2;
  const R=Math.max(80, Math.min(W*0.44, H*0.46));
  ctx.setLineDash([4,8]); ctx.strokeStyle='rgba(245,166,35,0.20)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.arc(cx,cy,R*0.55,0,2*Math.PI); ctx.stroke();
  ctx.setLineDash([3,10]); ctx.strokeStyle='rgba(245,166,35,0.10)';
  ctx.beginPath(); ctx.arc(cx,cy,R*1.08,0,2*Math.PI); ctx.stroke();
  ctx.setLineDash([]); ctx.strokeStyle='rgba(245,166,35,0.28)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.arc(cx,cy,R,0,2*Math.PI); ctx.stroke();
  const n = ATLAS.slots.length;
  ATLAS.slots.forEach((slot,i)=>{
    const a = -Math.PI/2 + (2*Math.PI*i)/n;
    const x = cx + R*Math.cos(a), y = cy + R*Math.sin(a);
    ctx.beginPath(); ctx.arc(x,y,5,0,2*Math.PI);
    ctx.fillStyle = slot.natural_structure ? '#8855ff' : '#f5a623';
    ctx.shadowColor = ctx.fillStyle; ctx.shadowBlur = 12; ctx.fill(); ctx.shadowBlur = 0;
  });
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.font='bold '+Math.max(18,Math.min(36,Math.floor(W/26)))+'px Unbounded,Arial Black,sans-serif';
  ctx.fillStyle='#ff3c54'; ctx.fillText('0 VERIFIED RELATIONS',cx,cy-8);
  ctx.font=Math.max(10,Math.min(16,Math.floor(W/70)))+'px Martian Mono,Consolas,monospace';
  ctx.fillStyle='#5a3800'; ctx.fillText('NODE POSITIONS = DISPLAY LAYOUT ONLY',cx,cy+22);
})();
</script>
<script>
/* LAYER 02 — interactive projection of source control points.
   No network, no timers, no external libraries, no mutation of source values. */
(function spatialLayer(){
  const SP = JSON.parse(document.getElementById('spatial-snapshot').textContent);
  const origin = SP.derived_geometry.centering_origin;
  const canvas = document.getElementById('spatial-canvas');
  const context = canvas.getContext('2d');
  const points = SP.points.map(function(p){
    return {
      id: p.point_id, name: p.name, network: p.network,
      x: p.local_coordinates.easting, y: p.local_coordinates.northing,
      z: p.local_coordinates.elevation,
      lon: p.longitude_latitude.longitude, lat: p.longitude_latitude.latitude,
      kmlz: p.longitude_latitude.kml_z, description: p.description,
      system: p.local_coordinates.coordinate_system, datum: p.datum_status,
      extraction: p.extraction
    };
  });
  const initial = {yaw:-0.70, pitch:0.45, zoom:1.0, panX:0, panY:0, ex:1.0};
  const view = Object.assign({}, initial, {
    labels:true, grid:true, main:true, secondary:true,
    selected:null, dragging:false, dragMode:'rotate', lastX:0, lastY:0, moved:0
  });
  const exaggerations = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0];
  let width = 800, height = 500, scale = 1, baseRadius = 1, projected = [];

  function escapeText(value){
    return String(value).replace(/[&<>"]/g, function(ch){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch];
    });
  }
  function computeRadius(){
    let r = 1;
    points.forEach(function(p){
      const dx = p.x - origin.easting;
      const dy = p.y - origin.northing;
      const dz = p.z - origin.elevation;
      r = Math.max(r, Math.sqrt(dx*dx + dy*dy + dz*dz));
    });
    baseRadius = r;
  }
  function rotate(vector){
    const cy = Math.cos(view.yaw), sy = Math.sin(view.yaw);
    const cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
    const x1 = cy*vector[0] - sy*vector[1];
    const y1 = sy*vector[0] + cy*vector[1];
    return [x1, cp*y1 - sp*vector[2], sp*y1 + cp*vector[2]];
  }
  function projectVector(vector){
    const rotated = rotate(vector);
    return {
      x: width/2 + rotated[0]*scale + view.panX,
      y: height/2 - rotated[1]*scale + view.panY,
      depth: rotated[2]
    };
  }
  function projectPoint(p){
    return projectVector([
      p.x - origin.easting,
      p.y - origin.northing,
      (p.z - origin.elevation)*view.ex
    ]);
  }
  function drawSegment(a, b, colour, lineWidth){
    const pa = projectVector(a), pb = projectVector(b);
    context.strokeStyle = colour; context.lineWidth = lineWidth || 1;
    context.beginPath(); context.moveTo(pa.x, pa.y); context.lineTo(pb.x, pb.y);
    context.stroke();
  }
  function drawMarker(p, screen, selected){
    const size = selected ? 9 : 5;
    const colour = p.network === 'main_traverse' ? '#f5a623' : '#8855ff';
    context.save();
    context.translate(screen.x, screen.y);
    if (p.network === 'secondary_network'){
      context.rotate(Math.PI/4);
      context.strokeStyle = colour; context.lineWidth = 1.6;
      context.strokeRect(-size/2, -size/2, size, size);
    } else {
      context.beginPath(); context.arc(0, 0, size/2, 0, 2*Math.PI);
      context.fillStyle = colour; context.fill();
    }
    if (selected){
      context.rotate(p.network === 'secondary_network' ? -Math.PI/4 : 0);
      context.strokeStyle = '#ffcc44'; context.lineWidth = 1;
      context.beginPath(); context.arc(0, 0, 13, 0, 2*Math.PI); context.stroke();
      context.beginPath(); context.moveTo(-18,0); context.lineTo(-9,0);
      context.moveTo(9,0); context.lineTo(18,0);
      context.moveTo(0,-18); context.lineTo(0,-9);
      context.moveTo(0,9); context.lineTo(0,18); context.stroke();
    }
    context.restore();
    if (view.labels){
      context.font = '9px Martian Mono, Consolas, monospace';
      context.fillStyle = selected ? '#ffcc44' : '#5a3800';
      context.textAlign = 'left'; context.textBaseline = 'middle';
      context.fillText(p.name, screen.x + 9, screen.y - 8);
    }
  }
  function draw(){
    if (!canvas.offsetWidth) { return; }
    width = canvas.width = canvas.offsetWidth;
    height = canvas.height = canvas.offsetHeight;
    scale = Math.min(width, height)*0.40/baseRadius*view.zoom;
    context.clearRect(0, 0, width, height);
    context.fillStyle = 'rgba(5,5,15,0.45)'; context.fillRect(0, 0, width, height);
    const reach = baseRadius*1.06;
    if (view.grid){
      const step = reach/5;
      for (let v = -reach; v <= reach + 0.001; v += step){
        drawSegment([v,-reach,0], [v,reach,0], 'rgba(0,212,255,0.07)', 1);
        drawSegment([-reach,v,0], [reach,v,0], 'rgba(0,212,255,0.07)', 1);
      }
    }
    drawSegment([0,0,0], [reach,0,0], 'rgba(245,166,35,0.75)', 1.5);
    drawSegment([0,0,0], [0,reach,0], 'rgba(0,212,255,0.75)', 1.5);
    drawSegment([0,0,0], [0,0,reach], 'rgba(57,255,122,0.85)', 1.5);
    context.font = '10px Unbounded, Arial Black, sans-serif';
    const labelX = projectVector([reach,0,0]);
    const labelY = projectVector([0,reach,0]);
    const labelZ = projectVector([0,0,reach]);
    context.fillStyle = '#f5a623'; context.fillText('X EASTING', labelX.x+6, labelX.y);
    context.fillStyle = '#00d4ff'; context.fillText('Y NORTHING', labelY.x+6, labelY.y);
    context.fillStyle = '#39ff7a'; context.fillText('Z ELEVATION', labelZ.x+6, labelZ.y);
    projected = [];
    points.forEach(function(p){
      if (p.network === 'main_traverse' && !view.main){ return; }
      if (p.network === 'secondary_network' && !view.secondary){ return; }
      projected.push({point:p, screen:projectPoint(p)});
    });
    projected.sort(function(a,b){ return a.screen.depth - b.screen.depth; });
    projected.forEach(function(item){
      drawMarker(item.point, item.screen, view.selected === item.point.id);
    });
    context.font = '9px Martian Mono, Consolas, monospace';
    context.textAlign = 'right'; context.textBaseline = 'bottom';
    context.fillStyle = '#5a3800';
    context.fillText('EX ' + view.ex.toFixed(1) + ' / SOURCE UNCHANGED', width-10, height-8);
  }
  function line(label, value, colour){
    return '<div><span class="lbl">' + escapeText(label) + '</span>' +
      '<span class="val ' + (colour || 'w') + '">' + escapeText(value) + '</span></div>';
  }
  function showPassport(p){
    if (!p){ return; }
    const box = document.getElementById('sp-passport');
    box.innerHTML =
      line('POINT ID', p.id) +
      line('NETWORK', p.network, 'v') +
      line('EASTING', p.x) +
      line('NORTHING', p.y) +
      line('ELEVATION', p.z + '  (description)', 'c') +
      line('LONGITUDE', p.lon) +
      line('LATITUDE', p.lat) +
      line('KML Z', p.kmlz + '  NOT ELEVATION', 'r') +
      line('COORD SYSTEM', p.system, 'v') +
      line('DATUM', p.datum, 'r') +
      line('OBJECT LINK', 'UNRESOLVED', 'r') +
      '<div class="raw">' + escapeText(p.description) + '</div>';
    view.selected = p.id;
    Array.prototype.forEach.call(document.querySelectorAll('.plist-row'), function(row){
      if (row.getAttribute('data-id') === p.id){ row.className = 'plist-row sel'; }
      else { row.className = 'plist-row'; }
    });
    draw();
  }
  function renderProvenance(){
    const source = SP.source, states = SP.provenance_states;
    const box = document.getElementById('sp-provenance');
    let markup = line('SOURCE FILE', source.source_file) +
      line('COMMITTED JSON SHA', source.sha256_of_committed_json.slice(0,16), 'c') +
      line('KML SHA (DECLARED)', source.sha256_of_kml.slice(0,16), 'c') +
      line('PLACEMARKS', source.declared_placemark_count) +
      line('DATUM STATUS', SP.coordinate_system.datum_status, 'r') +
      line('CRS CONVERSION', 'not performed', 'r');
    Object.keys(states).forEach(function(key){
      markup += line(key, states[key] ? 'TRUE' : 'FALSE', states[key] ? 'on' : 'r');
    });
    box.innerHTML = markup;
  }
  function renderModels(){
    const plane = SP.derived_geometry.least_squares_plane;
    const contract = SP.model_contract;
    const box = document.getElementById('sp-models');
    box.innerHTML =
      line('MEASURED_GEOMETRY', SP.counts.total + ' source points') +
      line('DERIVED_GEOMETRY', '1 least-squares plane', 'c') +
      line('FIT RMS', plane.residual_summary.rms.toFixed(3), 'r') +
      line('IDEALIZED_MODEL', contract.instantiated_models_in_this_commit, 'r') +
      line('HYPOTHETICAL_MODEL', 0, 'r') +
      line('UNKNOWN', 'form not identifiable', 'r') +
      '<div class="raw">Plane is derived over control points, NOT terrain. ' +
      'A model record requires model_id, method, parameters, units, assumptions, ' +
      'residual, uncertainty, validity domain, limitations and falsification conditions.</div>';
  }
  function renderList(){
    const box = document.getElementById('sp-list');
    const query = document.getElementById('sp-search').textContent.trim().toLowerCase();
    box.innerHTML = '';
    points.forEach(function(p){
      if (p.network === 'main_traverse' && !view.main){ return; }
      if (p.network === 'secondary_network' && !view.secondary){ return; }
      if (query && query !== 'search id / name' &&
          p.id.toLowerCase().indexOf(query) < 0 &&
          p.name.toLowerCase().indexOf(query) < 0){ return; }
      const row = document.createElement('div');
      row.className = 'plist-row' + (view.selected === p.id ? ' sel' : '');
      row.setAttribute('data-id', p.id);
      row.innerHTML = '<span class="plist-id">' + escapeText(p.name) + '</span>' +
        '<span class="plist-net">' + (p.network === 'main_traverse' ? 'MAIN' : 'SEC') + '</span>' +
        '<span class="plist-z">' + p.z.toFixed(2) + '</span>';
      row.addEventListener('click', function(){ showPassport(p); });
      box.appendChild(row);
    });
  }
  computeRadius(); renderProvenance(); renderModels(); renderList();
  window.addEventListener('resize', draw);
  document.getElementById('sp-search').addEventListener('focus', function(){
    if (this.textContent.trim() === 'SEARCH ID / NAME'){ this.textContent = ''; }
  });
  document.getElementById('sp-search').addEventListener('input', renderList);

  Array.prototype.forEach.call(document.querySelectorAll('.ltab'), function(tab){
    tab.addEventListener('click', function(){
      Array.prototype.forEach.call(document.querySelectorAll('.ltab'), function(other){
        other.className = 'ltab' + (other === tab ? ' active' : '');
      });
      const spatial = tab.getAttribute('data-layer') === 'spatial';
      document.getElementById('view-relation').className =
        'layer-view' + (spatial ? ' hidden' : '');
      document.getElementById('view-spatial').className =
        'layer-view' + (spatial ? '' : ' hidden');
      if (spatial){ draw(); }
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-toggle]'), function(button){
    button.addEventListener('click', function(){
      const key = button.getAttribute('data-toggle');
      view[key] = !view[key];
      button.className = 'sp-btn' + (view[key] ? ' on' : '');
      renderList(); draw();
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-act]'), function(button){
    button.addEventListener('click', function(){
      const action = button.getAttribute('data-act');
      if (action === 'reset'){
        Object.assign(view, initial);
        document.getElementById('ex-value').textContent = 'EX 1.0';
      } else if (action === 'ex-up' || action === 'ex-down'){
        let index = exaggerations.indexOf(view.ex);
        if (index < 0){ index = 1; }
        if (action === 'ex-up'){ index = Math.min(exaggerations.length-1, index+1); }
        else { index = Math.max(0, index-1); }
        view.ex = exaggerations[index];
        document.getElementById('ex-value').textContent = 'EX ' + view.ex.toFixed(1);
      }
      draw();
    });
  });
  canvas.addEventListener('mousedown', function(event){
    event.preventDefault();
    view.dragging = true; view.moved = 0;
    view.dragMode = (event.button === 2 || event.shiftKey) ? 'pan' : 'rotate';
    view.lastX = event.clientX; view.lastY = event.clientY;
    canvas.className = 'dragging';
  });
  window.addEventListener('mousemove', function(event){
    if (!view.dragging){ return; }
    const dx = event.clientX - view.lastX, dy = event.clientY - view.lastY;
    view.moved += Math.abs(dx) + Math.abs(dy);
    view.lastX = event.clientX; view.lastY = event.clientY;
    if (view.dragMode === 'pan'){ view.panX += dx; view.panY += dy; }
    else { view.yaw += dx*0.008; view.pitch += dy*0.008;
           view.pitch = Math.max(-1.4, Math.min(1.4, view.pitch)); }
    draw();
  });
  window.addEventListener('mouseup', function(event){
    if (!view.dragging){ return; }
    view.dragging = false; canvas.className = '';
    if (view.moved < 4 && event.target === canvas){
      const rect = canvas.getBoundingClientRect();
      const mx = event.clientX - rect.left, my = event.clientY - rect.top;
      let best = null, bestDistance = 14*14;
      projected.forEach(function(item){
        const d = (item.screen.x-mx)*(item.screen.x-mx) +
                  (item.screen.y-my)*(item.screen.y-my);
        if (d < bestDistance){ bestDistance = d; best = item.point; }
      });
      if (best){ showPassport(best); }
    }
  });
  canvas.addEventListener('contextmenu', function(event){ event.preventDefault(); });
  canvas.addEventListener('wheel', function(event){
    event.preventDefault();
    view.zoom = Math.max(0.35, Math.min(4.0,
      view.zoom * (event.deltaY < 0 ? 1.12 : 0.89)));
    draw();
  });
})();
</script>
</body>
</html>
'''


def main() -> str:
    snapshot = build_snapshot()
    spatial = build_spatial_snapshot()
    path = os.path.join(HERE, OUTPUT)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_html(snapshot, spatial))
    write_import_report()
    return path


if __name__ == "__main__":
    print(main())
