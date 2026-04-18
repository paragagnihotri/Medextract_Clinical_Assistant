"""File Handling Utilities"""
import os
import shutil
from datetime import datetime, timedelta
from fastapi import UploadFile

from app.core.config import settings


async def save_upload_file(file: UploadFile, session_id: str) -> str:
    """Save uploaded file to disk under outputs/uploads/{session_id}/"""
    upload_dir = os.path.join(settings.UPLOAD_DIR, session_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_ext  = os.path.splitext(file.filename)[1]
    safe_name = os.path.splitext(file.filename)[0].replace(" ", "_")[:40]
    file_path = os.path.join(upload_dir, f"{safe_name}{file_ext}")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


async def cleanup_old_files():
    """Remove files older than CLEANUP_HOURS"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=settings.CLEANUP_HOURS)
        
        # Cleanup uploads
        if os.path.exists(settings.UPLOAD_DIR):
            for job_dir in os.listdir(settings.UPLOAD_DIR):
                job_path = os.path.join(settings.UPLOAD_DIR, job_dir)
                if os.path.isdir(job_path):
                    dir_time = datetime.fromtimestamp(os.path.getctime(job_path))
                    if dir_time < cutoff_time:
                        shutil.rmtree(job_path)
        
        # Cleanup reports
        if os.path.exists(settings.REPORT_DIR):
            for job_dir in os.listdir(settings.REPORT_DIR):
                job_path = os.path.join(settings.REPORT_DIR, job_dir)
                if os.path.isdir(job_path):
                    dir_time = datetime.fromtimestamp(os.path.getctime(job_path))
                    if dir_time < cutoff_time:
                        shutil.rmtree(job_path)
                        
    except Exception as e:
        print(f"Cleanup error: {e}")
