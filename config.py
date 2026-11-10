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
    # Default 100 Megapixels (~10,000 x 10,000 px) to prevent Out-Of-Memory (OOM) DoS
    MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", 100_000_000))
    
    # Allowed input extensions
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
    
    # Supported target benchmark formats
    SUPPORTED_TARGET_FORMATS = ["JPEG", "PNG", "WEBP"]
    
    # Compression presets tested by default
    QUALITY_PRESETS = [25, 50, 75, 90]
    
    # Experiment cleanup timeout in seconds (default 1 day = 86400s)
    EXPERIMENT_EXPIRY_SECONDS = 86400

class TestConfig(Config):
    """Configuration for automated test suite."""
    TESTING = True
    UPLOAD_FOLDER = str(BASE_DIR / "tests" / "test_uploads")
    OUTPUT_FOLDER = str(BASE_DIR / "tests" / "test_outputs")
    SECRET_KEY = "test-secret-key"
    # Lower threshold for unit tests to easily verify decompression bomb detection
    MAX_IMAGE_PIXELS = 1_000_000  # 1 Megapixel
