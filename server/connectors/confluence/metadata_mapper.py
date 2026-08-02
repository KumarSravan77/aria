from __future__ import annotations

import re
from typing import Any


def _first_match(text: str, patterns: list[str], default: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip().lower()
    return default


def infer_confluence_metadata(page: dict[str, Any]) -> dict[str, Any]:
    title = page.get("title", "Untitled Confluence Page")
    body = page.get("body", "") or page.get("content", "") or ""
    labels = [str(x).lower() for x in page.get("labels", [])]
    combined = f"{title}\n{body}\n{' '.join(labels)}"

    service = page.get("service") or _first_match(
        combined,
        [r"service:\s*([a-zA-Z0-9_.-]+)", r"services?:\s*([a-zA-Z0-9_.-]+)"],
        "general",
    )
    team = page.get("team") or _first_match(combined, [r"team:\s*([a-zA-Z0-9_.-]+)", r"owner team:\s*([a-zA-Z0-9_.-]+)"], "platform")
    doc_type = page.get("doc_type")
    if not doc_type:
        if "rca" in combined or "postmortem" in combined:
            doc_type = "rca"
        elif "sop" in combined or "procedure" in combined:
            doc_type = "sop"
        elif "runbook" in combined:
            doc_type = "runbook"
        else:
            doc_type = "wiki"

    return {
        "source": "confluence",
        "space": page.get("space", "SRE"),
        "page_id": str(page.get("page_id") or page.get("id") or title),
        "title": title,
        "service": service,
        "team": team,
        "environment": page.get("environment", "prod"),
        "doc_type": doc_type,
        "last_updated": page.get("last_updated", "unknown"),
        "path": f"confluence://{page.get('space', 'SRE')}/{page.get('page_id') or page.get('id') or title}",
    }
