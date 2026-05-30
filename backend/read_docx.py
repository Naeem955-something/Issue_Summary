import zipfile
import xml.etree.ElementTree as ET
import os

docx_path = r"c:\Users\fomal\OneDrive\Desktop\ai summarize\github_issue_summariser\DevCollab AI.docx"

if not os.path.exists(docx_path):
    print(f"Error: File not found at {docx_path}")
    exit(1)

try:
    # A .docx file is a ZIP archive. We can extract the text from 'word/document.xml'
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml')
        
    root = ET.fromstring(xml_content)
    
    # Define namespaces used in docx XML format
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }
    
    # Extract all text elements
    text_runs = []
    
    # Find all paragraph elements
    for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
        p_text = []
        # Find all text elements inside the paragraph
        for text in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if text.text:
                p_text.append(text.text)
        if p_text:
            text_runs.append("".join(p_text))
            
    print("--- DOCX Text Content ---")
    for para in text_runs:
        print(para)
    print("------------------------")
    
except Exception as e:
    print(f"Error reading docx: {e}")
