# KỊCH BẢN THUYẾT TRÌNH BÁO CÁO & BẢO VỆ ĐỒ ÁN
## ĐỀ TÀI: HỆ THỐNG ĐÁNH GIÁ & SO SÁNH HIỆU QUẢ NÉN ẢNH ĐA ĐỊNH DẠNG (ImageBench)

---

### Slide 1: Trang bìa & Giới thiệu
- **Nội dung hiển thị:**
  - Tên đề tài: *Nghiên cứu, Thiết kế và Triển khai Hệ thống Đánh giá & So sánh Định dạng Ảnh Nén trên nền tảng Flask Web*.
  - Giảng viên hướng dẫn: ...
  - Sinh viên thực hiện: ...
- **Lời thuyết trình mẫu:**
  > "Kính thưa Thầy/Cô và các bạn, hôm nay nhóm chúng em xin được báo cáo đề tài nghiên cứu và xây dựng hệ thống ImageBench - một giải pháp toàn diện giúp đo lường, phân tích thực nghiệm và đưa ra khuyến nghị định dạng ảnh tối ưu cho các hệ thống ứng dụng Web và Mobile hiện đại."

---

### Slide 2: Đặt vấn đề & Mục tiêu nghiên cứu
- **Nội dung hiển thị:**
  - Vấn đề: Hình ảnh chiếm hơn 65% tổng dung lượng tải của một trang web điển hình.
  - Thách thức: Chọn sai định dạng hoặc mức nén dẫn đến suy giảm trải nghiệm người dùng, tăng chi phí băng thông, hoặc làm biến dạng chi tiết hình ảnh.
  - Mục tiêu: Xây dựng công cụ trực quan để so sánh tự động **JPEG, PNG, WebP, AVIF** ở các mức nén khác nhau bằng các chỉ số thị giác khách quan (**PSNR, SSIM, MSE**) và chỉ số nén (**Dung lượng, Tỷ lệ tiết kiệm, Bits-per-pixel**).
- **Lời thuyết trình mẫu:**
  > "Trong thời đại tối ưu hóa trải nghiệm số, việc giảm dù chỉ 100KB ảnh cũng có thể cải thiện đáng kể điểm Core Web Vitals và thời gian phản hồi. Tuy nhiên, lập trình viên thường chọn định dạng theo thói quen thay vì dựa trên số liệu thực nghiệm. Dự án của chúng em giải quyết bài toán này bằng cách cung cấp bằng chứng định lượng chính xác theo chuẩn thị giác con người."

---

### Slide 3: Kiến trúc Hệ thống (Flask Application Factory)
- **Nội dung hiển thị:**
  - Sơ đồ kiến trúc Flask Modular:
    - *Routes Layer:* Tiếp nhận HTTP/REST request (`upload`, `analysis`, `reports`, `main`).
    - *Services Layer:* `image_converter`, `quality_analyzer`, `size_analyzer`, `recommendation`, `report_generator`.
    - *Utils Layer:* `validators` (kiểm tra an toàn), `file_manager` (quản lý bộ nhớ tạm).
  - Công nghệ sử dụng: Python 3.11+, Flask 3, Pillow, NumPy, Scikit-image, Chart.js, ReportLab.
- **Lời thuyết trình mẫu:**
  > "Hệ thống được thiết kế theo mô hình Flask Application Factory chuyên nghiệp. Tách biệt hoàn toàn giữa tầng định tuyến API và tầng xử lý logic nghiệp vụ, đảm bảo dễ dàng mở rộng, cô lập lỗi và hỗ trợ viết unit test độc lập."

---

### Slide 4: Cơ sở Lý thuyết & Chỉ số Đánh giá Chất lượng
- **Nội dung hiển thị:**
  - **MSE (Mean Squared Error):** Đo sai số bình phương trung bình trên từng kênh màu.
  - **PSNR (Peak Signal-to-Noise Ratio):** Tỷ số đỉnh tín hiệu trên nhiễu ($PSNR = 10 \cdot \log_{10}(255^2 / MSE)$). Thang đo dB: > 40 dB (rất tốt), 30-40 dB (chuẩn web), < 30 dB (nhiễu).
  - **SSIM (Structural Similarity Index):** Đánh giá độ tương đồng cấu trúc theo mô hình thị giác người (HVS), thang điểm từ 0.0 đến 1.0.
  - **Chỉ số nén:** Space Saving Percentage, Compression Ratio, Bits Per Pixel (bpp).
- **Lời thuyết trình mẫu:**
  > "Thay vì chỉ so sánh dung lượng đơn thuần, hệ thống tích hợp cả hai chỉ số quan trọng nhất của xử lý ảnh: PSNR đo sai lệch số học pixel và SSIM đo độ tương đồng về độ tương phản, cấu trúc ánh sáng theo cơ chế cảm nhận của mắt người."

---

### Slide 5: Xử lý Kỹ thuật Chuyên sâu & Trường hợp Biên (Edge Cases)
- **Nội dung hiển thị:**
  - *Xử lý kênh trong suốt (Alpha RGBA):* Tự động dán composite trên nền trắng khi lưu định dạng JPEG để chống crash `OSError`.
  - *Xử lý ảnh giống hệt ($MSE = 0$):* Nhận diện và gán $PSNR = \infty$ an toàn, tránh lỗi chia cho 0 (`ZeroDivisionError`).
  - *Bảo mật tải tệp:* Kiểm tra Magic bytes bằng `Pillow.verify()`, giới hạn kích thước nghiêm ngặt 20MB, chống decompression bomb.
  - *Fallback SSIM:* Cung cấp hàm thuần NumPy tự tính toán nếu thư viện ngoài gặp sự cố môi trường.
- **Lời thuyết trình mẫu:**
  > "Về mặt lập trình, nhóm đã chú trọng đặc biệt vào tính bền bỉ của hệ thống. Chúng em bắt trọn các trường hợp biên như ảnh có kênh trong suốt khi chuyển sang JPEG, xử lý an toàn toán học khi 2 ảnh giống hệt nhau, và cơ chế fallback đảm bảo hệ thống không bao giờ bị dừng đột ngột."

---

### Slide 6: Giao diện Người dùng & Tính năng Nổi bật
- **Nội dung hiển thị:**
  - *Split Comparison Slider:* Thanh trượt chia đôi kéo qua lại soi từng điểm ảnh theo thời gian thực.
  - *Side-by-Side Mode:* Chế độ đối chiếu 2 ảnh cạnh nhau.
  - *Dashboard 4 Biểu đồ:* Dung lượng (KB), Đường cong Rate-Distortion, SSIM score, Thời gian mã hóa CPU.
  - *Recommendation Engine:* Gợi ý thông minh cho Web, Thumbnail, và Lưu trữ in ấn.
  - *Report Exporter:* Xuất báo cáo CSV UTF-8 mở ngay trên Excel và tài liệu PDF.

---

### Slide 7: Kết quả Thực nghiệm Hàng loạt trên Bộ Dữ Liệu Đa Dạng
- **Nội dung hiển thị:**
  - Thực nghiệm trên 25+ ảnh mẫu thuộc 6 nhóm: Phong cảnh, Chân dung, Chữ/Đồ họa vector, Kênh Alpha, Ảnh chụp đêm, Ảnh giao diện UI.
  - Kết luận thực nghiệm:
    1. **WebP** là lựa chọn cân bằng tốt nhất cho Web: Giảm 65-75% dung lượng ở mức Q75 mà vẫn giữ SSIM > 0.94.
    2. **PNG** tối ưu tuyệt đối cho đồ họa vector và chữ nét mảnh không nhòe biên.
    3. **JPEG** tương thích 100% nhưng gặp nhược điểm nhiễu khối (blocking artifact) ở các vùng chữ tương phản cao khi nén dưới Q50.

---

### Slide 8: Kịch Bản Demo Trực Tiếp (Live Demo)
*(Thực hiện trực tiếp 5 bước trên trình duyệt localhost:5000: Tải ảnh -> Xem metadata -> Chọn cấu hình -> Kéo thanh trượt so sánh -> Xuất file CSV).*

---

### Slide 9: Tiêu chí Nghiệm thu (Definition of Done)
- **Nội dung hiển thị:** Bảng kiểm tra 10/10 tiêu chí nghiệm thu đã hoàn thành xuất sắc:
  - [x] Flask khởi động ổn định.
  - [x] Đọc metadata chính xác.
  - [x] Chuyển đổi JPEG, PNG, WebP thành công.
  - [x] Tính đúng MSE, PSNR, SSIM.
  - [x] Đo dung lượng và thời gian mã hóa.
  - [x] Biểu đồ Chart.js trực quan.
  - [x] Xử lý lỗi an toàn.
  - [x] Bộ ảnh mẫu đa dạng (>20 ảnh).
  - [x] Tài liệu SRS, README, Báo cáo thực nghiệm đầy đủ.
  - [x] Kịch bản demo hoàn chỉnh.

---

### Slide 10: Tổng kết & Hướng Phát Triển
- **Nội dung hiển thị:**
  - Kết quả đạt được: Ứng dụng chạy mượt mà, đầy đủ chức năng P0 & P1, kiểm thử tự động đạt 100%.
  - Hướng phát triển: Bổ sung module nén nâng cao (AVIF/JXL chuyên sâu), tích hợp hàng đợi Celery/Redis cho xử lý ảnh hàng loạt dung lượng lớn.
- **Lời thuyết trình mẫu:**
  > "Nhóm chúng em xin chân thành cảm ơn Thầy/Cô đã lắng nghe. Chúng em rất mong nhận được những góp ý quý báu từ Hội đồng!"

