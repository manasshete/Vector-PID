"""Unit tests for deterministic text classification rules."""
import pytest
from src.ocr.text_classifier import TextClassifier, TextClass, classify_by_rules


@pytest.fixture
def classifier():
    return TextClassifier(grok_service=None)


# ---------------------------------------------------------------------------
# Rule-Based Classification Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_class", [
    ("P-1234",            TextClass.PIPE_TAG),
    ("26-P-9087",         TextClass.PIPE_TAG),
    ("p-5678",            TextClass.PIPE_TAG),
    ("26-KZ-902",         TextClass.EQUIPMENT_TAG),
    ("V-100",             TextClass.EQUIPMENT_TAG),
    ("E-200",             TextClass.EQUIPMENT_TAG),
    ('60"',               TextClass.PIPE_SIZE),
    ('2"',                TextClass.PIPE_SIZE),
    ("DN50",              TextClass.PIPE_SIZE),
    ('1-1/2"',            TextClass.PIPE_SIZE),
    ("INSTR. AIR",        TextClass.SERVICE),
    ("FUEL GAS",          TextClass.SERVICE),
    ("COOLING WATER",     TextClass.SERVICE),
    ("NITROGEN",          TextClass.SERVICE),
    ("NOTE 1",            TextClass.ANNOTATION),
    ("NOTE 18",           TextClass.ANNOTATION),
    ("MATCHLINE",         TextClass.DRAWING_REFERENCE),
    ("SEE DWG",           TextClass.DRAWING_REFERENCE),
    ("150mm",             TextClass.DIMENSION),
    ("10ft",              TextClass.DIMENSION),
])
def test_rule_classification(text, expected_class, classifier):
    cls, conf, method = classifier.classify(text)
    assert cls == expected_class, f"Expected {expected_class} for '{text}', got {cls}"
    assert method == "rule"
    assert conf >= 0.85


@pytest.mark.parametrize("text,expected_class", [
    ("26-PIT-9087",              TextClass.INSTRUMENT_TAG),
    ("26-PY-9087B",              TextClass.INSTRUMENT_TAG),
    ("FT-100",                   TextClass.INSTRUMENT_TAG),
    ("26-000001-001",            TextClass.LINE_NUMBER),
    ("63-900001-002",            TextClass.LINE_NUMBER),
    ("SP 108.5",                 TextClass.SPEC_REFERENCE),
    ("COMPRESSOR INLET HEADER",  TextClass.DESCRIPTION),
    ("HP GAS EXPORT COMPRESSOR", TextClass.DESCRIPTION),
    ("L",                        TextClass.GRID_LABEL),
    ("A",                        TextClass.GRID_LABEL),
    ("12",                       TextClass.GRID_LABEL),
])
def test_enhanced_rule_classification(text, expected_class, classifier):
    cls, conf, method = classifier.classify(text)
    assert cls == expected_class, f"Expected {expected_class} for '{text}', got {cls}"
    assert method == "rule"


def test_unknown_text_returns_unknown(classifier):
    cls, conf, method = classifier.classify("XYZZY_INVALID")
    assert cls == TextClass.UNKNOWN
    assert method == "rule"


def test_empty_text_returns_unknown(classifier):
    cls, _, _ = classifier.classify("")
    assert cls == TextClass.UNKNOWN


def test_case_insensitive_matching(classifier):
    cls, _, _ = classifier.classify("instr. air")
    assert cls == TextClass.SERVICE

    cls, _, _ = classifier.classify("note 5")
    assert cls == TextClass.ANNOTATION


def test_batch_classification():
    classifier = TextClassifier(grok_service=None)
    ocr_results = [
        {"id": "TXT-000-0000", "text": "P-1234",       "confidence": 0.95, "bbox": {}, "tile_id": 0},
        {"id": "TXT-000-0001", "text": "INSTR. AIR",   "confidence": 0.92, "bbox": {}, "tile_id": 0},
        {"id": "TXT-000-0002", "text": "UNKNOWN_XYZ",  "confidence": 0.80, "bbox": {}, "tile_id": 0},
    ]
    results = classifier.classify_batch(ocr_results)
    assert len(results) == 3
    assert results[0].classification == TextClass.PIPE_TAG
    assert results[1].classification == TextClass.SERVICE
    assert results[2].classification == TextClass.UNKNOWN
    assert all(r.method == "rule" for r in results)


def test_confidence_capped_by_ocr_confidence(classifier):
    # Rule confidence ~0.98, OCR confidence 0.60 → result must be ≤ 0.60
    cls, conf, _ = classifier.classify('60"', ocr_confidence=0.60)
    assert cls == TextClass.PIPE_SIZE
    assert conf <= 0.60
