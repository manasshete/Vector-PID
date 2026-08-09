"""Enhanced deterministic text classifier for real-world P&IDs."""
from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TextClass(str, Enum):
    PIPE_TAG = "PIPE_TAG"
    EQUIPMENT_TAG = "EQUIPMENT_TAG"
    INSTRUMENT_TAG = "INSTRUMENT_TAG"  # PIT, PY, FT, TT, etc.
    LINE_NUMBER = "LINE_NUMBER"        # 26-000001-001 format
    SPEC_REFERENCE = "SPEC_REFERENCE"  # SP 108.5, SPEC refs
    PIPE_SIZE = "PIPE_SIZE"
    SERVICE = "SERVICE"
    DESCRIPTION = "DESCRIPTION"        # Multi-word equipment/process descriptions
    DIMENSION = "DIMENSION"
    ANNOTATION = "ANNOTATION"
    DRAWING_REFERENCE = "DRAWING_REFERENCE"
    GRID_LABEL = "GRID_LABEL"          # Single letter / 1-2 digit grid markings
    UNKNOWN = "UNKNOWN"


class ClassifiedText(BaseModel):
    id: str
    text: str
    classification: TextClass
    confidence: float = Field(..., ge=0, le=1)
    method: str
    bbox: dict
    tile_id: int


# --- Enhanced Patterns for Real P&IDs ---

# Instrument tags: 26-PIT-9087, 26-PY-9087B, FT-100, TT-200A (ISA-5.1 designations)
INSTRUMENT_TAG_PATTERN = re.compile(
    r"^\d{0,2}-?(PIT|PY|PT|PIC|PDI|PDT|FT|FE|FIC|TT|TE|TIC|LT|LIC|LIT|AT|VT|ZT|XV|HV|PV|FV|TV|CV|SDV|BDV)-\d{3,5}[A-Z]?$",
    re.IGNORECASE,
)

# Line numbers / doc refs: 26-000001-001, 63-900001-002
LINE_NUMBER_PATTERN = re.compile(r"^\d{2,3}-\d{5,7}-\d{3,4}$")

# Spec references: SP 108.5, SPEC 200, ISO 9001
SPEC_PATTERN = re.compile(r"^(SP|SPEC|ISO|ASTM|API)\s*\d+[\.\d]*$", re.IGNORECASE)

# Pipe tags: P-1234, 26-P-9087, allows trailing letters
PIPE_TAG_PATTERN = re.compile(r"^\d{0,2}-?P-\d{3,5}[A-Z]?$", re.IGNORECASE)

# Equipment tags: 26-KZ-902, V-100A, E-200-B
EQUIPMENT_TAG_PATTERN = re.compile(r"^\d{0,2}-?[A-Z]{1,3}-\d{2,5}[A-Z-]?$", re.IGNORECASE)

# Pipe sizes: 60", 2", 1-1/2", DN50, 3"
PIPE_SIZE_PATTERN = re.compile(
    r'^(\d{1,3}["\']|DN\d{2,4}|\d{1,2}-\d{1,2}/\d{1,2}")$', re.IGNORECASE
)

# Annotations: NOTE 1, NOTE 18, NOTE 2A
ANNOTATION_PATTERN = re.compile(r"^NOTE\s+\d+[A-Z]?$", re.IGNORECASE)

# Grid labels: single letter or 1-2 digit number exact match
GRID_LABEL_PATTERN = re.compile(r"^([A-Z]|\d{1,2})$", re.IGNORECASE)

# Dimension pattern: value with unit (mm, m, ft, in, ')
DIMENSION_PATTERN = re.compile(r"^\d+\.?\d*\s*(MM|M|FT|IN|')$", re.IGNORECASE)

# Service keywords
SERVICE_KEYWORDS = {
    "INSTR. AIR", "INSTRUMENT AIR", "FUEL GAS", "COOLING WATER",
    "NITROGEN", "SEAL GAS", "LUBE OIL", "VENT", "DRAIN",
    "HP GAS", "LP GAS", "PRIMARY LEAKAGE", "SECONDARY LEAKAGE",
    "COMPRESSOR", "EXPORT", "IMPORT", "SUCTION", "DISCHARGE",
}

# Description indicators (multi-word technical phrases)
DESCRIPTION_INDICATORS = {
    "HEADER", "COMPRESSOR", "VALVE", "PUMP", "TANK", "FILTER",
    "COOLER", "HEATER", "SEPARATOR", "DRUM", "COLUMN", "REACTOR",
    "INLET", "OUTLET", "STAGE", "SYSTEM", "CONNECTION", "MODULE",
}

# Drawing references
DRAWING_REF_KEYWORDS = {"MATCHLINE", "CONTINUED", "SEE DWG", "REFER TO", "FROM", "TO"}


def classify_by_rules(text: str) -> tuple[Optional[TextClass], float]:
    cleaned = text.strip().upper()
    if not cleaned or len(cleaned) == 0:
        return TextClass.UNKNOWN, 0.0

    # Pipe size (very specific)
    if PIPE_SIZE_PATTERN.match(cleaned):
        return TextClass.PIPE_SIZE, 0.98

    # Annotations
    if ANNOTATION_PATTERN.match(cleaned):
        return TextClass.ANNOTATION, 0.95

    # Spec references
    if SPEC_PATTERN.match(cleaned):
        return TextClass.SPEC_REFERENCE, 0.93

    # Line numbers
    if LINE_NUMBER_PATTERN.match(cleaned):
        return TextClass.LINE_NUMBER, 0.94

    # Instrument tags (before equipment — more specific pattern)
    if INSTRUMENT_TAG_PATTERN.match(cleaned):
        return TextClass.INSTRUMENT_TAG, 0.92

    # Pipe tags
    if PIPE_TAG_PATTERN.match(cleaned):
        return TextClass.PIPE_TAG, 0.94

    # Equipment tags
    if EQUIPMENT_TAG_PATTERN.match(cleaned):
        return TextClass.EQUIPMENT_TAG, 0.91

    # Drawing references
    if any(kw in cleaned for kw in DRAWING_REF_KEYWORDS):
        return TextClass.DRAWING_REFERENCE, 0.85

    # Descriptions: multi-word with technical indicators (before single service keywords)
    words = cleaned.split()
    if len(words) >= 2 and any(ind in cleaned for ind in DESCRIPTION_INDICATORS):
        return TextClass.DESCRIPTION, 0.82

    # Services (exact or substring)
    if cleaned in SERVICE_KEYWORDS or any(kw in cleaned for kw in SERVICE_KEYWORDS):
        return TextClass.SERVICE, 0.88

    # Dimensions
    if DIMENSION_PATTERN.match(cleaned):
        return TextClass.DIMENSION, 0.88

    # Grid labels (single char/number) — lowest priority to avoid false positives
    if GRID_LABEL_PATTERN.match(cleaned):
        return TextClass.GRID_LABEL, 0.70

    return None, 0.0


class TextClassifier:
    def __init__(self, grok_service=None):
        self._grok = grok_service

    def classify(self, text: str, ocr_confidence: float = 1.0) -> tuple[TextClass, float, str]:
        rule_class, rule_conf = classify_by_rules(text)
        if rule_class is not None:
            combined_conf = min(rule_conf, ocr_confidence)
            return rule_class, combined_conf, "rule"

        if self._grok is not None:
            try:
                import asyncio
                grok_result = asyncio.run(self._grok.classify_text(text))
                return (
                    TextClass(grok_result.get("classification", "UNKNOWN")),
                    float(grok_result.get("confidence", 0.5)),
                    "grok",
                )
            except Exception:
                pass

        return TextClass.UNKNOWN, 0.3, "rule"

    def classify_batch(self, ocr_results: list[dict]) -> list[ClassifiedText]:
        classified = []
        for item in ocr_results:
            text = item.get("text", "")
            ocr_conf = item.get("confidence", 0.5)
            classification, conf, method = self.classify(text, ocr_conf)
            classified.append(ClassifiedText(
                id=item.get("id", ""),
                text=text,
                classification=classification,
                confidence=conf,
                method=method,
                bbox=item.get("bbox", {}),
                tile_id=item.get("tile_id", 0),
            ))
        return classified
