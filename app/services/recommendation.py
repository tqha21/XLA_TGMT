from typing import List, Dict, Any

def generate_recommendations(results: List[Dict[str, Any]], has_alpha: bool = False) -> Dict[str, Any]:
    """
    Analyzes multi-format conversion results and provides intelligent recommendations
    based on use cases:
    1. Best for Web Performance (Optimal balance of size & perceptual quality)
    2. Best for Maximum Storage/Bandwidth Saving (Smallest size with acceptable SSIM >= 0.85)
    3. Best for Archiving / High Fidelity (Highest PSNR & SSIM)
    4. Transparency Special Recommendation (if image has alpha channel)
    """
    valid_results = [r for r in results if r.get("success") and r.get("quality_metrics", {}).get("success")]
    
    if not valid_results:
        return {
            "summary": "Không có kết quả chuyển đổi hợp lệ để đưa ra khuyến nghị.",
            "categories": {}
        }
        
    # Filter 1: Best Archival / High Quality
    # Sort primarily by SSIM desc, then PSNR desc
    best_quality = max(
        valid_results,
        key=lambda r: (
            r.get("quality_metrics", {}).get("ssim", 0),
            r.get("quality_metrics", {}).get("psnr", 0)
        )
    )
    
    # Filter 2: Maximum Compression (smallest size that maintains acceptable visual quality: SSIM >= 0.85)
    acceptable_candidates = [
        r for r in valid_results
        if r.get("quality_metrics", {}).get("ssim", 0) >= 0.85
    ]
    if acceptable_candidates:
        max_saving = min(acceptable_candidates, key=lambda r: r.get("file_size_bytes", float("inf")))
    else:
        max_saving = min(valid_results, key=lambda r: r.get("file_size_bytes", float("inf")))
        
    # Filter 3: Best for Web (Sweet spot: SSIM >= 0.92, PSNR >= 32 dB, minimizing file size)
    web_candidates = [
        r for r in valid_results
        if r.get("quality_metrics", {}).get("ssim", 0) >= 0.92
        and r.get("quality_metrics", {}).get("psnr", 0) >= 32.0
    ]
    if web_candidates:
        best_web = min(web_candidates, key=lambda r: r.get("file_size_bytes", float("inf")))
    else:
        # Fallback to the one with highest quality-to-size score
        best_web = max(
            valid_results,
            key=lambda r: (
                r.get("quality_metrics", {}).get("ssim", 0) * 1000000 /
                max(r.get("file_size_bytes", 1), 1)
            )
        )
        
    categories = {
        "web": {
            "title": "Khuyến nghị cho Website / Ứng dụng số",
            "badge": "Tối ưu nhất cho Web",
            "format": best_web.get("target_format"),
            "quality": best_web.get("quality"),
            "file_size": best_web.get("size_analysis", {}).get("formatted_compressed"),
            "saving_percent": best_web.get("size_analysis", {}).get("saving_percent"),
            "ssim": best_web.get("quality_metrics", {}).get("ssim"),
            "psnr": best_web.get("quality_metrics", {}).get("psnr_display"),
            "reason": (
                f"Định dạng {best_web.get('target_format')} ở mức chất lượng {best_web.get('quality')} "
                f"đạt điểm cân bằng xuất sắc: tiết kiệm {best_web.get('size_analysis', {}).get('saving_percent')}% dung lượng "
                f"trong khi giữ độ tương đồng cấu trúc SSIM = {best_web.get('quality_metrics', {}).get('ssim')} (mắt thường gần như không thấy khác biệt)."
            )
        },
        "max_compression": {
            "title": "Tiết kiệm băng thông tối đa",
            "badge": "Dung lượng nhỏ nhất",
            "format": max_saving.get("target_format"),
            "quality": max_saving.get("quality"),
            "file_size": max_saving.get("size_analysis", {}).get("formatted_compressed"),
            "saving_percent": max_saving.get("size_analysis", {}).get("saving_percent"),
            "ssim": max_saving.get("quality_metrics", {}).get("ssim"),
            "psnr": max_saving.get("quality_metrics", {}).get("psnr_display"),
            "reason": (
                f"Lựa chọn lý tưởng cho mạng di động 3G/4G yếu hoặc ảnh thumbnail: "
                f"dung lượng chỉ còn {max_saving.get('size_analysis', {}).get('formatted_compressed')} "
                f"(tiết kiệm {max_saving.get('size_analysis', {}).get('saving_percent')}%)."
            )
        },
        "archival": {
            "title": "Lưu trữ / In ấn chất lượng cao",
            "badge": "Độ chi tiết tối đa",
            "format": best_quality.get("target_format"),
            "quality": best_quality.get("quality"),
            "file_size": best_quality.get("size_analysis", {}).get("formatted_compressed"),
            "saving_percent": best_quality.get("size_analysis", {}).get("saving_percent"),
            "ssim": best_quality.get("quality_metrics", {}).get("ssim"),
            "psnr": best_quality.get("quality_metrics", {}).get("psnr_display"),
            "reason": (
                f"Định dạng {best_quality.get('target_format')} giữ trọn vẹn chi tiết gốc với PSNR {best_quality.get('quality_metrics', {}).get('psnr_display')} "
                f"và SSIM = {best_quality.get('quality_metrics', {}).get('ssim')}, phù hợp cho in ấn và thiết kế chuyên nghiệp."
            )
        }
    }
    
    if has_alpha:
        categories["transparency_note"] = {
            "title": "Lưu ý kênh trong suốt (Alpha Channel)",
            "message": "Ảnh gốc có chứa vùng trong suốt. Hãy ưu tiên WEBP hoặc PNG để tránh bị phủ nền trắng khi lưu dạng JPEG."
        }
        
    return {
        "summary": f"Đã phân tích {len(valid_results)} cấu hình. Định dạng được khuyến nghị hàng đầu cho Web là {best_web.get('target_format')} (Quality {best_web.get('quality')}).",
        "categories": categories
    }

