import subprocess
import os
from pathlib import Path
import shutil

def convert_to_pdf(input_path: str, output_path: str) -> bool:
    """
    Convert PPTX file to PDF using LibreOffice
    
    Args:
        input_path: Path to input PPTX file
        output_path: Path where PDF should be saved
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert using LibreOffice with PDF export options to preserve hyperlinks
        process = subprocess.Popen([
            'soffice',
            '--headless',
            '--convert-to', 'pdf:writer_pdf_Export:EmbedCompleteFont:1,ExportBookmarks:1,ExportNotes:0,ExportNotesPages:0,UseTaggedPDF:1,ExportLinksRelativeFsys:0,ExportFormFields:1',
            '--outdir', os.path.dirname(output_path),
            input_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        process.wait()
        print(output_path)
        
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return False
