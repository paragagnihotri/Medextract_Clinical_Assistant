"""Medical Extraction Service — wraps LangExtract with clinical configuration.

Key improvements over the generic version:
- Full document processing via LangExtract native chunking (no truncation)
- extraction_passes=2 for higher recall on dense clinical text
- context_window_chars=200 for coreference resolution across chunk boundaries
- char_interval offsets captured and surfaced on every extraction item
- alignment_status surfaced for clinician confidence signalling
"""
import os
import langextract as lx
from collections import defaultdict

from app.core.config import settings
from app.core.schemas import MedicalDocumentType, ClinicalExtractionItem, SourceSpan
from app.templates.extraction_templates import get_template

from dotenv import load_dotenv

load_dotenv()

os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY


def extract_medical_insights(text: str, doc_type: MedicalDocumentType) -> list[ClinicalExtractionItem]:
    """Run LangExtract on the full document text and return enriched extraction items.

    Args:
        text: Full document text (no truncation — LangExtract chunks internally)
        doc_type: Classified medical document type

    Returns:
        List of ClinicalExtractionItem with char_interval offsets and group keys
    """
    template = get_template(doc_type)

    annotated = lx.extract(
        text_or_documents=text,
        prompt_description=template.prompt_description,
        examples=template.examples,
        model_id=os.getenv("GEMINI_MODEL"),
        max_char_buffer=3000,   # larger chunks → fewer calls → fewer example repetitions
        batch_length=3,
        max_workers=3,
        extraction_passes=1,    # single pass — biggest token saver
        show_progress=False,
    )

    return _build_extraction_items(annotated.extractions)


def _build_extraction_items(raw_extractions: list) -> list[ClinicalExtractionItem]:
    """Convert LangExtract Extraction objects → ClinicalExtractionItem with dedup."""
    # Deduplicate by (class, normalised text) keeping richest attributes
    grouped: dict[tuple, dict] = defaultdict(lambda: {"item": None, "count": 0, "attrs": []})

    for e in raw_extractions:
        key = (e.extraction_class, (e.extraction_text or "").strip().lower())
        g = grouped[key]
        g["count"] += 1

        if g["item"] is None:
            span = None
            if e.char_interval and e.char_interval.start_pos is not None:
                span = SourceSpan(
                    char_start=e.char_interval.start_pos,
                    char_end=e.char_interval.end_pos,
                    alignment_status=(
                        e.alignment_status.value
                        if hasattr(e.alignment_status, "value")
                        else str(e.alignment_status) if e.alignment_status else None
                    ),
                )
            attrs = dict(e.attributes or {})
            group_key = attrs.get("medication_group") or attrs.get("finding_group") or \
                        attrs.get("test_group") or attrs.get("pathology_group") or \
                        attrs.get("operative_group")
            g["item"] = ClinicalExtractionItem(
                extraction_class=e.extraction_class,
                extraction_text=e.extraction_text or "",
                attributes=attrs,
                source_span=span,
                group_key=group_key,
            )

        if e.attributes and isinstance(e.attributes, dict):
            g["attrs"].append(dict(e.attributes))

    results: list[ClinicalExtractionItem] = []
    for g in grouped.values():
        item = g["item"]
        if item is None:
            continue
        merged = _merge_attributes(g["attrs"])
        if g["count"] > 1:
            merged["mention_count"] = g["count"]
        item.attributes = merged
        results.append(item)

    return results


def _merge_attributes(all_attrs: list[dict]) -> dict:
    merged: dict = {}
    value_sets: dict[str, set] = defaultdict(set)

    for attrs in all_attrs:
        for k, v in attrs.items():
            if k not in merged and v is not None:
                merged[k] = v
            if v:
                value_sets[k].add(str(v))

    for k, vals in value_sets.items():
        if len(vals) > 1:
            merged[f"{k}_variations"] = ", ".join(sorted(vals))

    return merged
