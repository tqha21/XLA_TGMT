import math
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image

def _compute_ssim_numpy(img1_np: np.ndarray, img2_np: np.ndarray) -> float:
    """
    Pure NumPy implementation of SSIM (Structural Similarity Index) as a resilient fallback.
    Formula: SSIM(x, y) = (2 * mu_x * mu_y + C1)(2 * sigma_xy + C2) / 
                          ((mu_x^2 + mu_y^2 + C1)(sigma_x^2 + sigma_y^2 + C2))
    """
    # Convert to float64
    x = img1_np.astype(np.float64)
    y = img2_np.astype(np.float64)
    
    # Dynamic range constants for 8-bit image
    K1, K2 = 0.01, 0.03
    L = 255.0
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2
    
    mu_x = np.mean(x)
    mu_y = np.mean(y)
    
    sigma_x_sq = np.var(x)
    sigma_y_sq = np.var(y)
    sigma_xy = np.mean((x - mu_x) * (y - mu_y))
    
    numerator = (2.0 * mu_x * mu_y + C1) * (2.0 * sigma_xy + C2)
    denominator = (mu_x ** 2 + mu_y ** 2 + C1) * (sigma_x_sq + sigma_y_sq + C2)
    
    if denominator == 0:
        return 1.0 if numerator == 0 else 0.0
        
    ssim_val = numerator / denominator
    return float(np.clip(ssim_val, -1.0, 1.0))

def compute_quality_metrics(reference_path: str, compressed_path: str) -> Dict[str, Any]:
    """
    Computes MSE, PSNR, and SSIM between original reference image and compressed image.
    Safely normalizes color space, dimensions, and handles edge cases (like identical images).
    """
    try:
        with Image.open(reference_path) as ref_img, Image.open(compressed_path) as comp_img:
            # Normalize to RGB mode for standardized pixel comparison
            # If reference has alpha, composite over white to match JPEG/standard behavior
            if ref_img.mode in ("RGBA", "LA") or (ref_img.mode == "P" and "transparency" in ref_img.info):
                bg = Image.new("RGBA", ref_img.size, (255, 255, 255, 255))
                ref_norm = Image.alpha_composite(bg, ref_img.convert("RGBA")).convert("RGB")
            else:
                ref_norm = ref_img.convert("RGB")
                
            if comp_img.mode in ("RGBA", "LA") or (comp_img.mode == "P" and "transparency" in comp_img.info):
                bg = Image.new("RGBA", comp_img.size, (255, 255, 255, 255))
                comp_norm = Image.alpha_composite(bg, comp_img.convert("RGBA")).convert("RGB")
            else:
                comp_norm = comp_img.convert("RGB")
                
            # Ensure dimensions match
            if ref_norm.size != comp_norm.size:
                comp_norm = comp_norm.resize(ref_norm.size, Image.Resampling.LANCZOS)
                
            ref_array = np.array(ref_norm, dtype=np.float64)
            comp_array = np.array(comp_norm, dtype=np.float64)
            
        # 1. MSE (Mean Squared Error)
        diff = ref_array - comp_array
        mse = float(np.mean(diff ** 2))
        
        # 2. PSNR (Peak Signal-to-Noise Ratio)
        if mse == 0.0:
            psnr = float("inf")
            psnr_display = "∞ dB (Lossless)"
            quality_rating = "Hoàn hảo (Không suy hao)"
        else:
            psnr = 10.0 * math.log10((255.0 ** 2) / mse)
            psnr_display = f"{psnr:.2f} dB"
            
            if psnr >= 45.0:
                quality_rating = "Xuất sắc (Không nhận thấy biến dạng)"
            elif psnr >= 35.0:
                quality_rating = "Rất tốt (Chất lượng cao)"
            elif psnr >= 28.0:
                quality_rating = "Tốt (Chấp nhận được trên Web)"
            elif psnr >= 20.0:
                quality_rating = "Trung bình (Có thể thấy nhiễu mờ)"
            else:
                quality_rating = "Kém (Mất nhiều chi tiết)"
                
        # 3. SSIM (Structural Similarity Index)
        try:
            from skimage.metrics import structural_similarity as skimage_ssim
            # Try skimage with channel_axis (scikit-image >= 0.19)
            try:
                ssim_score = float(skimage_ssim(
                    ref_array,
                    comp_array,
                    data_range=255.0,
                    channel_axis=2
                ))
            except TypeError:
                # Older scikit-image API
                ssim_score = float(skimage_ssim(
                    ref_array,
                    comp_array,
                    data_range=255.0,
                    multichannel=True
                ))
        except (ImportError, Exception):
            # Pure NumPy fallback
            ssim_score = _compute_ssim_numpy(ref_array, comp_array)
            
        ssim_score = round(float(np.clip(ssim_score, 0.0, 1.0)), 4)
        
        return {
            "success": True,
            "mse": round(mse, 4),
            "psnr": 100.0 if math.isinf(psnr) else round(psnr, 2),
            "is_lossless": math.isinf(psnr),
            "psnr_display": psnr_display,
            "ssim": ssim_score,
            "quality_rating": quality_rating,
            "error_message": None
        }
        
    except Exception as exc:
        return {
            "success": False,
            "mse": 0.0,
            "psnr": 0.0,
            "is_lossless": False,
            "psnr_display": "N/A",
            "ssim": 0.0,
            "quality_rating": "Lỗi phân tích",
            "error_message": f"Lỗi tính toán chỉ số chất lượng: {str(exc)}"
        }

