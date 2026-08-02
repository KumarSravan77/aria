from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from server.platform.reports.markdown_report import MarkdownServiceReviewReportGenerator


class MarkdownServiceReviewReport:
    """Compatibility wrapper exposing render/write methods."""

    def __init__(self) -> None:
        self.generator = MarkdownServiceReviewReportGenerator()

    def render(self, review: Dict[str, Any]) -> str:
        text = self.generator.generate(review)
        return text.replace("# ARIA Service Review", "# ARIA Service Review Report").replace("## Scorecard", "## Scores")

    def write(self, review: Dict[str, Any], output_dir: str, filename: Optional[str] = None) -> str:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        name = filename or f"{review.get('service_id', 'service')}-service-review.md"
        path = out / name
        path.write_text(self.render(review))
        return str(path)
