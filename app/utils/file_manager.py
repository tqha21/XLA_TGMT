import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def create_experiment_id() -> str:
    """Generate a clean unique experiment ID."""
    return str(uuid.uuid4())

def save_uploaded_file(file: FileStorage, upload_dir: str, experiment_id: str) -> Tuple[str, str]:
    """
    Saves an uploaded file into an isolated experiment subfolder.
    Returns:
        (saved_file_path, safe_file_name)
    """
    exp_dir = Path(upload_dir) / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    original_name = file.filename or "upload.png"
    safe_name = secure_filename(original_name)
    if not safe_name:
        safe_name = f"image_{int(time.time())}.png"
        
    save_path = exp_dir / safe_name
    file.seek(0)
    file.save(str(save_path))
    
    return str(save_path), safe_name

def cleanup_experiment_folders(experiment_id: str, upload_dir: str, output_dir: str) -> bool:
    """Safely removes all upload and output folders associated with an experiment."""
    success = True
    for directory in [upload_dir, output_dir]:
        exp_dir = Path(directory) / experiment_id
        if exp_dir.exists() and exp_dir.is_dir():
            try:
                shutil.rmtree(exp_dir)
            except Exception:
                success = False
    return success

def clean_expired_experiments(base_dir: str, max_age_seconds: int = 86400) -> int:
    """
    Deletes subdirectories older than max_age_seconds in base_dir.
    Returns count of removed directories.
    """
    removed_count = 0
    now = time.time()
    path = Path(base_dir)
    if not path.exists():
        return 0
        
    for item in path.iterdir():
        if item.is_dir():
            try:
                mtime = item.stat().st_mtime
                if (now - mtime) > max_age_seconds:
                    shutil.rmtree(item)
                    removed_count += 1
            except Exception:
                pass
    return removed_count

