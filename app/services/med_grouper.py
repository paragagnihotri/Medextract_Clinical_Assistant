"""MedGrouper — aggregates flat LangExtract extractions into structured clinical records.

Uses the shared group-key attributes defined in extraction_templates.py:
  medication_group  → MedicationRecord
  finding_group     → RadiologyFinding
  test_group        → LabResult
"""
from collections import defaultdict
from typing import List

from app.core.schemas import (
    ClinicalExtractionItem,
    MedicationRecord,
    RadiologyFinding,
    LabResult,
    SourceSpan,
)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def group_medications(extractions: List[ClinicalExtractionItem]) -> List[MedicationRecord]:
    """Group medication-related extractions into MedicationRecord objects."""
    buckets: dict[str, dict] = defaultdict(dict)

    for e in extractions:
        group = (e.attributes or {}).get("medication_group") or e.group_key
        if not group:
            continue

        cls = e.extraction_class
        if cls in ("medication", "treatment_given", "medication_change", "medication_adjustment"):
            buckets[group].setdefault("name", e.extraction_text)
            buckets[group].setdefault("name_span", e.source_span)
            attrs = e.attributes or {}
            if attrs.get("indication"):
                buckets[group]["indication"] = attrs["indication"]
            if attrs.get("change_type"):
                buckets[group]["change_type"] = attrs["change_type"]

        elif cls == "dosage":
            buckets[group]["dosage"] = e.extraction_text
            buckets[group]["dosage_span"] = e.source_span

        elif cls == "route":
            buckets[group]["route"] = e.extraction_text
            buckets[group]["route_span"] = e.source_span

        elif cls == "frequency":
            buckets[group]["frequency"] = e.extraction_text
            buckets[group]["frequency_span"] = e.source_span

        elif cls == "duration":
            buckets[group]["duration"] = e.extraction_text
            buckets[group]["duration_span"] = e.source_span

        elif cls == "indication":
            buckets[group]["indication"] = e.extraction_text
            buckets[group]["indication_span"] = e.source_span

        elif cls == "special_instruction":
            buckets[group]["special_instruction"] = e.extraction_text
            buckets[group]["instruction_span"] = e.source_span

    records: List[MedicationRecord] = []
    for group, data in buckets.items():
        if "name" not in data:
            continue
        spans: dict = {}
        for field, key in [
            ("medication_name", "name_span"),
            ("dosage",          "dosage_span"),
            ("route",           "route_span"),
            ("frequency",       "frequency_span"),
            ("duration",        "duration_span"),
            ("indication",      "indication_span"),
        ]:
            span = data.get(key)
            if isinstance(span, SourceSpan):
                spans[field] = span

        records.append(MedicationRecord(
            medication_name=data.get("name", group),
            dosage=data.get("dosage"),
            route=data.get("route"),
            frequency=data.get("frequency"),
            duration=data.get("duration"),
            indication=data.get("indication"),
            special_instruction=data.get("special_instruction"),
            source_spans=spans,
        ))

    return records


def group_radiology_findings(extractions: List[ClinicalExtractionItem]) -> List[RadiologyFinding]:
    """Group finding-related extractions into RadiologyFinding objects."""
    buckets: dict[str, dict] = defaultdict(dict)

    for e in extractions:
        group = (e.attributes or {}).get("finding_group") or e.group_key
        if not group:
            continue

        cls = e.extraction_class
        if cls == "finding":
            buckets[group].setdefault("finding", e.extraction_text)
            buckets[group].setdefault("finding_span", e.source_span)
            attrs = e.attributes or {}
            for field in ("body_part", "laterality", "character", "severity"):
                if attrs.get(field):
                    buckets[group][field] = attrs[field]

        elif cls == "measurement":
            buckets[group]["measurement"] = e.extraction_text
            buckets[group]["measurement_span"] = e.source_span

        elif cls == "impression":
            buckets[group]["impression"] = e.extraction_text
            buckets[group]["impression_span"] = e.source_span

        elif cls == "recommendation":
            buckets[group]["recommendation"] = e.extraction_text
            buckets[group]["recommendation_span"] = e.source_span

    findings: List[RadiologyFinding] = []
    for group, data in buckets.items():
        if "finding" not in data:
            continue
        spans: dict = {}
        for field, key in [
            ("finding",        "finding_span"),
            ("measurement",    "measurement_span"),
            ("impression",     "impression_span"),
            ("recommendation", "recommendation_span"),
        ]:
            span = data.get(key)
            if isinstance(span, SourceSpan):
                spans[field] = span

        findings.append(RadiologyFinding(
            finding=data["finding"],
            body_part=data.get("body_part"),
            laterality=data.get("laterality"),
            character=data.get("character"),
            measurement=data.get("measurement"),
            impression=data.get("impression"),
            recommendation=data.get("recommendation"),
            severity=data.get("severity"),
            source_spans=spans,
        ))

    return findings


def group_lab_results(extractions: List[ClinicalExtractionItem]) -> List[LabResult]:
    """Group lab-result extractions into LabResult objects."""
    buckets: dict[str, dict] = defaultdict(dict)

    for e in extractions:
        group = (e.attributes or {}).get("test_group") or e.group_key
        if not group:
            continue

        cls = e.extraction_class
        if cls == "lab_test":
            buckets[group].setdefault("name", e.extraction_text)
            buckets[group].setdefault("name_span", e.source_span)
            attrs = e.attributes or {}
            if attrs.get("panel"):
                buckets[group]["panel_name"] = attrs["panel"]

        elif cls == "result_value":
            buckets[group]["result_value"] = e.extraction_text
            buckets[group]["value_span"] = e.source_span

        elif cls == "unit":
            buckets[group]["unit"] = e.extraction_text

        elif cls == "reference_range":
            buckets[group]["reference_range"] = e.extraction_text

        elif cls == "flag":
            buckets[group]["flag"] = e.extraction_text.upper()
            buckets[group]["flag_span"] = e.source_span

        elif cls == "panel_name":
            buckets[group].setdefault("panel_name", e.extraction_text)

    results: List[LabResult] = []
    for group, data in buckets.items():
        if "name" not in data:
            continue
        spans: dict = {}
        for field, key in [
            ("test_name",    "name_span"),
            ("result_value", "value_span"),
            ("flag",         "flag_span"),
        ]:
            span = data.get(key)
            if isinstance(span, SourceSpan):
                spans[field] = span

        results.append(LabResult(
            test_name=data.get("name", group),
            result_value=data.get("result_value"),
            unit=data.get("unit"),
            reference_range=data.get("reference_range"),
            flag=data.get("flag"),
            panel_name=data.get("panel_name"),
            source_spans=spans,
        ))

    return results


def extract_diagnoses(extractions: List[ClinicalExtractionItem]) -> List[str]:
    """Collect unique diagnosis strings from extractions."""
    seen: set = set()
    diags: List[str] = []
    diagnosis_classes = {
        "diagnosis", "admission_diagnosis", "discharge_diagnosis", "ed_diagnosis"
    }
    for e in extractions:
        if e.extraction_class in diagnosis_classes:
            txt = (e.extraction_text or "").strip()
            if txt and txt.lower() not in seen:
                seen.add(txt.lower())
                diags.append(txt)
    return diags
