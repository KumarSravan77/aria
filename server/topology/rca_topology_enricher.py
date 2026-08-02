from __future__ import annotations
from typing import Any


def enrich_rca_with_topology(rca_markdown: str, blast_radius: dict[str, Any]) -> str:
    """Append a topology and blast-radius section to an existing RCA draft."""
    if not blast_radius or not blast_radius.get("root_service"):
        return rca_markdown

    root = blast_radius["root_service"]
    affected = blast_radius.get("all_affected_services", [])
    customer_facing = blast_radius.get("customer_facing_impact", [])
    upstream = blast_radius.get("upstream_callers", [])
    impact = blast_radius.get("impact_level", "unknown")
    score = blast_radius.get("blast_radius_score", 0)

    lines = [
        "",
        "## Topology and Blast Radius",
        "",
        f"**Root service:** `{root}`  ",
        f"**Impact level:** {impact.upper()} (score={score})",
        "",
    ]

    if upstream:
        lines.append(f"**Upstream callers of {root}:** " + ", ".join(f"`{s}`" for s in upstream))
    if affected:
        lines.append(f"**Downstream services affected ({len(affected)}):** " + ", ".join(f"`{s}`" for s in affected))
    else:
        lines.append(f"**Downstream services affected:** none detected in dependency graph")

    if customer_facing:
        lines.append(f"**Customer-facing services in blast radius:** " + ", ".join(f"`{s}`" for s in customer_facing))
        lines.append("  → Customer impact is likely. Notify on-call and stakeholders immediately.")

    lines.extend([
        "",
        "### Propagation Chain",
        f"Failure origin: `{root}` → downstream propagation detected across {len(affected)} service(s).",
        blast_radius.get("recommendation", ""),
    ])

    return rca_markdown + "\n".join(lines)
