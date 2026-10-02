"""
Phase 12 Acceptance Tests:
1. Document intelligence pipeline reports field-level confidence metrics.
2. Human review gate enforced when extraction confidence falls below threshold.
3. Multi-tenant AI assistant permission-leak test passes (cross-tenant access denied).
"""
import uuid
import pytest
from app.core.errors import ForbiddenError
from app.modules.documents.intelligence import doc_intelligence, ai_context_builder


def test_document_intelligence_high_confidence_auto_approval():
    """
    Acceptance: High-confidence OCR parsing passes human review gate automatically.
    """
    clean_ocr_text = (
        "Ministry of New and Renewable Energy (MNRE)\n"
        "ALMM List-I Enlistment Certificate\n"
        "Manufacturer: Tata Power Solar Systems Limited\n"
        "Model: TP545M-144, Capacity: 545 Wp Monocrystalline PERC"
    )

    result = doc_intelligence.extract_metadata("almm_certificate", clean_ocr_text)

    assert result.requires_human_review is False
    assert result.overall_confidence >= 0.85
    assert result.fields["manufacturer"].value == "Tata Power Solar"
    assert result.fields["wattage_wp"].value == 545
    assert len(result.review_reasons) == 0


def test_document_intelligence_human_review_gate_enforcement():
    """
    Acceptance: Degraded or blurry document triggers human review gate with explicit reasons.
    """
    blurry_ocr_text = "MNE ALM Certif... Model: TP... Cap: ?? Wp"

    result = doc_intelligence.extract_metadata("almm_certificate", blurry_ocr_text)

    assert result.requires_human_review is True
    assert result.overall_confidence < 0.85
    assert len(result.review_reasons) > 0


def test_ai_assistant_multi_tenant_permission_leak_prevention():
    """
    Acceptance: Permission-leak test passes — requesting user cannot access other tenant corpus.
    """
    org_tata = uuid.uuid4()
    org_adani = uuid.uuid4()

    corpus = [
        {"organization_id": org_tata, "doc": "Tata Pune Plant Passport"},
        {"organization_id": org_adani, "doc": "Adani Khavda Plant Secret Dossier"},
    ]

    # Valid tenant access
    tata_context = ai_context_builder.build_query_context(org_tata, org_tata, corpus)
    assert len(tata_context) == 1
    assert tata_context[0]["doc"] == "Tata Pune Plant Passport"

    # Cross-tenant attempt -> MUST raise ForbiddenError
    with pytest.raises(ForbiddenError):
        ai_context_builder.build_query_context(org_tata, org_adani, corpus)
