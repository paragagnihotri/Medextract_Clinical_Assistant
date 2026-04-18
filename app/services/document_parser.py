"""Document Parsing Service"""
import pdfplumber
from docx import Document


def parse_document(file_path: str, file_ext: str) -> str:
    """
    Parse document and extract text
    
    Args:
        file_path: Path to document file
        file_ext: File extension (.pdf, .docx, .txt)
    
    Returns:
        Extracted text content
    """
    
    if file_ext == ".pdf":
        return _parse_pdf(file_path)
    elif file_ext == ".docx":
        return _parse_docx(file_path)
    elif file_ext == ".txt":
        return _parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_ext}")


def _parse_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    text_parts = []
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


def _parse_docx(file_path: str) -> str:
    """Extract text from DOCX"""
    doc = Document(file_path)
    text_parts = []
    
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)
    
    return "\n\n".join(text_parts)


def _parse_txt(file_path: str) -> str:
    """Extract text from TXT"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()
