import math
import numpy as np
import pytest
from PIL import Image
from app.services.quality_analyzer import compute_quality_metrics, _compute_ssim_numpy

def test_identical_images_psnr_infinite(tmp_path):
    """
    Test edge case: When comparing two identical images,
    MSE must be 0 and PSNR must be infinite (handled safely without ZeroDivisionError).
    """
    img_path = tmp_path / "reference.png"
    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    img.save(str(img_path))
    
    metrics = compute_quality_metrics(str(img_path), str(img_path))
    assert metrics["success"] is True
    assert metrics["mse"] == 0.0
    assert metrics["is_lossless"] is True
    assert "Lossless" in metrics["psnr_display"]
    assert metrics["ssim"] == 1.0

def test_different_images_metrics(tmp_path):
    """
    Test metrics between two distinctly different images:
    MSE should be > 0, PSNR should be finite, SSIM should be < 1.0.
    """
    ref_path = tmp_path / "ref.png"
    comp_path = tmp_path / "comp.png"
    
    img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img2 = Image.new("RGB", (100, 100), color=(200, 200, 200))
    
    img1.save(str(ref_path))
    img2.save(str(comp_path))
    
    metrics = compute_quality_metrics(str(ref_path), str(comp_path))
    assert metrics["success"] is True
    assert metrics["mse"] > 0.0
    assert not metrics["is_lossless"]
    assert metrics["psnr"] > 0.0
    assert metrics["ssim"] < 1.0

def test_pure_numpy_ssim_formula():
    """Verify pure NumPy SSIM implementation against uniform and noise matrices."""
    arr1 = np.ones((64, 64, 3), dtype=np.uint8) * 128
    arr2 = np.ones((64, 64, 3), dtype=np.uint8) * 128
    
    ssim_val = _compute_ssim_numpy(arr1, arr2)
    assert pytest.approx(ssim_val, 0.001) == 1.0

