import io
import csv
from typing import Dict, Any, List
from pathlib import Path

def generate_csv_report(experiment_data: Dict[str, Any]) -> str:
    """
    Generates a UTF-8 CSV report with complete benchmark results.
    Includes BOM (\ufeff) so Microsoft Excel opens Vietnamese characters cleanly.
    """
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write("\ufeff")
    
    writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    
    # Header metadata
    meta = experiment_data.get("metadata", {})
    writer.writerow(["BÁO CÁO THỬ NGHIỆM ĐÁNH GIÁ VÀ SO SÁNH ĐỊNH DẠNG ẢNH"])
    writer.writerow(["Mã phiên thử nghiệm:", experiment_data.get("experiment_id", "")])
    writer.writerow(["Tên ảnh gốc:", meta.get("filename", "")])
    writer.writerow(["Định dạng gốc:", meta.get("format", "")])
    writer.writerow(["Độ phân giải:", f"{meta.get('width', 0)} x {meta.get('height', 0)} ({meta.get('megapixels', 0)} MP)"])
    writer.writerow(["Chế độ màu:", meta.get("mode", "")])
    writer.writerow(["Dung lượng gốc:", meta.get("formatted_size", "")])
    writer.writerow([])  # Blank line
    
    # Table headers
    writer.writerow([
        "Định dạng mục tiêu",
        "Mức chất lượng (Quality)",
        "Dung lượng (Bytes)",
        "Dung lượng hiển thị",
        "Dung lượng tiết kiệm (%)",
        "Tỷ lệ nén (Ratio)",
        "Bits Per Pixel (bpp)",
        "MSE",
        "PSNR (dB)",
        "SSIM",
        "Thời gian mã hóa (ms)",
        "Đánh giá chất lượng"
    ])
    
    results: List[Dict[str, Any]] = experiment_data.get("results", [])
    for r in results:
        size_info = r.get("size_analysis", {})
        quality_info = r.get("quality_metrics", {})
        
        writer.writerow([
            r.get("target_format", ""),
            r.get("quality", ""),
            size_info.get("compressed_size_bytes", 0),
            size_info.get("formatted_compressed", ""),
            size_info.get("saving_percent", 0.0),
            size_info.get("compression_ratio", 1.0),
            size_info.get("bpp", 0.0),
            quality_info.get("mse", 0.0),
            quality_info.get("psnr_display", ""),
            quality_info.get("ssim", 0.0),
            r.get("encoding_time_ms", 0.0),
            quality_info.get("quality_rating", "")
        ])
        
    writer.writerow([])
    # Recommendation summary
    rec = experiment_data.get("recommendations", {})
    writer.writerow(["TỔNG KẾT KHUYẾN NGHỊ"])
    writer.writerow(["Tóm tắt:", rec.get("summary", "")])
    
    for key, item in rec.get("categories", {}).items():
        if isinstance(item, dict) and "title" in item:
            writer.writerow([
                item.get("title", ""),
                f"Định dạng: {item.get('format', '')} (Q={item.get('quality', '')})",
                f"Dung lượng: {item.get('file_size', '')} (Tiết kiệm {item.get('saving_percent', 0)}%)",
                f"SSIM: {item.get('ssim', '')}",
                f"PSNR: {item.get('psnr', '')}",
                item.get("reason", "")
            ])
            
    return output.getvalue()

def generate_pdf_report(experiment_data: Dict[str, Any], output_path: str) -> bool:
    """
    Generates a structured PDF summary using ReportLab.
    Returns True if successfully generated, False otherwise.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(letter),
            rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25
        )
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=10
        )
        meta = experiment_data.get("metadata", {})
        story.append(Paragraph("Báo Cáo Thực Nghiệm So Sánh Định Dạng Ảnh", title_style))
        story.append(Paragraph(
            f"Phiên thử nghiệm: <b>{experiment_data.get('experiment_id', '')}</b> | "
            f"Tệp gốc: <b>{meta.get('filename', '')}</b> ({meta.get('formatted_size', '')}, "
            f"{meta.get('width', 0)}x{meta.get('height', 0)}px, Mode: {meta.get('mode', '')})",
            styles['Normal']
        ))
        story.append(Spacer(1, 15))
        
        table_data = [[
            "Format", "Quality", "Dung lượng", "Tiết kiệm (%)",
            "Ratio", "MSE", "PSNR", "SSIM", "Encode (ms)", "Đánh giá"
        ]]
        
        for r in experiment_data.get("results", []):
            s = r.get("size_analysis", {})
            q = r.get("quality_metrics", {})
            table_data.append([
                str(r.get("target_format", "")),
                f"Q{r.get('quality', '')}",
                str(s.get("formatted_compressed", "")),
                f"{s.get('saving_percent', 0.0)}%",
                f"{s.get('compression_ratio', 1.0)}x",
                str(q.get("mse", 0.0)),
                str(q.get("psnr_display", "")),
                str(q.get("ssim", 0.0)),
                f"{r.get('encoding_time_ms', 0)} ms",
                str(q.get("quality_rating", ""))[:20]
            ])
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(t)
        
        doc.build(story)
        return True
    except Exception:
        return False

