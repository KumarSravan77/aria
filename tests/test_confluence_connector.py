from pathlib import Path
from server.connectors.confluence.confluence_client import ConfluenceClient
from server.connectors.confluence.confluence_ingestor import normalize_page_for_vector_store
from server.connectors.confluence.metadata_mapper import infer_confluence_metadata


def test_confluence_local_pages_map_to_rebac_metadata():
    pages = ConfluenceClient().load_local_pages(Path("examples/confluence/pages.json"))
    metadata = infer_confluence_metadata(pages[0])
    assert metadata["source"] == "confluence"
    assert metadata["service"] == "checkout-api"
    assert metadata["team"] == "payments"
    assert metadata["doc_type"] == "runbook"


def test_confluence_ingestor_outputs_vector_chunks():
    page = {
        "page_id": "p1",
        "space": "SRE",
        "title": "Checkout Runbook",
        "service": "checkout-api",
        "team": "payments",
        "body": "Service: checkout-api\nTeam: payments\nCheck latency and errors.",
    }
    ids, docs, metas = normalize_page_for_vector_store(page)
    assert ids[0].startswith("confluence::p1::")
    assert "Checkout Runbook" in docs[0]
    assert metas[0]["service"] == "checkout-api"
