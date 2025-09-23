#!/usr/bin/env python3
"""
PDF to ASCII Manual Converter

Converts any PDF manual to 100% ASCII format compatible with the Universal RAG system.
Extracts text, images, and structures content using the manual template format.

Usage:
    python pdf_to_ascii_converter.py "path/to/manual.pdf" "Output Manual Title"

Example:
    python pdf_to_ascii_converter.py "Orbi Whole Home Tri-Band.pdf" "Orbi Whole Home Tri-Band Mesh WiFi 6 System"
"""

import sys
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_to_ascii(text: str) -> str:
    """Convert any text to 100% ASCII, handling Unicode characters gracefully."""
    # First normalize Unicode to decomposed form
    normalized = unicodedata.normalize('NFD', text)

    # Remove non-ASCII characters, keeping only basic ASCII (0-127)
    ascii_text = ''.join(c for c in normalized if ord(c) < 128)

    # Replace common Unicode punctuation with ASCII equivalents
    replacements = {
        '"': '"',  # Smart quotes
        '"': '"',
        ''': "'",  # Smart apostrophes
        ''': "'",
        '—': '--',  # Em dash
        '–': '-',   # En dash
        '…': '...',  # Ellipsis
        '•': '- ',   # Bullet points
        '©': '(c)',  # Copyright
        '®': '(R)',  # Registered
        '™': '(TM)', # Trademark
        '°': ' degrees',  # Degree symbol
        '×': 'x',    # Multiplication
        '÷': '/',    # Division
        '±': '+/-',  # Plus/minus
        '≤': '<=',   # Less than or equal
        '≥': '>=',   # Greater than or equal
        '≠': '!=',   # Not equal
        '→': '->',   # Right arrow
        '←': '<-',   # Left arrow
        '↑': '^',    # Up arrow
        '↓': 'v',    # Down arrow
    }

    for unicode_char, ascii_replacement in replacements.items():
        ascii_text = ascii_text.replace(unicode_char, ascii_replacement)

    # Clean up multiple spaces and ensure proper line breaks
    ascii_text = re.sub(r'\s+', ' ', ascii_text)
    ascii_text = re.sub(r'\n\s*\n', '\n\n', ascii_text)

    return ascii_text.strip()

def extract_pdf_text_simple(pdf_path: str) -> str:
    """Extract text from PDF using basic approach (fallback method)."""
    try:
        # Try PyPDF2 first (most common)
        import PyPDF2

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n\n=== PAGE {page_num + 1} ===\n"
                        text += page_text
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                    continue

            return normalize_to_ascii(text)

    except ImportError:
        logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
        return ""
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

def extract_pdf_text_advanced(pdf_path: str) -> str:
    """Extract text from PDF using advanced methods."""
    methods_to_try = [
        ("pdfplumber", extract_with_pdfplumber),
        ("pymupdf", extract_with_pymupdf),
        ("pdfminer", extract_with_pdfminer),
        ("pypdf2", extract_pdf_text_simple)
    ]

    for method_name, extract_func in methods_to_try:
        try:
            logger.info(f"Trying {method_name}...")
            text = extract_func(pdf_path)
            if text and len(text.strip()) > 100:  # Reasonable amount of text
                logger.info(f"Successfully extracted text using {method_name}")
                return normalize_to_ascii(text)
        except ImportError:
            logger.warning(f"{method_name} not available")
            continue
        except Exception as e:
            logger.warning(f"{method_name} failed: {e}")
            continue

    logger.error("All PDF extraction methods failed")
    return ""

def extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract using pdfplumber (best for tables/layout)."""
    import pdfplumber

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n\n=== PAGE {page_num + 1} ===\n"
                text += page_text
    return text

def extract_with_pymupdf(pdf_path: str) -> str:
    """Extract using PyMuPDF/fitz (good OCR capabilities)."""
    import fitz  # PyMuPDF

    text = ""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        if page_text.strip():
            text += f"\n\n=== PAGE {page_num + 1} ===\n"
            text += page_text
    doc.close()
    return text

def extract_with_pdfminer(pdf_path: str) -> str:
    """Extract using pdfminer.six (good for complex layouts)."""
    from pdfminer.high_level import extract_text
    return extract_text(pdf_path)

def structure_content_sections(raw_text: str, manual_title: str) -> List[Dict[str, Any]]:
    """Structure raw PDF text into organized sections for the template."""

    # Split text by pages for easier processing
    pages = re.split(r'=== PAGE \d+ ===', raw_text)

    sections = []
    section_counter = 1

    # Look for common section patterns
    section_patterns = [
        r'(?i)(introduction|overview|getting started)',
        r'(?i)(safety|warning|precaution)',
        r'(?i)(installation|setup|connect)',
        r'(?i)(configuration|settings)',
        r'(?i)(troubleshooting|problem|issue)',
        r'(?i)(specifications|spec|technical)',
        r'(?i)(appendix|reference|index)'
    ]

    current_section = {
        'title': 'Introduction & Overview',
        'subtitle': 'General information and getting started',
        'page': '1-5',
        'section_id': f'introduction_overview_{section_counter:03d}',
        'content': '',
        'keywords': ['introduction', 'overview', 'getting started'],
        'is_complete': True
    }

    # Process each page
    for i, page_content in enumerate(pages[1:], 1):  # Skip first empty split
        if not page_content.strip():
            continue

        # Clean up the page content
        clean_content = normalize_to_ascii(page_content)

        # Check if this page starts a new major section
        found_new_section = False
        for pattern in section_patterns:
            if re.search(pattern, clean_content[:500]):  # Check first 500 chars
                if current_section['content'].strip():  # Save previous section
                    sections.append(current_section.copy())
                    section_counter += 1

                # Start new section
                match = re.search(pattern, clean_content, re.IGNORECASE)
                section_title = match.group(1).title() if match else f"Section {section_counter}"

                current_section = {
                    'title': section_title,
                    'subtitle': f'Information from page {i}',
                    'page': str(i),
                    'section_id': f'{section_title.lower().replace(" ", "_")}_{section_counter:03d}',
                    'content': clean_content,
                    'keywords': [section_title.lower()],
                    'is_complete': True
                }
                found_new_section = True
                break

        if not found_new_section:
            # Add to current section
            current_section['content'] += f"\n\n{clean_content}"
            current_section['page'] = f"{current_section['page'].split('-')[0]}-{i}"

    # Add the last section
    if current_section['content'].strip():
        sections.append(current_section)

    # If no structured sections found, create one large section
    if not sections:
        sections.append({
            'title': 'Manual Content',
            'subtitle': 'Complete manual content',
            'page': '1-end',
            'section_id': 'manual_content_001',
            'content': normalize_to_ascii(raw_text),
            'keywords': ['manual', 'content', 'complete'],
            'is_complete': True
        })

    return sections

def generate_ascii_manual(pdf_path: str, manual_title: str, author: str = "Unknown") -> str:
    """Generate complete ASCII manual from PDF."""

    logger.info(f"Starting conversion of {pdf_path}")

    # Extract text from PDF
    raw_text = extract_pdf_text_advanced(pdf_path)
    if not raw_text:
        logger.error("Could not extract any text from PDF")
        return ""

    logger.info(f"Extracted {len(raw_text)} characters from PDF")

    # Structure content into sections
    sections = structure_content_sections(raw_text, manual_title)
    logger.info(f"Created {len(sections)} sections")

    # Generate the ASCII manual using template format
    manual_content = f"""# Manual Input Template
**Instructions**: Fill out each section completely. Text will be automatically chunked semantically. Do not trim content - the system will preserve everything. Include all sections.

## Document Metadata
- **Title**: {normalize_to_ascii(manual_title)}
- **Version**: v1.0
- **Source Type**: manual (options: manual, maintenance_guide, faq, troubleshooting, best_practices)
- **Language**: en-US
- **Author/Publisher**: {normalize_to_ascii(author)}

---

"""

    # Add each section
    for i, section in enumerate(sections, 1):
        section_content = f"""## Section {i}: {section['title']}
- **Subtitle**: {section['subtitle']}
- **Page Number**: {section['page']}
- **Section ID**: {section['section_id']}

### Content
{section['content']}

### Images
- **Image Filename**: section_{i}_diagram.png
- **Firebase Path**: manual001/section_{i}_diagram.png
- **Image Description**: [Image extracted from PDF page {section['page']} - manual review needed for accurate description]

### Metadata
- **Keywords**: {', '.join(section['keywords'])}
- **Related Sections**: [To be determined based on content analysis]
- **Is Complete Section**: {str(section['is_complete']).lower()}

"""
        manual_content += section_content

    # Add processing instructions
    manual_content += """## Processing Instructions
- **Auto-chunking**: Enable semantic chunking with 30% overlap
- **Summary Generation**: Generate summaries for each chunk
- **Embedding**: Use text-embedding-004
- **Validation**: Check for unique IDs and sequential chunk ordering
- **Language Detection**: Verify language matches specified language code
"""

    return manual_content

def main():
    """Main conversion function."""
    if len(sys.argv) < 3:
        print("Usage: python pdf_to_ascii_converter.py <pdf_path> <manual_title> [author]")
        print("Example: python pdf_to_ascii_converter.py 'manual.pdf' 'My Device Manual' 'Company Name'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    manual_title = sys.argv[2]
    author = sys.argv[3] if len(sys.argv) > 3 else "Unknown Publisher"

    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)

    # Generate output filename
    safe_title = re.sub(r'[^\w\s-]', '', manual_title).strip()
    safe_title = re.sub(r'[-\s]+', '_', safe_title).lower()
    output_file = f"{safe_title}_manual_content.md"

    # Convert PDF to ASCII manual
    ascii_manual = generate_ascii_manual(pdf_path, manual_title, author)

    if not ascii_manual:
        logger.error("Failed to generate ASCII manual")
        sys.exit(1)

    # Write to file
    with open(output_file, 'w', encoding='ascii', errors='replace') as f:
        f.write(ascii_manual)

    logger.info(f"ASCII manual written to: {output_file}")
    logger.info(f"File size: {len(ascii_manual)} characters")

    # Also create a copy with standard naming for the RAG system
    template_file = "chatbot_backend/templates/my_manual_content.md"
    if os.path.exists("chatbot_backend/templates/"):
        with open(template_file, 'w', encoding='ascii', errors='replace') as f:
            f.write(ascii_manual)
        logger.info(f"Template copy written to: {template_file}")

    print(f"\nSUCCESS: Converted '{pdf_path}' to 100% ASCII format")
    print(f"Output file: {output_file}")
    print(f"Content: {len(ascii_manual)} ASCII characters")
    print(f"\nNext steps:")
    print(f"1. Review and edit the generated content in {output_file}")
    print(f"2. Add proper image descriptions and keywords")
    print(f"3. Run: python training/scripts/generate_jsonl_enhanced.py {output_file}")
    print(f"4. Run: python training/scripts/prepare_vectors_enhanced.py training/output/chunks/{safe_title}_manual_content_enhanced_chunks.jsonl")

if __name__ == "__main__":
    main()