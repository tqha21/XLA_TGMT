from pathlib import Path
from PIL import Image
import pytest
from app.services.image_converter import convert_image, prepare_image_for_format

def test_convert_rgb_to_formats(tmp_path):
    src_path = tmp_path / "source.png"
    img = Image.new("RGB", (200, 150), color=(50, 100, 150))
    img.save(str(src_path))
    
    out_dir = tmp_path / "outputs"
    
    # Test JPEG
    res_jpeg = convert_image(str(src_path), str(out_dir), "JPEG", quality=80)
    assert res_jpeg["success"] is True
    assert res_jpeg["resolution_preserved"] is True
    assert res_jpeg["dimensions"] == (200, 150)
    assert res_jpeg["encoding_time_ms"] >= 0
    assert Path(res_jpeg["output_path"]).exists()
    
    # Test WebP
    res_webp = convert_image(str(src_path), str(out_dir), "WEBP", quality=75)
    assert res_webp["success"] is True
    assert res_webp["resolution_preserved"] is True
    assert Path(res_webp["output_path"]).exists()
    
    # Test PNG
    res_png = convert_image(str(src_path), str(out_dir), "PNG", quality=90)
    assert res_png["success"] is True
    assert res_png["resolution_preserved"] is True
    assert Path(res_png["output_path"]).exists()

def test_rgba_transparency_handling_for_jpeg(tmp_path):
    """
    JPEG cannot handle RGBA natively.
    Converter must automatically composite on white background and avoid OSError.
    """
    src_rgba = tmp_path / "transparent.png"
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))  # Red with 50% opacity
    img.save(str(src_rgba))
    
    out_dir = tmp_path / "outputs"
    res = convert_image(str(src_rgba), str(out_dir), "JPEG", quality=85)
    assert res["success"] is True
    assert res["error_message"] is None
    
    # Verify saved image is valid RGB JPEG
    with Image.open(res["output_path"]) as out_img:
        assert out_img.format == "JPEG"
        assert out_img.mode == "RGB"

