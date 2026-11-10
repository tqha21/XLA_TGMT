import json
from pathlib import Path
from typing import List, Dict, Any
from celery import shared_task
from flask import current_app

from app.services.image_converter import convert_image
from app.services.size_analyzer import analyze_size_efficiency
from app.services.quality_analyzer import compute_quality_metrics
from app.services.recommendation import generate_recommendations
from app.services.image_metadata import get_image_metadata

def get_experiment_store_path(experiment_id: str) -> Path:
    """Returns path to cached experiment JSON file in instance folder."""
    instance_dir = Path(current_app.instance_path) / "experiments"
    instance_dir.mkdir(parents=True, exist_ok=True)
    return instance_dir / f"{experiment_id}.json"

@shared_task(bind=True, name="app.tasks.image_tasks.run_image_benchmark_task")
def run_image_benchmark_task(
    self,
    experiment_id: str,
    requested_formats: List[str],
    requested_qualities: List[int]
) -> Dict[str, Any]:
    """
    Asynchronous Celery Task for complete Image Compression Benchmark.
    Provides real-time state updates (PROGRESS) to the client.
    """
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / experiment_id
    if not upload_dir.exists() or not upload_dir.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục tải lên cho phiên {experiment_id}")

    uploaded_files = [f for f in upload_dir.iterdir() if f.is_file() and not f.name.endswith(".gitkeep")]
    if not uploaded_files:
        raise FileNotFoundError(f"Không tìm thấy tệp ảnh gốc trong phiên {experiment_id}")
    source_file_path = str(uploaded_files[0])

    metadata = get_image_metadata(source_file_path)
    output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate total conversion steps for progress tracking
    total_steps = 0
    step_matrix = []
    for fmt in requested_formats:
        fmt_upper = fmt.upper()
        q_list = requested_qualities if fmt_upper != "PNG" else [50, 90]
        for q in q_list:
            total_steps += 1
            step_matrix.append((fmt_upper, int(q)))

    results = []
    original_size = metadata["file_size_bytes"]
    width = metadata["width"]
    height = metadata["height"]
    has_alpha = metadata["has_alpha"]

    # Initial state update
    self.update_state(
        state="PROGRESS",
        meta={
            "current": 0,
            "total": total_steps,
            "percent": 0,
            "status": "Khởi động quy trình nén và phân tích đa định dạng..."
        }
    )

    current_step = 0
    for fmt_upper, q in step_matrix:
        current_step += 1
        percent = int((current_step / total_steps) * 100)
        
        self.update_state(
            state="PROGRESS",
            meta={
                "current": current_step,
                "total": total_steps,
                "percent": percent,
                "status": f"Đang nén {fmt_upper} ở mức chất lượng Q{q} ({current_step}/{total_steps})..."
            }
        )

        conversion_res = convert_image(
            source_path=source_file_path,
            output_dir=str(output_dir),
            target_format=fmt_upper,
            quality=q
        )

        if conversion_res["success"]:
            comp_path = conversion_res["output_path"]
            compressed_size = conversion_res["file_size_bytes"]

            size_res = analyze_size_efficiency(
                original_size_bytes=original_size,
                compressed_size_bytes=compressed_size,
                width=width,
                height=height
            )

            quality_res = compute_quality_metrics(
                reference_path=source_file_path,
                compressed_path=comp_path
            )

            relative_url = f"/media/outputs/{experiment_id}/{conversion_res['filename']}"

            results.append({
                "target_format": fmt_upper,
                "quality": q,
                "filename": conversion_res["filename"],
                "url": relative_url,
                "file_size_bytes": compressed_size,
                "encoding_time_ms": conversion_res["encoding_time_ms"],
                "size_analysis": size_res,
                "quality_metrics": quality_res,
                "success": True
            })
        else:
            results.append({
                "target_format": fmt_upper,
                "quality": q,
                "success": False,
                "error_message": conversion_res.get("error_message", "Chuyển đổi thất bại"),
                "file_size_bytes": 0,
                "encoding_time_ms": 0.0,
                "size_analysis": {},
                "quality_metrics": {}
            })

    # Generate recommendations
    self.update_state(
        state="PROGRESS",
        meta={
            "current": total_steps,
            "total": total_steps,
            "percent": 99,
            "status": "Đang tổng hợp dữ liệu và tạo báo cáo khuyến nghị..."
        }
    )
    recommendations = generate_recommendations(results, has_alpha=has_alpha)

    experiment_data = {
        "experiment_id": experiment_id,
        "metadata": metadata,
        "results": results,
        "recommendations": recommendations,
        "original_preview_url": f"/media/uploads/{experiment_id}/{Path(source_file_path).name}"
    }

    # Persist cache file for reports and web results view
    store_file = get_experiment_store_path(experiment_id)
    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(experiment_data, f, ensure_ascii=False, indent=2)

    return experiment_data
