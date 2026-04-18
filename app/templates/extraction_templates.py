"""Medical Extraction Templates — all 10 clinical document types.

Token-optimised: concise prompt descriptions and minimal but representative
few-shot examples. These are sent with EVERY LangExtract chunk call, so
keeping them small directly reduces total token usage.

Grouping convention:
  medication_group  → links medication + dosage + route + frequency
  finding_group     → links finding + measurement + impression
  test_group        → links lab_test + result_value + unit + flag
"""
from langextract.core.data import ExampleData, Extraction
from app.core.schemas import MedicalDocumentType, ExtractionTemplate


# ─────────────────────────────────────────────────────────────────────────────
# 1. CLINICAL / SOAP NOTE
# ─────────────────────────────────────────────────────────────────────────────
CLINICAL_NOTE_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract clinical entities: medication, dosage, route, frequency, duration, "
        "indication, special_instruction, diagnosis, vital_sign, symptom, allergy, "
        "procedure, follow_up. "
        "Link each medication's components with the same medication_group attribute value."
    ),
    examples=[
        ExampleData(
            text=(
                "Allergies: Penicillin (anaphylaxis). "
                "Dx: Type 2 Diabetes (primary), Hypertension (secondary). "
                "Plan: Metformin 500mg orally twice daily with meals for glycaemic control. "
                "BP: 138/88 mmHg. Follow-up in 4 weeks with HbA1c."
            ),
            extractions=[
                Extraction("allergy", "Penicillin",
                           attributes={"reaction_type": "anaphylaxis"}),
                Extraction("diagnosis", "Type 2 Diabetes",
                           attributes={"diagnosis_type": "primary", "status": "active"}),
                Extraction("diagnosis", "Hypertension",
                           attributes={"diagnosis_type": "secondary", "status": "active"}),
                Extraction("medication", "Metformin",
                           attributes={"medication_group": "Metformin",
                                       "indication": "glycaemic control"}),
                Extraction("dosage", "500mg",
                           attributes={"medication_group": "Metformin"}),
                Extraction("route", "orally",
                           attributes={"medication_group": "Metformin"}),
                Extraction("frequency", "twice daily",
                           attributes={"medication_group": "Metformin"}),
                Extraction("special_instruction", "with meals",
                           attributes={"medication_group": "Metformin"}),
                Extraction("vital_sign", "138/88 mmHg",
                           attributes={"type": "blood_pressure", "value": "138/88",
                                       "unit": "mmHg"}),
                Extraction("follow_up", "Follow-up in 4 weeks with HbA1c",
                           attributes={"timeframe": "4 weeks"}),
            ]
        )
    ],
    extraction_classes=[
        "medication", "dosage", "route", "frequency", "duration",
        "indication", "special_instruction", "diagnosis", "vital_sign",
        "symptom", "allergy", "procedure", "follow_up"
    ],
    report_sections=[
        "Medications", "Diagnoses", "Vital Signs",
        "Symptoms & Allergies", "Procedures", "Follow-up"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. RADIOLOGY REPORT
# ─────────────────────────────────────────────────────────────────────────────
RADIOLOGY_REPORT_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract radiology entities: finding, measurement, impression, recommendation, comparison. "
        "Link each finding's measurement and impression with the same finding_group attribute value. "
        "Include body_part, laterality, character, severity on findings."
    ),
    examples=[
        ExampleData(
            text=(
                "Liver: 2.3 cm hypodense lesion, right hepatic lobe, consistent with simple cyst. "
                "Bilateral renal calculi, largest 4mm on the right. No hydronephrosis. "
                "Impression: Simple hepatic cyst. Bilateral nephrolithiasis. "
                "Recommendation: Urological referral for nephrolithiasis."
            ),
            extractions=[
                Extraction("finding", "hypodense lesion",
                           attributes={"finding_group": "hepatic_cyst",
                                       "body_part": "liver", "laterality": "right",
                                       "character": "hypodense", "severity": "benign"}),
                Extraction("measurement", "2.3 cm",
                           attributes={"finding_group": "hepatic_cyst", "unit": "cm"}),
                Extraction("impression", "Simple hepatic cyst",
                           attributes={"finding_group": "hepatic_cyst"}),
                Extraction("finding", "Bilateral renal calculi",
                           attributes={"finding_group": "nephrolithiasis",
                                       "body_part": "kidneys", "laterality": "bilateral"}),
                Extraction("measurement", "4mm",
                           attributes={"finding_group": "nephrolithiasis", "unit": "mm"}),
                Extraction("impression", "Bilateral nephrolithiasis",
                           attributes={"finding_group": "nephrolithiasis"}),
                Extraction("recommendation", "Urological referral for nephrolithiasis",
                           attributes={"finding_group": "nephrolithiasis",
                                       "urgency": "routine"}),
            ]
        )
    ],
    extraction_classes=["finding", "measurement", "impression", "recommendation", "comparison"],
    report_sections=["Findings", "Measurements", "Impressions", "Recommendations"]
)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PRESCRIPTION
# ─────────────────────────────────────────────────────────────────────────────
PRESCRIPTION_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract prescription entities: medication, dosage, route, frequency, duration, "
        "quantity, refills, indication, special_instruction, prescriber, prescription_date. "
        "Link each drug's components with the same medication_group attribute value."
    ),
    examples=[
        ExampleData(
            text=(
                "Dr. Emily Carter, MD — Cardiology. Date: 10 Apr 2025. "
                "Aspirin 81mg oral once daily, 90 tabs, 3 refills, "
                "for cardiovascular prophylaxis, take with water."
            ),
            extractions=[
                Extraction("prescriber", "Dr. Emily Carter",
                           attributes={"specialty": "Cardiology", "credential": "MD"}),
                Extraction("prescription_date", "10 Apr 2025", attributes={}),
                Extraction("medication", "Aspirin",
                           attributes={"medication_group": "Aspirin",
                                       "indication": "cardiovascular prophylaxis"}),
                Extraction("dosage", "81mg",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("route", "oral",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("frequency", "once daily",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("quantity", "90 tabs",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("refills", "3 refills",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("special_instruction", "take with water",
                           attributes={"medication_group": "Aspirin"}),
            ]
        )
    ],
    extraction_classes=[
        "medication", "dosage", "route", "frequency", "duration",
        "quantity", "refills", "indication", "special_instruction",
        "prescriber", "prescription_date"
    ],
    report_sections=["Prescriptions", "Prescriber Details"]
)


# ─────────────────────────────────────────────────────────────────────────────
# 4. LAB / BLOOD REPORT
# ─────────────────────────────────────────────────────────────────────────────
LAB_REPORT_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract lab entities: lab_test, result_value, unit, reference_range, flag "
        "(HIGH/LOW/NORMAL/CRITICAL), panel_name, collection_date, report_date, "
        "ordering_physician, lab_comment. "
        "Link each test's result/unit/range/flag with the same test_group attribute value."
    ),
    examples=[
        ExampleData(
            text=(
                "CBC. Ordered by Dr. Patel. Collected: 15 Apr 2025. "
                "Haemoglobin: 10.2 g/dL [13.0-17.0] LOW. "
                "WBC: 11.8 x10^9/L [4.0-11.0] HIGH. "
                "Comment: Anaemia with leukocytosis."
            ),
            extractions=[
                Extraction("panel_name", "CBC", attributes={}),
                Extraction("ordering_physician", "Dr. Patel", attributes={}),
                Extraction("collection_date", "15 Apr 2025", attributes={}),
                Extraction("lab_test", "Haemoglobin",
                           attributes={"test_group": "Haemoglobin", "panel": "CBC"}),
                Extraction("result_value", "10.2",
                           attributes={"test_group": "Haemoglobin"}),
                Extraction("unit", "g/dL",
                           attributes={"test_group": "Haemoglobin"}),
                Extraction("reference_range", "13.0-17.0",
                           attributes={"test_group": "Haemoglobin"}),
                Extraction("flag", "LOW",
                           attributes={"test_group": "Haemoglobin"}),
                Extraction("lab_test", "WBC",
                           attributes={"test_group": "WBC", "panel": "CBC"}),
                Extraction("result_value", "11.8",
                           attributes={"test_group": "WBC"}),
                Extraction("flag", "HIGH",
                           attributes={"test_group": "WBC"}),
                Extraction("lab_comment",
                           "Anaemia with leukocytosis", attributes={}),
            ]
        )
    ],
    extraction_classes=[
        "lab_test", "result_value", "unit", "reference_range", "flag",
        "panel_name", "collection_date", "report_date", "ordering_physician", "lab_comment"
    ],
    report_sections=["Lab Results", "Abnormal Values", "Lab Comments"]
)


# ─────────────────────────────────────────────────────────────────────────────
# 5. DISCHARGE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
DISCHARGE_SUMMARY_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract discharge entities: admission_diagnosis, discharge_diagnosis, hospital_course, "
        "medication (discharge), dosage, route, frequency, duration, change_type "
        "(new/continued/discontinued/dose-changed), follow_up_appointment, discharge_condition, "
        "pending_result, patient_instruction. "
        "Link each discharge medication's components with medication_group = drug name."
    ),
    examples=[
        ExampleData(
            text=(
                "Admission Dx: Acute COPD exacerbation. "
                "Discharge Dx: COPD exacerbation resolved. Community-acquired pneumonia. "
                "Condition: Stable. "
                "Discharge meds: Prednisolone 25mg oral once daily for 5 days (new). "
                "Follow-up: Respiratory clinic in 4 weeks. "
                "Pending: Sputum culture. Patient: Avoid smoking."
            ),
            extractions=[
                Extraction("admission_diagnosis", "Acute COPD exacerbation", attributes={}),
                Extraction("discharge_diagnosis", "COPD exacerbation resolved",
                           attributes={"status": "resolved"}),
                Extraction("discharge_condition", "Stable", attributes={}),
                Extraction("medication", "Prednisolone",
                           attributes={"medication_group": "Prednisolone",
                                       "change_type": "new"}),
                Extraction("dosage", "25mg",
                           attributes={"medication_group": "Prednisolone"}),
                Extraction("route", "oral",
                           attributes={"medication_group": "Prednisolone"}),
                Extraction("frequency", "once daily",
                           attributes={"medication_group": "Prednisolone"}),
                Extraction("duration", "for 5 days",
                           attributes={"medication_group": "Prednisolone"}),
                Extraction("follow_up_appointment", "Respiratory clinic in 4 weeks",
                           attributes={"specialty": "Respiratory", "timeframe": "4 weeks"}),
                Extraction("pending_result", "Sputum culture", attributes={}),
                Extraction("patient_instruction", "Avoid smoking", attributes={}),
            ]
        )
    ],
    extraction_classes=[
        "admission_diagnosis", "discharge_diagnosis", "hospital_course",
        "medication", "dosage", "route", "frequency", "duration", "change_type",
        "discharge_condition", "follow_up_appointment", "pending_result", "patient_instruction"
    ],
    report_sections=[
        "Diagnoses", "Hospital Course", "Discharge Medications",
        "Follow-up", "Pending Results", "Patient Instructions"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# 6. PATHOLOGY REPORT
# ─────────────────────────────────────────────────────────────────────────────
PATHOLOGY_REPORT_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract pathology entities: specimen, histological_finding, staging, margin_status, "
        "lymph_node_status, pathological_diagnosis, immunohistochemistry, tumour_size. "
        "Link related entities with pathology_group attribute. "
        "Include grade, morphology on findings; marker and result on IHC."
    ),
    examples=[
        ExampleData(
            text=(
                "Specimen: Right breast core biopsy. "
                "Microscopy: Moderately differentiated invasive ductal carcinoma, grade 2. "
                "Tumour: 18mm. Margins: Clear, 3mm posterior. Nodes: 2/14 positive. "
                "Staging: pT2 N1 M0. IHC: ER positive (90%), HER2 negative. "
                "Diagnosis: Invasive ductal carcinoma, right breast, grade 2, pT2N1M0."
            ),
            extractions=[
                Extraction("specimen", "Right breast core biopsy",
                           attributes={"site": "breast", "laterality": "right",
                                       "collection_method": "core biopsy"}),
                Extraction("histological_finding", "invasive ductal carcinoma",
                           attributes={"pathology_group": "breast_ca", "grade": "2",
                                       "differentiation": "moderately differentiated"}),
                Extraction("tumour_size", "18mm",
                           attributes={"pathology_group": "breast_ca", "unit": "mm"}),
                Extraction("margin_status", "Clear",
                           attributes={"pathology_group": "breast_ca",
                                       "margin_distance": "3mm"}),
                Extraction("lymph_node_status", "2/14 positive",
                           attributes={"pathology_group": "breast_ca",
                                       "positive_count": "2", "examined_count": "14"}),
                Extraction("staging", "pT2 N1 M0",
                           attributes={"pathology_group": "breast_ca",
                                       "T": "pT2", "N": "N1", "M": "M0"}),
                Extraction("immunohistochemistry", "ER positive",
                           attributes={"pathology_group": "breast_ca",
                                       "marker": "ER", "result": "positive",
                                       "percentage": "90%"}),
                Extraction("pathological_diagnosis",
                           "Invasive ductal carcinoma, right breast, grade 2, pT2N1M0",
                           attributes={"pathology_group": "breast_ca"}),
            ]
        )
    ],
    extraction_classes=[
        "specimen", "histological_finding", "staging", "margin_status",
        "lymph_node_status", "pathological_diagnosis", "immunohistochemistry", "tumour_size"
    ],
    report_sections=[
        "Specimen", "Microscopy Findings", "Staging", "Margins",
        "Lymph Nodes", "IHC Results", "Final Diagnosis"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# 7. OPERATIVE / SURGICAL REPORT
# ─────────────────────────────────────────────────────────────────────────────
OPERATIVE_REPORT_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract operative entities: procedure_name, indication, intraoperative_finding, "
        "implant, complication, blood_loss, operative_duration, surgeon, anaesthetist, "
        "anaesthesia_type, operative_date. "
        "Include approach and laterality on procedure_name. "
        "Link findings to procedure with operative_group attribute."
    ),
    examples=[
        ExampleData(
            text=(
                "Date: 12 Apr 2025. Surgeon: Mr. David Lee (Consultant Orthopaedic). "
                "Anaesthetist: Dr. Anna Brown. Anaesthesia: Spinal. "
                "Procedure: Right Total Knee Replacement — medial parapatellar approach. "
                "Indication: Severe osteoarthritis right knee. "
                "Implant: Stryker Triathlon CR — size 5 femur / size 4 tibia. "
                "Blood loss: 200mL. Duration: 95 min. Complications: None."
            ),
            extractions=[
                Extraction("operative_date", "12 Apr 2025", attributes={}),
                Extraction("surgeon", "Mr. David Lee",
                           attributes={"designation": "Consultant Orthopaedic"}),
                Extraction("anaesthesia_type", "Spinal", attributes={}),
                Extraction("procedure_name", "Right Total Knee Replacement",
                           attributes={"operative_group": "TKA",
                                       "approach": "medial parapatellar",
                                       "laterality": "right"}),
                Extraction("indication", "Severe osteoarthritis right knee",
                           attributes={"operative_group": "TKA"}),
                Extraction("implant", "Stryker Triathlon CR",
                           attributes={"operative_group": "TKA",
                                       "manufacturer": "Stryker"}),
                Extraction("blood_loss", "200mL",
                           attributes={"operative_group": "TKA"}),
                Extraction("operative_duration", "95 min",
                           attributes={"operative_group": "TKA"}),
            ]
        )
    ],
    extraction_classes=[
        "procedure_name", "indication", "intraoperative_finding", "implant",
        "complication", "blood_loss", "operative_duration", "surgeon",
        "anaesthetist", "anaesthesia_type", "operative_date"
    ],
    report_sections=[
        "Procedure Details", "Surgical Team", "Intraoperative Findings",
        "Implants Used", "Complications", "Outcome"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# 8. CONSULTATION NOTE
# ─────────────────────────────────────────────────────────────────────────────
CONSULTATION_NOTE_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract consultation entities: referral_reason, specialist_assessment, recommendation, "
        "medication_change, dosage, route, frequency, change_type (new/discontinued/dose-changed), "
        "investigation_ordered, follow_up_plan, referring_clinician, consulting_specialist. "
        "Link medication changes with medication_group = drug name."
    ),
    examples=[
        ExampleData(
            text=(
                "Referred by Dr. James Wong (GP). Specialist: Dr. Sarah Ali (Endocrinology). "
                "Reason: Poorly controlled T2DM, HbA1c 9.8%. "
                "Assessment: Suboptimal control on Metformin alone. "
                "Plan: Add Empagliflozin 10mg oral once daily (new). "
                "Increase Metformin to 1000mg BD (dose-changed). "
                "Order: Renal function, UACR. Follow-up: Endocrine in 3 months."
            ),
            extractions=[
                Extraction("referring_clinician", "Dr. James Wong",
                           attributes={"specialty": "GP"}),
                Extraction("consulting_specialist", "Dr. Sarah Ali",
                           attributes={"specialty": "Endocrinology"}),
                Extraction("referral_reason", "Poorly controlled T2DM",
                           attributes={"marker": "HbA1c 9.8%"}),
                Extraction("specialist_assessment",
                           "Suboptimal control on Metformin alone", attributes={}),
                Extraction("medication_change", "Empagliflozin",
                           attributes={"medication_group": "Empagliflozin",
                                       "change_type": "new"}),
                Extraction("dosage", "10mg",
                           attributes={"medication_group": "Empagliflozin"}),
                Extraction("frequency", "once daily",
                           attributes={"medication_group": "Empagliflozin"}),
                Extraction("medication_change", "Metformin",
                           attributes={"medication_group": "Metformin",
                                       "change_type": "dose-changed"}),
                Extraction("investigation_ordered", "Renal function", attributes={}),
                Extraction("follow_up_plan", "Endocrine in 3 months",
                           attributes={"specialty": "Endocrine", "timeframe": "3 months"}),
            ]
        )
    ],
    extraction_classes=[
        "referral_reason", "specialist_assessment", "recommendation",
        "medication_change", "dosage", "route", "frequency", "change_type",
        "investigation_ordered", "follow_up_plan",
        "referring_clinician", "consulting_specialist"
    ],
    report_sections=[
        "Referral Details", "Assessment", "Recommendations",
        "Medication Changes", "Investigations Ordered", "Follow-up Plan"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# 9. EMERGENCY DEPARTMENT (ED) NOTE
# ─────────────────────────────────────────────────────────────────────────────
ED_NOTE_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract ED entities: chief_complaint, triage_vital, mechanism_of_injury, "
        "treatment_given, dosage, route, investigation_result, ed_diagnosis, "
        "disposition, disposition_detail. "
        "Include vital_type/value/unit on vitals. "
        "Link ED drug treatments with medication_group = drug name."
    ),
    examples=[
        ExampleData(
            text=(
                "CC: Crushing chest pain, radiating left arm, 2hr onset. "
                "Vitals: BP 160/95 mmHg, HR 102 bpm, SpO2 94%. "
                "Tx: Aspirin 300mg oral, Morphine 5mg IV. "
                "ECG: ST elevation leads II/III/aVF — inferior STEMI. Troponin: 1.2 ng/mL (elevated). "
                "Dx: Inferior STEMI. Admitted to CCU for primary PCI."
            ),
            extractions=[
                Extraction("chief_complaint", "Crushing chest pain, radiating left arm",
                           attributes={"onset": "2hr"}),
                Extraction("triage_vital", "160/95 mmHg",
                           attributes={"vital_type": "blood_pressure",
                                       "value": "160/95", "unit": "mmHg"}),
                Extraction("triage_vital", "102 bpm",
                           attributes={"vital_type": "heart_rate",
                                       "value": "102", "unit": "bpm"}),
                Extraction("treatment_given", "Aspirin",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("dosage", "300mg",
                           attributes={"medication_group": "Aspirin"}),
                Extraction("treatment_given", "Morphine",
                           attributes={"medication_group": "Morphine"}),
                Extraction("dosage", "5mg",
                           attributes={"medication_group": "Morphine"}),
                Extraction("route", "IV",
                           attributes={"medication_group": "Morphine"}),
                Extraction("investigation_result", "ST elevation leads II/III/aVF",
                           attributes={"investigation": "ECG",
                                       "significance": "inferior STEMI"}),
                Extraction("ed_diagnosis", "Inferior STEMI", attributes={}),
                Extraction("disposition", "Admitted",
                           attributes={"destination": "CCU",
                                       "planned_procedure": "primary PCI"}),
            ]
        )
    ],
    extraction_classes=[
        "chief_complaint", "triage_vital", "mechanism_of_injury",
        "treatment_given", "dosage", "route", "investigation_result",
        "ed_diagnosis", "disposition", "disposition_detail"
    ],
    report_sections=[
        "Presentation", "Triage Vitals", "Treatments Given",
        "Investigation Results", "ED Diagnosis", "Disposition"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# 10. PROGRESS NOTE
# ─────────────────────────────────────────────────────────────────────────────
PROGRESS_NOTE_TEMPLATE = ExtractionTemplate(
    prompt_description=(
        "Extract progress note entities: interval_change, new_finding, medication_adjustment, "
        "dosage, route, frequency, change_type (dose-increased/dose-decreased/discontinued/new/"
        "route-changed), ongoing_problem, plan_update, vital_sign, response_to_treatment. "
        "Link medication adjustments with medication_group = drug name."
    ),
    examples=[
        ExampleData(
            text=(
                "Day 3 — Patient improving. Fever resolved, Temp 37.0°C, HR 85 bpm. "
                "CRP down 120→45 mg/L — good response to antibiotics. "
                "Ongoing: right lower lobe pneumonia, improving. "
                "Step down IV to oral Amoxicillin-Clavulanate 625mg BD (route-changed). "
                "Plan: Repeat CXR tomorrow. Discharge day 5 if improving."
            ),
            extractions=[
                Extraction("interval_change", "Patient improving",
                           attributes={"direction": "improvement"}),
                Extraction("vital_sign", "37.0°C",
                           attributes={"type": "temperature", "value": "37.0",
                                       "unit": "°C"}),
                Extraction("vital_sign", "85 bpm",
                           attributes={"type": "heart_rate", "value": "85",
                                       "unit": "bpm"}),
                Extraction("response_to_treatment", "CRP down 120→45 mg/L",
                           attributes={"treatment": "antibiotics", "marker": "CRP"}),
                Extraction("ongoing_problem", "right lower lobe pneumonia",
                           attributes={"status": "improving"}),
                Extraction("medication_adjustment", "Amoxicillin-Clavulanate",
                           attributes={"medication_group": "Amoxicillin-Clavulanate",
                                       "change_type": "route-changed",
                                       "from": "IV", "to": "oral"}),
                Extraction("dosage", "625mg",
                           attributes={"medication_group": "Amoxicillin-Clavulanate"}),
                Extraction("frequency", "BD",
                           attributes={"medication_group": "Amoxicillin-Clavulanate"}),
                Extraction("plan_update", "Repeat CXR tomorrow",
                           attributes={"timeframe": "tomorrow"}),
            ]
        )
    ],
    extraction_classes=[
        "interval_change", "new_finding", "medication_adjustment",
        "dosage", "route", "frequency", "change_type",
        "ongoing_problem", "plan_update", "vital_sign", "response_to_treatment"
    ],
    report_sections=[
        "Clinical Changes", "Vital Signs", "Medication Adjustments",
        "Ongoing Problems", "Treatment Response", "Updated Plan"
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# Template Registry
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES = {
    MedicalDocumentType.CLINICAL_NOTE:      CLINICAL_NOTE_TEMPLATE,
    MedicalDocumentType.RADIOLOGY_REPORT:   RADIOLOGY_REPORT_TEMPLATE,
    MedicalDocumentType.PRESCRIPTION:       PRESCRIPTION_TEMPLATE,
    MedicalDocumentType.LAB_REPORT:         LAB_REPORT_TEMPLATE,
    MedicalDocumentType.DISCHARGE_SUMMARY:  DISCHARGE_SUMMARY_TEMPLATE,
    MedicalDocumentType.PATHOLOGY_REPORT:   PATHOLOGY_REPORT_TEMPLATE,
    MedicalDocumentType.OPERATIVE_REPORT:   OPERATIVE_REPORT_TEMPLATE,
    MedicalDocumentType.CONSULTATION_NOTE:  CONSULTATION_NOTE_TEMPLATE,
    MedicalDocumentType.ED_NOTE:            ED_NOTE_TEMPLATE,
    MedicalDocumentType.PROGRESS_NOTE:      PROGRESS_NOTE_TEMPLATE,
    MedicalDocumentType.UNKNOWN:            CLINICAL_NOTE_TEMPLATE,
}


def get_template(doc_type: MedicalDocumentType) -> ExtractionTemplate:
    return TEMPLATES.get(doc_type, CLINICAL_NOTE_TEMPLATE)
