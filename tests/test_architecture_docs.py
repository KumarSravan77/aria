from pathlib import Path


def test_architecture_doc_exists_and_has_invariant():
    doc = Path("docs/architecture/ARIA_SYSTEM_ARCHITECTURE.md")
    assert doc.exists()
    text = doc.read_text()
    assert "AI recommends" in text
    assert "ReBAC authorizes" in text
    assert "Approval" in text


def test_threat_model_doc_exists_and_has_controls():
    doc = Path("docs/security/ARIA_THREAT_MODEL.md")
    assert doc.exists()
    text = doc.read_text()
    assert "Spoofed webhook" in text
    assert "Prompt Injection" in text
    assert "HMAC" in text
    assert "ReBAC" in text
