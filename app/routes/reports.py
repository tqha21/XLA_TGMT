import json
from pathlib import Path
from flask import Blueprint, request, jsonify, Response, current_app, send_file
from app.services.report_generator import generate_csv_report, generate_pdf_report
from app.routes.analysis import get_experiment_store_path

reports_bp = Blueprint("reports_bp", __name__)

@reports_bp.route("/api/experiments/<experiment_id>/report", methods=["GET"])
def export_report(experiment_id: str):
    """
    FR-10: Export benchmark report in CSV, PDF, or JSON format.
    Usage:
    GET /api/experiments/<id>/report?format=csv (default)
    GET /api/experiments/<id>/report?format=pdf
    GET /api/experiments/<id>/report?format=json
    """
    store_file = get_experiment_store_path(experiment_id)
    if not store_file.exists():
        return jsonify({"status": "error", "message": "Phiên thử nghiệm không tồn tại."}), 404
        
    with open(store_file, "r", encoding="utf-8") as f:
        experiment_data = json.load(f)
        
    export_format = request.args.get("format", "csv").lower()
    
    if export_format == "csv":
        csv_content = generate_csv_report(experiment_data)
        return Response(
            csv_content,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=benchmark_{experiment_id[:8]}.csv"
            }
        )
        
    elif export_format == "pdf":
        pdf_path = Path(current_app.config["OUTPUT_FOLDER"]) / experiment_id / f"report_{experiment_id[:8]}.pdf"
        success = generate_pdf_report(experiment_data, str(pdf_path))
        if success and pdf_path.exists():
            return send_file(
                str(pdf_path),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"benchmark_{experiment_id[:8]}.pdf"
            )
        else:
            return jsonify({
                "status": "error",
                "message": "Không thể xuất file PDF (yêu cầu thư viện reportlab hoặc lỗi tạo file)."
            }), 500
            
    elif export_format == "json":
        return Response(
            json.dumps(experiment_data, ensure_ascii=False, indent=2),
            mimetype="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=benchmark_{experiment_id[:8]}.json"
            }
        )
        
    else:
        return jsonify({
            "status": "error",
            "message": f"Định dạng xuất '{export_format}' không được hỗ trợ. Sử dụng 'csv', 'pdf', hoặc 'json'."
        }), 400

