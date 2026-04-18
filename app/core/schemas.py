"""Pydantic Models and Schemas for MedExtract Clinical Assistant"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MedicalDocumentType(str, Enum):
    CLINICAL_NOTE = "clinical_note"
    RADIOLOGY_REPORT = "radiology_report"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    PATHOLOGY_REPORT = "pathology_report"
    OPERATIVE_REPORT = "operative_report"
    CONSULTATION_NOTE = "consultation_note"
    ED_NOTE = "ed_note"
    PROGRESS_NOTE = "progress_note"
    UNKNOWN = "unknown"


class SourceSpan(BaseModel):
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    alignment_status: Optional[str] = None

    def snippet(self, text: str, context: int = 40) -> str:
        """Return a short snippet of source text around this span."""
        if self.char_start is None or self.char_end is None or not text:
            return ""
        start = max(0, self.char_start - context)
        end = min(len(text), self.char_end + context)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end]}{suffix}"


class ClinicalExtractionItem(BaseModel):
    extraction_class: str
    extraction_text: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_span: Optional[SourceSpan] = None
    group_key: Optional[str] = None


class MedicationRecord(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    indication: Optional[str] = None
    special_instruction: Optional[str] = None
    source_spans: Dict[str, Optional[SourceSpan]] = Field(default_factory=dict)


class RadiologyFinding(BaseModel):
    finding: str
    body_part: Optional[str] = None
    laterality: Optional[str] = None
    character: Optional[str] = None
    measurement: Optional[str] = None
    impression: Optional[str] = None
    recommendation: Optional[str] = None
    severity: Optional[str] = None
    source_spans: Dict[str, Optional[SourceSpan]] = Field(default_factory=dict)


class LabResult(BaseModel):
    test_name: str
    result_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None
    panel_name: Optional[str] = None
    source_spans: Dict[str, Optional[SourceSpan]] = Field(default_factory=dict)


class DocumentAnalysis(BaseModel):
    document_id: str
    filename: str
    document_type: MedicalDocumentType
    classification_confidence: float
    classification_reasoning: str = ""
    extractions: List[ClinicalExtractionItem] = Field(default_factory=list)
    medication_records: List[MedicationRecord] = Field(default_factory=list)
    radiology_findings: List[RadiologyFinding] = Field(default_factory=list)
    lab_results: List[LabResult] = Field(default_factory=list)
    diagnoses: List[str] = Field(default_factory=list)
    raw_text: str = ""
    pdf_url: str = ""
    jsonl_url: str = ""


class MedExtractResponse(BaseModel):
    session_id: str
    document_count: int
    documents: List[DocumentAnalysis]
    all_medications: List[MedicationRecord] = Field(default_factory=list)
    all_findings: List[RadiologyFinding] = Field(default_factory=list)
    all_lab_results: List[LabResult] = Field(default_factory=list)
    all_diagnoses: List[str] = Field(default_factory=list)
    session_pdf_url: str = ""
    session_jsonl_url: str = ""


class ClassificationResult(BaseModel):
    document_type: MedicalDocumentType
    confidence: float
    reasoning: str


class ExtractionTemplate(BaseModel):
    prompt_description: str
    examples: List[Any]
    extraction_classes: List[str]
    report_sections: List[str]
