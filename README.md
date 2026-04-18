# MedExtract Clinical Assistant

A medical document intelligence application that extracts structured clinical data from healthcare documents using [LangExtract](https://github.com/google/langextract) and Google Gemini. Upload a clinical PDF, DOCX, or plain-text file and get back a structured PDF report, an interactive web dashboard, and a searchable SQLite database — all in seconds.

---

## What Problem Does It Solve?

Clinical documents (discharge summaries, lab reports, radiology reports, prescriptions, etc.) are rich in information but stored as unstructured text. Reading them manually is slow and error-prone. MedExtract automatically pulls out:

- Every **medication** with its dose, route, frequency, and duration
- All **diagnoses** (admission, discharge, working)
- **Lab results** with values, units, reference ranges, and abnormality flags
- **Radiology findings** with body part, size, impression, and recommendations
- **Vital signs**, symptoms, allergies, procedures, follow-up instructions
- The **exact character position** of every extracted fact in the original document so clinicians can verify the source

---

## Supported Document Types

| # | Type | Description |
|---|------|-------------|
| 1 | Clinical Note | General SOAP notes, GP, outpatient, inpatient |
| 2 | Radiology Report | CT, MRI, X-Ray, Ultrasound, PET scans |
| 3 | Prescription | Medication/drug order sheets |
| 4 | Lab Report | CBC, metabolic panel, urinalysis, cultures |
| 5 | Discharge Summary | Hospital discharge and transfer summaries |
| 6 | Pathology Report | Surgical pathology, biopsy, cytology, histology |
| 7 | Operative Report | Surgical notes and procedure notes |
| 8 | Consultation Note | Specialist consultation letters |
| 9 | ED Note | Emergency department triage and physician notes |
| 10 | Progress Note | Ward round notes, outpatient follow-ups |

The application automatically classifies the document type before extraction, so you do not need to specify it manually.

---

## Key Features

- **Multi-document upload** — analyse several documents in one request; session summary aggregates all results
- **Structured extraction** — medications, labs, findings grouped into typed records (not flat key-value pairs)
- **Source verification** — every extracted fact linked to its exact character offset in the original text
- **Professional PDF reports** — formatted tables with flag colouring (High = red, Low = blue, Normal = green)
- **Interactive dashboard** — 7 tabs per document: Report, Medications, Radiology, Labs, Diagnoses, All Extractions, Source Verify
- **SQLite persistence** — all sessions and extractions stored locally; no cloud database required
- **Token-efficient** — single extraction pass, large chunk buffers, concise prompts to minimise Gemini API costs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit Frontend  (frontend/app.py)                      │
│  Multi-file upload · 7-tab result view · Source verify      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (multipart/form-data)
┌───────────────────────────▼─────────────────────────────────┐
│  FastAPI Backend  (app/main.py)                             │
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │  Classifier │   │  Extractor   │   │  Med Grouper    │  │
│  │  (Gemini)   │──▶│  (LangExtract│──▶│  Medications    │  │
│  └─────────────┘   │   + Gemini)  │   │  Radiology      │  │
│                    └──────────────┘   │  Lab Results    │  │
│                                       └────────┬────────┘  │
│  ┌─────────────────────┐              ┌────────▼────────┐  │
│  │  Report Generator   │◀─────────────│  SQLite DB      │  │
│  │  (ReportLab PDF)    │              │  (6 tables)     │  │
│  └─────────────────────┘              └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Roles

| Component | File | Role |
|-----------|------|------|
| Classifier | `app/services/classifier.py` | Identifies document type via Gemini prompt |
| Extractor | `app/services/extractor.py` | Runs LangExtract with medical templates |
| Templates | `app/templates/extraction_templates.py` | 10 type-specific few-shot prompts |
| Med Grouper | `app/services/med_grouper.py` | Groups flat extractions into typed records |
| Report Generator | `app/services/report_generator.py` | Produces PDF with ReportLab |
| Database | `app/core/database.py` | Saves sessions and extractions to SQLite |

---

## How LangExtract Works Here

LangExtract is Google's open-source information extraction library. It splits the document into chunks, runs a Gemini few-shot prompt on each chunk, and returns `Extraction` objects with:

- `extraction_class` — the entity type (e.g. `medication`, `dosage`, `diagnosis`)
- `extraction_text` — the extracted value
- `attributes` — key-value metadata (e.g. `medication_group`, `route`, `frequency`)
- `char_interval` — start and end character offsets in the original document

MedExtract uses **grouping attributes** to link related entities. For example, every extraction belonging to the same medication (name, dosage, route, frequency, duration) shares the same `medication_group` value. The Med Grouper then assembles these into a single `MedicationRecord`.

---

## Prerequisites

- Python 3.10 or later
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))
- The LangExtract source repository (included as the `langextract/` folder in this project)

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd Medextract_Clinical_Assistant
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
HOST=0.0.0.0
PORT=8000
UPLOAD_DIR=outputs/uploads
REPORT_DIR=outputs/reports
DB_PATH=outputs/medextract.db
```

### 5. Set up SQLite

SQLite is built into Python — no installation required. The database file is created automatically at `outputs/medextract.db` when you first start the backend. The `outputs/` directory is also created automatically.

---

## Running the Application

### Start the Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### Start the Frontend

Open a second terminal (with the virtual environment activated):

```bash
streamlit run frontend/app.py
```

The dashboard will open at `http://localhost:8501`.

---

## Using the Application

### Via the Web Dashboard

1. Open `http://localhost:8501` in your browser
2. Enter the backend URL (default: `http://localhost:8000`)
3. Upload one or more documents (PDF, DOCX, or TXT)
4. Click **Analyze**
5. For each document, explore the 7 tabs:
   - **Report** — download the full PDF report
   - **Medications** — structured table of all medications
   - **Radiology** — imaging findings with impressions
   - **Labs** — lab results with reference ranges and flags
   - **Diagnoses** — all diagnoses extracted
   - **All Extractions** — complete flat list of every extracted entity
   - **Source Verify** — each fact with its exact character position in the original text
6. Use the **Session Summary** tab to see aggregates across all uploaded documents

### Via the REST API

**Analyse documents:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "files=@sample_docs/sample_clinical_note.txt"
```

**Download the PDF report:**
```bash
curl "http://localhost:8000/api/v1/report/{job_id}" --output report.pdf
```

**Download the JSONL data:**
```bash
curl "http://localhost:8000/api/v1/data/{job_id}" --output data.jsonl
```

**Health check:**
```bash
curl "http://localhost:8000/health"
```

---

## Sample Documents

Three sample files are included in `sample_docs/` to test the application immediately:

| File | Type | Content |
|------|------|---------|
| `sample_clinical_note.txt` | Clinical Note | SOAP note with multiple medications, diagnoses, vitals |
| `sample_radiology_report.txt` | Radiology Report | CT abdomen with multiple findings and impressions |
| `sample_lab_report.txt` | Lab Report | Full panel — CBC, iron studies, CMP, lipids, HbA1c, thyroid |

---

## Data Storage

All data is stored locally in a SQLite database (`outputs/medextract.db`). The schema has six tables:

| Table | Stores |
|-------|--------|
| `sessions` | One row per analysis job (job_id, timestamp, document count) |
| `documents` | One row per uploaded document (filename, type, confidence) |
| `extractions` | Every extracted entity with class, text, attributes, char offsets |
| `medications` | Grouped medication records (name, dose, route, frequency, etc.) |
| `radiology_findings` | Grouped radiology findings (finding, body part, impression, etc.) |
| `lab_results` | Grouped lab results (test, value, unit, reference range, flag) |

You can query the database directly with any SQLite client:

```bash
sqlite3 outputs/medextract.db "SELECT * FROM medications LIMIT 10;"
```

---

## Project Structure

```
POC-Google_Langextract/
├── app/
│   ├── main.py                        # FastAPI entry point
│   ├── api/routes/analyze.py          # Upload and analysis endpoint
│   ├── core/
│   │   ├── config.py                  # Settings from .env
│   │   ├── schemas.py                 # Pydantic models (all medical types)
│   │   └── database.py                # SQLite schema and helpers
│   ├── services/
│   │   ├── classifier.py              # Document type classification (Gemini)
│   │   ├── extractor.py               # LangExtract wrapper
│   │   ├── med_grouper.py             # Groups extractions into typed records
│   │   └── report_generator.py        # PDF generation (ReportLab)
│   ├── templates/
│   │   └── extraction_templates.py    # 10 medical few-shot prompt templates
│   └── utils/
│       └── file_handler.py            # PDF/DOCX/TXT parsing
├── frontend/
│   └── app.py                         # Streamlit dashboard
├── sample_docs/                       # Sample documents for testing
├── langextract/                       # LangExtract source (added to sys.path)
├── outputs/                           # Created at runtime (uploads, reports, DB)
├── requirements.txt
└── .env                               # Your API keys (not committed)
```

---

## Limitations

- **No OCR** — scanned PDFs (image-based) are not supported. Documents must contain selectable text.
- **English only** — extraction templates are written in English. Other languages may produce partial results.
- **POC scope** — this is a proof of concept. It is not validated for clinical use and should not be used to make medical decisions.
- **Token cost** — processing large documents (>10 pages) will consume more Gemini API tokens. The application is optimised to minimise token usage, but costs apply based on your Gemini API plan.
- **Gemini rate limits** — very large batches may hit API rate limits. Reduce `max_workers` in `extractor.py` if you see rate limit errors.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use for both classification and extraction |
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8000` | Backend port |
| `UPLOAD_DIR` | `outputs/uploads` | Where uploaded files are stored |
| `REPORT_DIR` | `outputs/reports` | Where generated PDF reports are saved |
| `DB_PATH` | `outputs/medextract.db` | SQLite database file path |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AI Extraction | [LangExtract](https://github.com/google/langextract) + Google Gemini |
| Classification | Google Gemini (`google-genai`) |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| PDF Generation | ReportLab |
| Database | SQLite (built-in Python) |
| Document Parsing | PyMuPDF (PDF), python-docx (DOCX) |
