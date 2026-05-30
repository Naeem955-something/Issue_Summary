import zipfile
import xml.etree.ElementTree as ET
import os

docx_path = r"c:\Users\fomal\OneDrive\Desktop\ai summarize\github_issue_summariser\DevCollab AI.docx"
output_path = r"c:\Users\fomal\OneDrive\Desktop\ai summarize\github_issue_summariser\DevCollab_AI_Content.txt"

try:
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml')
        
    root = ET.fromstring(xml_content)
    
    text_runs = []
    for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
        p_text = []
        for text in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if text.text:
                p_text.append(text.text)
        if p_text:
            text_runs.append("".join(p_text))
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("--- DOCX Text Content ---\n")
        for para in text_runs:
            f.write(para + "\n")
        f.write("------------------------\n")
    print(f"Success! Written to {output_path}")
    
except Exception as e:
    print(f"Error reading docx: {e}")
