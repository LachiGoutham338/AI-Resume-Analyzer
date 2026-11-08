from pathlib import Path

def extract_text(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        import pdfplumber
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        text = "\n".join(parts)
    elif suffix == ".docx":
        from docx import Document
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + " ".join(cell.text for cell in row.cells)
    else:
        raise ValueError("Only PDF and DOCX files are supported.")
    if not text.strip():
        raise ValueError("No readable text found. Try a text-based PDF or DOCX file.")
    return text
