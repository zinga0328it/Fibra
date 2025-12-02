import re
from typing import List, Dict, Any

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


def parse_pdf_work_order(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a PDF work order file and extract job information.
    
    This parser attempts to extract:
    - Work order number
    - Customer name
    - Customer address
    - Customer phone
    - Description
    - Extra fields
    """
    
    if PdfReader is None:
        raise ImportError("PyPDF2 is required to parse PDF files")
    
    jobs = []
    
    try:
        reader = PdfReader(file_path)
        full_text = ""
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        # Parse the extracted text
        jobs = extract_jobs_from_text(full_text)
        
    except Exception as e:
        # If PDF parsing fails, return empty list
        print(f"Error parsing PDF: {e}")
        return []
    
    return jobs


def extract_jobs_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract job information from text content."""
    
    jobs = []
    
    # Common patterns for work order fields (Italian and English)
    patterns = {
        "work_order_number": [
            r"(?:ordine|order|wo|wr|pratica|codice)[:\s#]*([A-Z0-9\-/]+)",
            r"(?:numero|number)[:\s#]*([A-Z0-9\-/]+)",
        ],
        "customer_name": [
            r"(?:cliente|customer|nome|name)[:\s]+([^\n\r]+)",
            r"(?:intestatario|subscriber)[:\s]+([^\n\r]+)",
        ],
        "customer_address": [
            r"(?:indirizzo|address|via|località|location)[:\s]+([^\n\r]+)",
            r"(?:comune|città|city)[:\s]+([^\n\r]+)",
        ],
        "customer_phone": [
            r"(?:telefono|phone|tel|cellulare|mobile)[:\s]+([0-9\s\+\-\.]+)",
            r"(?:contatto|contact)[:\s]+([0-9\s\+\-\.]+)",
        ],
        "description": [
            r"(?:descrizione|description|lavoro|work|tipo|type)[:\s]+([^\n\r]+)",
            r"(?:intervento|operation|attività|activity)[:\s]+([^\n\r]+)",
        ]
    }
    
    # Try to detect multiple work orders by looking for separators or repeated patterns
    sections = re.split(r"(?:={3,}|-{3,}|\n{3,}|pagina\s*\d+|page\s*\d+)", text, flags=re.IGNORECASE)
    
    if len(sections) <= 1:
        # If no clear separators, treat as single work order
        sections = [text]
    
    for section in sections:
        if not section.strip():
            continue
        
        job_data = {
            "work_order_number": None,
            "customer_name": None,
            "customer_address": None,
            "customer_phone": None,
            "description": None,
            "extra_fields": {}
        }
        
        # Extract each field using patterns
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, section, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) > 1:
                        job_data[field] = value
                        break
        
        # Only add job if we found some meaningful data
        if any(v for k, v in job_data.items() if k != "extra_fields" and v):
            jobs.append(job_data)
    
    # If no structured data found, create a single job with the description
    if not jobs and text.strip():
        jobs.append({
            "work_order_number": None,
            "customer_name": None,
            "customer_address": None,
            "customer_phone": None,
            "description": text.strip()[:500],
            "extra_fields": {}
        })
    
    return jobs
