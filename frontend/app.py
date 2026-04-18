"""MedExtract Clinical Assistant — Streamlit Frontend"""
import streamlit as st
import requests
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv() 
API_BASE_URL = os.getenv("API_BASE_URL","http://localhost:8000")

st.set_page_config(
    page_title="MedExtract Clinical Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}

    .main-header {
        font-size: 2rem; font-weight: 700;
        color: #0d6e6e; text-align: center; margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem; color: #666;
        text-align: center; margin-bottom: 1.5rem;
    }
    .doc-type-badge {
        display: inline-block; padding: 2px 10px;
        border-radius: 12px; font-size: 0.75rem; font-weight: 600;
        background: #e6f4f4; color: #0d6e6e; border: 1px solid #0d6e6e;
    }
    .flag-high     { color: #c0392b; font-weight: 700; }
    .flag-low      { color: #1f77b4; font-weight: 700; }
    .flag-critical { color: #c0392b; font-weight: 700; }
    .flag-normal   { color: #1a7a4a; font-weight: 700; }
    .flag-abnormal { color: #d35400; font-weight: 700; }
    .source-box {
        background: #f8f9fa; border-left: 3px solid #0d6e6e;
        padding: 6px 10px; border-radius: 4px;
        font-size: 0.82rem; font-family: monospace; color: #333;
    }
    .confidence-exact  { color: #1a7a4a; font-size: 0.75rem; }
    .confidence-fuzzy  { color: #d35400; font-size: 0.75rem; }
    .confidence-none   { color: #999;    font-size: 0.75rem; }
    [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { font-size: 0.92rem; font-weight: 500; }
    .block-container  { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def check_health() -> bool:
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=3).status_code == 200
    except Exception:
        return False


def analyze_files(uploaded_files) -> tuple:
    file_tuples = [
        ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
        for f in uploaded_files
    ]
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/analyze",
            files=file_tuples,
            timeout=180,
        )
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"Error {resp.status_code}: {resp.json().get('detail', 'Unknown error')}"
    except requests.exceptions.Timeout:
        return None, "Request timed out (>3 min). Try with fewer or smaller files."
    except Exception as e:
        return None, str(e)


def get_pdf(session_id: str, doc_id: str) -> bytes | None:
    try:
        r = requests.get(f"{API_BASE_URL}/api/v1/report/{session_id}/{doc_id}", timeout=30)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


def display_pdf(pdf_bytes: bytes):
    b64 = base64.b64encode(pdf_bytes).decode()
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="750" type="application/pdf"></iframe>',
        unsafe_allow_html=True,
    )


def flag_html(flag: str) -> str:
    css = {
        "HIGH": "flag-high", "H": "flag-high",
        "LOW": "flag-low",   "L": "flag-low",
        "CRITICAL": "flag-critical",
        "ABNORMAL": "flag-abnormal",
        "NORMAL": "flag-normal", "N": "flag-normal",
    }.get((flag or "").upper(), "")
    if css:
        return f'<span class="{css}">{flag}</span>'
    return flag or "—"


def source_snippet(extraction_text: str, span: dict | None, raw_text: str) -> str:
    if not span or span.get("char_start") is None:
        return ""
    s, e = span["char_start"], span["char_end"]
    ctx_s = max(0, s - 50)
    ctx_e = min(len(raw_text), e + 50)
    prefix = "…" if ctx_s > 0 else ""
    suffix = "…" if ctx_e < len(raw_text) else ""
    snippet = raw_text[ctx_s:ctx_e]
    # Highlight extracted portion
    rel_s = s - ctx_s
    rel_e = e - ctx_s
    highlighted = (
        snippet[:rel_s]
        + f"**{snippet[rel_s:rel_e]}**"
        + snippet[rel_e:]
    )
    return f"{prefix}{highlighted}{suffix}"


def confidence_badge(status: str | None) -> str:
    mapping = {
        "match_exact":   ("Exact",    "confidence-exact"),
        "match_fuzzy":   ("Fuzzy",    "confidence-fuzzy"),
        "match_greater": ("Wider",    "confidence-fuzzy"),
        "match_lesser":  ("Narrower", "confidence-fuzzy"),
    }
    label, css = mapping.get(status or "", ("Unverified", "confidence-none"))
    return f'<span class="{css}">◉ {label}</span>'


def doc_type_label(doc_type: str) -> str:
    return doc_type.replace("_", " ").title()


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

def render_sidebar(result: dict | None):
    with st.sidebar:
        st.markdown("### 🏥 MedExtract")
        st.markdown("*Clinical Data Extraction*")
        st.divider()

        st.markdown("**Supported Documents**")
        doc_types = [
            "Clinical / SOAP Note", "Radiology Report", "Prescription",
            "Lab / Blood Report", "Discharge Summary", "Pathology Report",
            "Operative Report", "Consultation Note", "ED Note", "Progress Note",
        ]
        for dt in doc_types:
            st.markdown(f"• {dt}")

        st.divider()
        st.markdown("**Powered by**")
        st.markdown("🔬 LangExtract · Google Gemini")
        st.markdown("📊 SQLite · ReportLab")

        if result:
            st.divider()
            st.markdown("**Session Stats**")
            all_meds  = result.get("all_medications", [])
            all_finds = result.get("all_findings", [])
            all_labs  = result.get("all_lab_results", [])
            all_diags = result.get("all_diagnoses", [])
            st.metric("Documents",   result.get("document_count", 0))
            st.metric("Medications", len(all_meds))
            st.metric("Diagnoses",   len(all_diags))
            st.metric("Findings",    len(all_finds))
            st.metric("Lab Tests",   len(all_labs))


# ──────────────────────────────────────────────────────────────────────────────
# Per-document tabs
# ──────────────────────────────────────────────────────────────────────────────

def render_document_tab(doc: dict):
    raw_text = doc.get("raw_text", "")

    tab_report, tab_meds, tab_findings, tab_labs, tab_diag, tab_all, tab_verify = st.tabs([
        "📄 Report", "💊 Medications", "🔬 Radiology",
        "🧪 Lab Results", "📋 Diagnoses", "🗂 All Extractions", "🔍 Source Verify"
    ])

    # ── PDF Report ────────────────────────────────────────────────────────────
    with tab_report:
        sid  = doc.get("_session_id", "")
        did  = doc.get("document_id", "")
        pdf  = get_pdf(sid, did) if sid and did else None
        if pdf:
            display_pdf(pdf)
            st.download_button(
                "⬇ Download PDF Report", data=pdf,
                file_name=f"medextract_{did[:8]}.pdf",
                mime="application/pdf", use_container_width=True,
            )
        else:
            st.info("PDF report not available.")

    # ── Medications ───────────────────────────────────────────────────────────
    with tab_meds:
        meds = doc.get("medication_records", [])
        if not meds:
            st.info("No medications extracted from this document.")
        else:
            st.markdown(f"**{len(meds)} medication(s) identified**")
            for m in meds:
                with st.expander(f"💊 {m.get('medication_name', 'Unknown')}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Dose",      m.get("dosage")    or "—")
                    col2.metric("Route",     m.get("route")     or "—")
                    col3.metric("Frequency", m.get("frequency") or "—")
                    if m.get("duration"):
                        st.markdown(f"**Duration:** {m['duration']}")
                    if m.get("indication"):
                        st.markdown(f"**Indication:** {m['indication']}")
                    if m.get("special_instruction"):
                        st.info(f"ℹ️ {m['special_instruction']}")

                    # Source spans for each component
                    spans = m.get("source_spans", {})
                    if spans and raw_text:
                        st.markdown("---")
                        st.markdown("**Source Verification**")
                        for field, span in spans.items():
                            if span and span.get("char_start") is not None:
                                snip = source_snippet("", span, raw_text)
                                st.markdown(
                                    f'`{field}` {confidence_badge(span.get("alignment_status"))}',
                                    unsafe_allow_html=True,
                                )
                                st.markdown(
                                    f'<div class="source-box">{snip}</div>',
                                    unsafe_allow_html=True,
                                )

    # ── Radiology ─────────────────────────────────────────────────────────────
    with tab_findings:
        findings = doc.get("radiology_findings", [])
        if not findings:
            st.info("No radiology findings extracted from this document.")
        else:
            st.markdown(f"**{len(findings)} finding(s) identified**")
            for f in findings:
                with st.expander(f"🔬 {f.get('finding', 'Unknown finding')}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Body Part",  f.get("body_part")  or "—")
                    col2.metric("Laterality", f.get("laterality") or "—")
                    col3.metric("Size",       f.get("measurement") or "—")
                    if f.get("character"):
                        st.markdown(f"**Character:** {f['character']}")
                    if f.get("impression"):
                        st.success(f"**Impression:** {f['impression']}")
                    if f.get("severity"):
                        st.markdown(f"**Severity:** {f['severity']}")
                    if f.get("recommendation"):
                        st.warning(f"**Recommendation:** {f['recommendation']}")

                    spans = f.get("source_spans", {})
                    if spans and raw_text:
                        st.markdown("---")
                        st.markdown("**Source Verification**")
                        for field, span in spans.items():
                            if span and span.get("char_start") is not None:
                                snip = source_snippet("", span, raw_text)
                                st.markdown(
                                    f'`{field}` {confidence_badge(span.get("alignment_status"))}',
                                    unsafe_allow_html=True,
                                )
                                st.markdown(
                                    f'<div class="source-box">{snip}</div>',
                                    unsafe_allow_html=True,
                                )

    # ── Lab Results ───────────────────────────────────────────────────────────
    with tab_labs:
        labs = doc.get("lab_results", [])
        if not labs:
            st.info("No lab results extracted from this document.")
        else:
            st.markdown(f"**{len(labs)} test(s) extracted**")
            # Separate abnormals
            abnormals = [r for r in labs if (r.get("flag") or "").upper()
                         in ("HIGH", "H", "LOW", "L", "CRITICAL", "ABNORMAL")]
            if abnormals:
                st.error(f"⚠️ {len(abnormals)} abnormal result(s)")

            for r in labs:
                flag     = (r.get("flag") or "").upper()
                icon     = "🔴" if flag in ("HIGH", "H", "CRITICAL") else \
                           "🔵" if flag in ("LOW", "L") else \
                           "🟡" if flag == "ABNORMAL" else "🟢"
                with st.expander(f"{icon} {r.get('test_name', 'Test')}  —  "
                                 f"{r.get('result_value', '?')} {r.get('unit', '')}"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Result",    r.get("result_value") or "—")
                    col2.metric("Unit",      r.get("unit")         or "—")
                    col3.metric("Ref Range", r.get("reference_range") or "—")
                    col4.markdown(
                        f"**Flag**<br>{flag_html(r.get('flag', ''))}", unsafe_allow_html=True
                    )
                    if r.get("panel_name"):
                        st.caption(f"Panel: {r['panel_name']}")

                    spans = r.get("source_spans", {})
                    if spans and raw_text:
                        st.markdown("---")
                        st.markdown("**Source Verification**")
                        for field, span in spans.items():
                            if span and span.get("char_start") is not None:
                                snip = source_snippet("", span, raw_text)
                                st.markdown(
                                    f'`{field}` {confidence_badge(span.get("alignment_status"))}',
                                    unsafe_allow_html=True,
                                )
                                st.markdown(
                                    f'<div class="source-box">{snip}</div>',
                                    unsafe_allow_html=True,
                                )

    # ── Diagnoses ─────────────────────────────────────────────────────────────
    with tab_diag:
        diags = doc.get("diagnoses", [])
        if not diags:
            st.info("No diagnoses extracted from this document.")
        else:
            st.markdown(f"**{len(diags)} diagnosis/diagnoses identified**")
            for i, d in enumerate(diags, 1):
                st.markdown(f"{i}. {d}")

    # ── All Extractions ────────────────────────────────────────────────────────
    with tab_all:
        extractions = doc.get("extractions", [])
        if not extractions:
            st.info("No extractions.")
        else:
            grouped: dict = {}
            for e in extractions:
                cls = e.get("extraction_class", "other")
                grouped.setdefault(cls, []).append(e)

            for cls, items in sorted(grouped.items()):
                with st.expander(f"{cls.replace('_', ' ').title()}  ({len(items)})", expanded=False):
                    for e in items:
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            st.markdown(f"**{e.get('extraction_text', '')}**")
                        with col2:
                            attrs = {k: v for k, v in (e.get("attributes") or {}).items()
                                     if k not in ("medication_group", "finding_group",
                                                  "test_group", "pathology_group",
                                                  "operative_group") and v}
                            if attrs:
                                st.caption(" · ".join(
                                    f"{k.replace('_', ' ')}: {v}"
                                    for k, v in list(attrs.items())[:4]
                                ))
                        sp = e.get("source_span")
                        if sp and sp.get("char_start") is not None and raw_text:
                            snip = raw_text[sp["char_start"]:sp["char_end"]]
                            st.markdown(
                                f'<div class="source-box">{snip[:120]}</div>',
                                unsafe_allow_html=True,
                            )
                        st.markdown("---")

    # ── Source Verification ───────────────────────────────────────────────────
    with tab_verify:
        st.markdown(
            "Every extracted fact below is linked to its exact position in the source document. "
            "Char positions are character-level byte offsets."
        )
        extractions = doc.get("extractions", [])
        verifiable  = [e for e in extractions
                       if e.get("source_span") and
                       e["source_span"].get("char_start") is not None]

        if not verifiable:
            st.info("No character offsets available — the document may be too short for LangExtract to align spans.")
            return

        st.markdown(f"**{len(verifiable)} verifiable extraction(s)**")

        search = st.text_input("Filter by class or text", key=f"sv_search_{doc.get('document_id', '')}")

        for e in verifiable:
            if search and search.lower() not in (e.get("extraction_class", "") + e.get("extraction_text", "")).lower():
                continue

            sp     = e["source_span"]
            status = sp.get("alignment_status", "")
            snip   = source_snippet(e.get("extraction_text", ""), sp, raw_text)

            with st.expander(
                f"`{e.get('extraction_class', '')}` — **{e.get('extraction_text', '')}**",
                expanded=False,
            ):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"**Chars:** {sp.get('char_start')}–{sp.get('char_end')}")
                    st.markdown(
                        f"**Confidence:** {confidence_badge(status)}",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown("**Source context:**")
                    st.markdown(
                        f'<div class="source-box">{snip}</div>',
                        unsafe_allow_html=True,
                    )


# ──────────────────────────────────────────────────────────────────────────────
# Unified Session Summary (multi-document)
# ──────────────────────────────────────────────────────────────────────────────

def render_session_summary(result: dict):
    st.markdown("## Session Summary — All Documents")

    all_meds  = result.get("all_medications", [])
    all_finds = result.get("all_findings", [])
    all_labs  = result.get("all_lab_results", [])
    all_diags = result.get("all_diagnoses", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Medications",  len(all_meds))
    c2.metric("Total Findings",     len(all_finds))
    c3.metric("Total Lab Tests",    len(all_labs))
    c4.metric("Total Diagnoses",    len(all_diags))

    st.divider()

    if all_diags:
        st.markdown("### 📋 All Diagnoses (across documents)")
        for i, d in enumerate(all_diags, 1):
            st.markdown(f"{i}. {d}")
        st.divider()

    if all_meds:
        st.markdown("### 💊 Medication Reconciliation (all documents)")
        st.caption("Review for duplicates or conflicts across uploaded documents.")
        rows = []
        for m in all_meds:
            rows.append({
                "Medication":   m.get("medication_name", ""),
                "Dose":         m.get("dosage", "—"),
                "Route":        m.get("route", "—"),
                "Frequency":    m.get("frequency", "—"),
                "Duration":     m.get("duration", "—"),
                "Indication":   m.get("indication", "—"),
            })
        st.dataframe(rows, use_container_width=True)
        st.divider()

    if all_labs:
        abnormals = [r for r in all_labs
                     if (r.get("flag") or "").upper()
                     in ("HIGH", "H", "LOW", "L", "CRITICAL", "ABNORMAL")]
        if abnormals:
            st.error(f"⚠️ {len(abnormals)} abnormal lab result(s) across all documents")

        st.markdown("### 🧪 All Lab Results")
        rows = []
        for r in all_labs:
            rows.append({
                "Test":      r.get("test_name", ""),
                "Result":    r.get("result_value", "—"),
                "Unit":      r.get("unit", "—"),
                "Ref Range": r.get("reference_range", "—"),
                "Flag":      r.get("flag", "—"),
                "Panel":     r.get("panel_name", "—"),
            })
        st.dataframe(rows, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    result = st.session_state.get("result")
    render_sidebar(result)

    st.markdown("""
    <div class="header-banner">
        <h1 style="margin:0;">🏥 MedExtract Clinical Assistant</h1>
        <p style="opacity:0.9;">AI-powered structured clinical data extraction</p>
    </div>
    """, unsafe_allow_html=True)

    if not check_health():
        st.error("⚠️ Backend not running. Start with: `python run.py`")
        st.stop()

    # ── Upload screen ─────────────────────────────────────────────────────────
    if not st.session_state.get("show_results"):
        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 3, 1])
        with col_c:
            st.markdown("### Upload medical document(s) to begin")
            st.caption("Supports PDF · DOCX · TXT · Up to 10 files · Max 10 MB each")

            uploaded = st.file_uploader(
                "Drag and drop or browse",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )

            if uploaded:
                for f in uploaded:
                    st.success(f"✓ {f.name}  ({f.size / 1024:.1f} KB)")

                if st.button("🔍 Analyse Documents", type="primary", use_container_width=True):
                    with st.spinner(f"Analysing {len(uploaded)} document(s) — this may take 20–60 seconds..."):
                        res, err = analyze_files(uploaded)
                    if err:
                        st.error(err)
                    else:
                        # Attach session_id to each document for PDF retrieval
                        for doc in res.get("documents", []):
                            doc["_session_id"] = res["session_id"]
                        st.session_state.result       = res
                        st.session_state.show_results = True
                        st.rerun()

    # ── Results screen ────────────────────────────────────────────────────────
    else:
        result = st.session_state.result
        docs   = result.get("documents", [])

        top_l, top_r = st.columns([5, 1])
        with top_l:
            doc_count = result.get("document_count", 0)
            st.markdown(f"**Session:** `{result.get('session_id', '')[:16]}…` · "
                        f"**{doc_count} document(s) analysed**")
        with top_r:
            if st.button("↩ New Analysis"):
                st.session_state.show_results = False
                st.session_state.result       = None
                st.rerun()

        st.divider()

        # Multi-document: tabs across top
        if doc_count > 1:
            tab_labels = ["📊 Session Summary"] + [f"📄 {d.get('filename', f'Doc {i+1}')}"
                          for i, d in enumerate(docs)]
            tabs = st.tabs(tab_labels)

            with tabs[0]:
                render_session_summary(result)

            for i, doc in enumerate(docs):
                with tabs[i + 1]:
                    dt = doc_type_label(doc.get("document_type", ""))
                    conf = doc.get("classification_confidence", 0)
                    extcount = len(doc.get("extractions", []))
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Document Type", dt)
                    c2.metric("Confidence",    f"{conf:.0%}")
                    c3.metric("Extractions",   extcount)
                    if doc.get("classification_reasoning"):
                        st.caption(doc["classification_reasoning"])
                    st.divider()
                    render_document_tab(doc)

        # Single document: render directly
        else:
            doc  = docs[0] if docs else {}
            dt   = doc_type_label(doc.get("document_type", ""))
            conf = doc.get("classification_confidence", 0)
            extcount = len(doc.get("extractions", []))

            c1, c2, c3 = st.columns(3)
            c1.metric("Document Type", dt)
            c2.metric("Confidence",    f"{conf:.0%}")
            c3.metric("Extractions",   extcount)
            if doc.get("classification_reasoning"):
                st.caption(doc["classification_reasoning"])
            st.divider()
            render_document_tab(doc)

        # JSONL download in sidebar
        with st.sidebar:
            st.divider()
            st.markdown("**Downloads**")
            for doc in docs:
                sid = doc.get("_session_id", "")
                did = doc.get("document_id", "")
                if sid and did:
                    try:
                        jresp = requests.get(
                            f"{API_BASE_URL}/api/v1/data/{sid}/{did}", timeout=10
                        )
                        if jresp.status_code == 200:
                            st.download_button(
                                f"⬇ JSONL — {doc.get('filename', did)[:20]}",
                                data=jresp.content,
                                file_name=f"data_{did[:8]}.jsonl",
                                mime="application/jsonl",
                                use_container_width=True,
                            )
                    except Exception:
                        pass


if __name__ == "__main__":
    main()
