"""MedExtract API Routes — supports single and multi-document analysis"""
import os
import uuid
import langextract as lx
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.schemas import (
    MedExtractResponse, DocumentAnalysis, MedicalDocumentType,
    ClassificationResult
)
from app.core import database as db
from app.services.document_parser import parse_document
from app.services.classifier import classify_document
from app.services.extractor import extract_medical_insights
from app.services.med_grouper import (
    group_medications, group_radiology_findings,
    group_lab_results, extract_diagnoses
)
from app.services.report_generator import generate_pdf_report
from app.utils.file_handler import save_upload_file, cleanup_old_files

router = APIRouter()

MAX_FILES_PER_REQUEST = 10


@router.post("/analyze", response_model=MedExtractResponse)
async def analyze_documents(files: List[UploadFile] = File(...)):
    """
    Analyse one or more medical documents.

    - Accepts PDF, DOCX, TXT files (up to 10 per request)
    - Auto-detects document type for each file
    - Extracts structured clinical data using LangExtract
    - Returns medication records, radiology findings, lab results
      with character-offset source verification
    """
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_FILES_PER_REQUEST} files per request."
        )

    session_id = str(uuid.uuid4())

    _validate_files(files)

    doc_analyses: List[DocumentAnalysis] = []

    for uploaded_file in files:
        doc_id   = str(uuid.uuid4())
        file_ext = os.path.splitext(uploaded_file.filename)[1].lower()

        try:
            file_path  = await save_upload_file(uploaded_file, session_id)
            text       = parse_document(file_path, file_ext)

            if not text or len(text.strip()) < 30:
                raise HTTPException(
                    status_code=400,
                    detail=f"'{uploaded_file.filename}' appears empty or too short."
                )

            classification = classify_document(text)
            extractions    = extract_medical_insights(text, classification.document_type)

            med_records  = group_medications(extractions)
            rad_findings = group_radiology_findings(extractions)
            lab_results  = group_lab_results(extractions)
            diagnoses    = extract_diagnoses(extractions)

            report_path  = generate_pdf_report(
                doc_analysis=DocumentAnalysis(
                    document_id=doc_id,
                    filename=uploaded_file.filename,
                    document_type=classification.document_type,
                    classification_confidence=classification.confidence,
                    classification_reasoning=classification.reasoning,
                    extractions=extractions,
                    medication_records=med_records,
                    radiology_findings=rad_findings,
                    lab_results=lab_results,
                    diagnoses=diagnoses,
                    raw_text=text,
                ),
                job_id=f"{session_id}/{doc_id}",
                filename=uploaded_file.filename,
                classification=classification,
                document_text=text,
            )

            # Save raw LangExtract JSONL for this document
            jsonl_dir = os.path.join(settings.REPORT_DIR, session_id, doc_id)
            os.makedirs(jsonl_dir, exist_ok=True)
            _save_jsonl(text, extractions, jsonl_dir)

            # Persist to SQLite
            db.save_document(doc_id, session_id, uploaded_file.filename,
                             classification.document_type.value,
                             classification.confidence, file_path)
            db.save_extractions(doc_id, extractions)
            db.save_medication_records(doc_id, med_records)
            db.save_radiology_findings(doc_id, rad_findings)
            db.save_lab_results(doc_id, lab_results)

            doc_analyses.append(DocumentAnalysis(
                document_id=doc_id,
                filename=uploaded_file.filename,
                document_type=classification.document_type,
                classification_confidence=classification.confidence,
                classification_reasoning=classification.reasoning,
                extractions=extractions,
                medication_records=med_records,
                radiology_findings=rad_findings,
                lab_results=lab_results,
                diagnoses=diagnoses,
                raw_text=text,
                pdf_url=f"/api/v1/report/{session_id}/{doc_id}",
                jsonl_url=f"/api/v1/data/{session_id}/{doc_id}",
            ))

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            print(f"Error processing '{uploaded_file.filename}': {e}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process '{uploaded_file.filename}': {str(e)}"
            )

    db.save_session(session_id, len(doc_analyses))
    await cleanup_old_files()

    # Aggregate across all documents
    all_meds    = [m for d in doc_analyses for m in d.medication_records]
    all_finds   = [f for d in doc_analyses for f in d.radiology_findings]
    all_labs    = [l for d in doc_analyses for l in d.lab_results]
    all_diags   = list({d for doc in doc_analyses for d in doc.diagnoses})

    return MedExtractResponse(
        session_id=session_id,
        document_count=len(doc_analyses),
        documents=doc_analyses,
        all_medications=all_meds,
        all_findings=all_finds,
        all_lab_results=all_labs,
        all_diagnoses=all_diags,
        session_pdf_url=f"/api/v1/report/{session_id}",
        session_jsonl_url=f"/api/v1/data/{session_id}",
    )


@router.get("/report/{session_id}/{doc_id}")
async def get_document_report(session_id: str, doc_id: str):
    """Download PDF report for a single document"""
    path = os.path.join(settings.REPORT_DIR, session_id, doc_id, "report.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, media_type="application/pdf",
                        filename=f"medextract_{doc_id}.pdf")


@router.get("/data/{session_id}/{doc_id}")
async def get_document_data(session_id: str, doc_id: str):
    """Download JSONL extraction data for a single document"""
    path = os.path.join(settings.REPORT_DIR, session_id, doc_id, "data.jsonl")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Data not found")
    return FileResponse(path, media_type="application/jsonl",
                        filename=f"data_{doc_id}.jsonl")


@router.get("/history")
async def get_analysis_history():
    """Return recent analysis session history from SQLite"""
    return {"sessions": db.get_session_history(limit=20)}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _validate_files(files: List[UploadFile]):
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"'{f.filename}': unsupported type. Allowed: "
                       f"{', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        f.file.seek(0, 2)
        size = f.file.tell()
        f.file.seek(0)
        if size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"'{f.filename}' exceeds {settings.MAX_FILE_SIZE_MB}MB limit."
            )


def _save_jsonl(text: str, extractions: list, output_dir: str):
    """Reconstruct a minimal AnnotatedDocument and save via LangExtract IO."""
    try:
        import langextract as lx
        from langextract.core.data import AnnotatedDocument, Extraction, CharInterval

        raw_exts = []
        for e in extractions:
            sp = e.source_span
            ci = None
            if sp and sp.char_start is not None:
                ci = CharInterval(start_pos=sp.char_start, end_pos=sp.char_end)
            raw_exts.append(Extraction(
                extraction_class=e.extraction_class,
                extraction_text=e.extraction_text,
                attributes=e.attributes or {},
                char_interval=ci,
            ))

        annotated = AnnotatedDocument(text=text, extractions=raw_exts)
        lx.io.save_annotated_documents(
            [annotated],
            output_name="data.jsonl",
            output_dir=output_dir,
        )
    except Exception as ex:
        print(f"JSONL save warning: {ex}")
