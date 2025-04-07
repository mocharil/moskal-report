from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import subprocess
import os
from pathlib import Path
import shutil

app = FastAPI()

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
        
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return False

@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    # Create temp directories
    temp_dir = Path("temp")
    output_dir = Path("output")
    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    temp_pptx = temp_dir / file.filename
    with open(temp_pptx, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Generate output PDF path
    pdf_name = os.path.splitext(file.filename)[0] + ".pdf"
    pdf_path = output_dir / pdf_name
    
    # Convert to PDF
    success = convert_to_pdf(str(temp_pptx), str(pdf_path))
    
    if success:
        # Clean up temp file
        os.remove(temp_pptx)
        
        # Return the PDF file
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=pdf_name
        )
    else:
        return {"error": "Conversion failed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
