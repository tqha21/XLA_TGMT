import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-image-format-benchmark-key-2026")
    
    # Upload and Output directories
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", str(BASE_DIR / "outputs"))
    SAMPLE_FOLDER = str(BASE_DIR / "data" / "sample_images")
    
    # File Limits: 20 MB strictly enforced
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 Megabytes
    
    # Pixel Limits: Decompression Bomb Attack Defense (Image Bomb)
    MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", 100_000_000))
    
    # Allowed input extensions
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
    
    # Supported target benchmark formats
    SUPPORTED_TARGET_FORMATS = ["JPEG", "PNG", "WEBP"]
    
    # Compression presets tested by default
    QUALITY_PRESETS = [25, 50, 75, 90]
    
    # Experiment cleanup timeout in seconds (default 1 day = 86400s)
    EXPERIMENT_EXPIRY_SECONDS = 86400

    # =========================================================================
    # Celery & Redis Task Queue Configuration
    # =========================================================================
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    CELERY = {
        "broker_url": CELERY_BROKER_URL,
        "result_backend": CELERY_RESULT_BACKEND,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "result_expires": 86400,
        "task_track_started": True,
        "worker_prefetch_multiplier": 1,  # Fair distribution of heavy image tasks
        "task_acks_late": True,           # Resilient against worker crash
    }

class TestConfig(Config):
    """Configuration for automated test suite."""
    TESTING = True
    UPLOAD_FOLDER = str(BASE_DIR / "tests" / "test_uploads")
    OUTPUT_FOLDER = str(BASE_DIR / "tests" / "test_outputs")
    SECRET_KEY = "test-secret-key"
    MAX_IMAGE_PIXELS = 1_000_000  # 1 Megapixel for quick unit testing

    # Eager execution for Celery in testing environment (no live Redis required for tests)
    CELERY = {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,
        "task_store_eager_result": True,
        "task_eager_propagates": True,
    }
