"""Medical Document Classification Service"""
import os
import google.genai as genai
from app.core.config import settings
from app.core.schemas import MedicalDocumentType, ClassificationResult
from dotenv import load_dotenv

load_dotenv()

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_CATEGORIES = {
    "CLINICAL_NOTE":      MedicalDocumentType.CLINICAL_NOTE,
    "RADIOLOGY_REPORT":   MedicalDocumentType.RADIOLOGY_REPORT,
    "PRESCRIPTION":       MedicalDocumentType.PRESCRIPTION,
    "LAB_REPORT":         MedicalDocumentType.LAB_REPORT,
    "DISCHARGE_SUMMARY":  MedicalDocumentType.DISCHARGE_SUMMARY,
    "PATHOLOGY_REPORT":   MedicalDocumentType.PATHOLOGY_REPORT,
    "OPERATIVE_REPORT":   MedicalDocumentType.OPERATIVE_REPORT,
    "CONSULTATION_NOTE":  MedicalDocumentType.CONSULTATION_NOTE,
    "ED_NOTE":            MedicalDocumentType.ED_NOTE,
    "PROGRESS_NOTE":      MedicalDocumentType.PROGRESS_NOTE,
    "UNKNOWN":            MedicalDocumentType.UNKNOWN,
}

_PROMPT_TEMPLATE = """You are a medical document classifier. Classify the following clinical document excerpt into EXACTLY ONE of these categories:

1. CLINICAL_NOTE       – General clinical or SOAP note (GP, outpatient, inpatient)
2. RADIOLOGY_REPORT    – Imaging report (CT, MRI, X-Ray, Ultrasound, PET, nuclear medicine)
3. PRESCRIPTION        – Medication prescription or drug order sheet
4. LAB_REPORT          – Laboratory / blood test results (CBC, metabolic panel, urinalysis, cultures)
5. DISCHARGE_SUMMARY   – Hospital discharge summary or transfer summary
6. PATHOLOGY_REPORT    – Surgical pathology, biopsy, cytology, or histology report
7. OPERATIVE_REPORT    – Operative / surgical note or procedure note
8. CONSULTATION_NOTE   – Specialist consultation letter or inpatient consult note
9. ED_NOTE             – Emergency department triage or physician note
10. PROGRESS_NOTE      – Ward round note or outpatient follow-up note
11. UNKNOWN            – Cannot be determined or is not a medical document

Document excerpt (first 2000 characters):
---
{sample}
---

Respond in this exact format (no extra text):
CATEGORY: [one of the category names above]
CONFIDENCE: [0.0 to 1.0]
REASONING: [one sentence explanation]
"""


def classify_document(text: str) -> ClassificationResult:
    sample = text[:2000]
    prompt = _PROMPT_TEMPLATE.format(sample=sample)

    try:
        response = _client.models.generate_content(
            model=os.getenv("GEMINI_MODEL"),
            contents=prompt,
        )

        category   = MedicalDocumentType.UNKNOWN
        confidence = 0.7
        reasoning  = ""

        for line in response.text.strip().split("\n"):
            if line.startswith("CATEGORY:"):
                key      = line.split(":", 1)[1].strip().upper()
                category = _CATEGORIES.get(key, MedicalDocumentType.UNKNOWN)
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    confidence = 0.7
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()

        return ClassificationResult(
            document_type=category,
            confidence=confidence,
            reasoning=reasoning,
        )

    except Exception as e:
        print(f"Classification error: {e}")
        return ClassificationResult(
            document_type=MedicalDocumentType.UNKNOWN,
            confidence=0.5,
            reasoning=f"Classification failed: {str(e)}",
        )
