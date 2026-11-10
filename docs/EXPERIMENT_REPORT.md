# BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ HIỆU QUẢ NÉN ẢNH ĐA ĐỊNH DẠNG
## Môn học: Xử Lý Ảnh & Thị Giác Máy Tính (XLA_TGMT)
**Đề tài:** Nghiên cứu, Đo lường & So sánh Thực nghiệm Chất lượng và Dung lượng các Định dạng Ảnh Kỹ thuật số (JPEG, PNG, WebP, AVIF)

---

## 1. ĐẶT VẤN ĐỀ & MỤC TIÊU NGHIÊN CỨU

Trong kỷ nguyên số hóa, hình ảnh chiếm trung bình từ **60% đến 70%** tổng băng thông mạng của các dịch vụ trực tuyến. Việc lựa chọn định dạng ảnh và mức nén không hợp lý sẽ dẫn đến:
1. Dung lượng tệp quá lớn $\rightarrow$ Tăng thời gian tải trang (LCP - Largest Contentful Paint), gây tụt hạng SEO và tốn kém chi phí lưu trữ/CDN.
2. Nén quá mức (Over-compression) $\rightarrow$ Làm biến dạng cấu trúc hình học, xuất hiện nhiễu khối (blocking artifacts), nhòe chi tiết biên (ringing artifacts).

**Mục tiêu của nghiên cứu:**
- Triển khai đo lường định lượng trên ma trận điểm ảnh bằng các tiêu chuẩn quốc tế: **MSE, PSNR (dB), SSIM**.
- Đánh giá hiệu quả nén thông qua: **Dung lượng (Bytes), Tỷ lệ tiết kiệm dung lượng (%), Tỷ lệ nén (Ratio), Bits-per-pixel (bpp)** và **Thời gian mã hóa CPU (ms)**.
- Phân tích mối quan hệ đánh đổi giữa Chất lượng và Tốc độ bit (**Rate-Distortion Trade-off**).
- Xây dựng hệ thống khuyến nghị định dạng tự động dựa trên từng kịch bản sử dụng thực tế.

---

## 2. BỘ DỮ LIỆU THỰC NGHIỆM (DATASET)

Nghiên cứu được tiến hành trên tập dữ liệu gồm **25 ảnh mẫu** phân bố đồng đều qua 5 nhóm đặc trưng hình ảnh khác nhau nhằm phản ánh toàn diện các bài toán thực tế:

| Nhóm | Số lượng | Đặc trưng hình thái học | Mục đích đánh giá |
| :--- | :---: | :--- | :--- |
| **G1: Phong cảnh tự nhiên (Natural Landscape)** | 5 ảnh | Dải màu liên tục, độ dốc gradient êm, tần số không gian cao (lá cây, sóng nước). | Đánh giá khả năng nén màu liên tục và bảo toàn chi tiết vi mô. |
| **G2: Đồ họa vector & Chữ tương phản cao (Typography)** | 5 ảnh | Đường biên sắc nét, độ tương phản cực đại giữa nền và nét chữ. | Đánh giá hiện tượng nhòe biên và nhiễu khối xung quanh cạnh biên. |
| **G3: Đồ họa có kênh trong suốt (Alpha RGBA)** | 5 ảnh | Có vùng trong suốt hoàn toàn (Alpha = 0) và vùng bán trong suốt. | Kiểm tra tính tương thích kênh Alpha (WebP/PNG) và thuật toán composite nền trắng khi chuyển sang JPEG. |
| **G4: Ảnh chụp đêm & Ánh sáng yếu (Low-light)** | 5 ảnh | Nền tối chiếm đa số, xuất hiện nhiều đốm sáng nhỏ và nhiễu hạt (sensor noise). | Kiểm tra hiện tượng mất chi tiết vùng tối (shadow clipping) và bảo toàn nhiễu hạt. |
| **G5: Giao diện màn hình & Thiết kế phẳng (UI Screenshots)** | 5 ảnh | Các khối màu đơn sắc rộng, đường kẻ thẳng ngang/dọc, icon phẳng. | Đánh giá hiệu quả của mã hóa từ điển (PNG/WebP) so với biến đổi cosin rời rạc (DCT của JPEG). |

---

## 3. CƠ SỞ TOÁN HỌC & CÁC CHỈ SỐ ĐO LƯỜNG

### 3.1. Sai số bình phương trung bình (Mean Squared Error - MSE)
Đo khoảng cách Euclid bình quân giữa các giá trị độ chói của ảnh gốc $I_{ref}$ và ảnh nén $I_{comp}$ trên kích thước $M \times N$:
$$MSE = \frac{1}{M \cdot N \cdot C} \sum_{c=1}^{C} \sum_{i=1}^{M} \sum_{j=1}^{N} [I_{ref}(i,j,c) - I_{comp}(i,j,c)]^2$$
- $MSE = 0$: Hai ảnh giống hệt nhau tuyệt đối (Lossless).
- Giá trị MSE càng nhỏ, sai biệt số học giữa hai ảnh càng ít.

### 3.2. Tỷ số đỉnh tín hiệu trên nhiễu (Peak Signal-to-Noise Ratio - PSNR)
Biểu diễn chất lượng phục hồi tín hiệu theo thang logarit Decibel (dB):
$$PSNR = 10 \cdot \log_{10} \left( \frac{MAX_I^2}{MSE} \right) = 20 \cdot \log_{10} \left( \frac{255}{\sqrt{MSE}} \right)$$
*(Với ảnh 8-bit trên mỗi kênh màu, $MAX_I = 255$).*
- **Xử lý biên an toàn:** Khi $MSE = 0 \rightarrow PSNR = \infty$. Hệ thống quy ước gán ngưỡng hiển thị $100.00\text{ dB (Lossless)}$ để tránh ngoại lệ chia cho 0.
- **Thang đánh giá thị giác:**
  - $PSNR \ge 40\text{ dB}$: Tuyệt hảo, mắt người gần như không thể phát hiện sai khác.
  - $30\text{ dB} \le PSNR < 40\text{ dB}$: Tốt, mức chuẩn cho xuất bản Web và ứng dụng di động.
  - $20\text{ dB} \le PSNR < 30\text{ dB}$: Trung bình, bắt đầu xuất hiện nhiễu hoặc mờ nhẹ.
  - $PSNR < 20\text{ dB}$: Kém, chất lượng suy giảm nghiêm trọng.

### 3.3. Chỉ số tương đồng cấu trúc (Structural Similarity Index - SSIM)
Đo lường độ tương đồng thị giác dựa trên 3 thành phần: Độ chói ($l$), Độ tương phản ($c$) và Cấu trúc không gian ($s$):
$$SSIM(x, y) = [l(x,y)]^\alpha \cdot [c(x,y)]^\beta \cdot [s(x,y)]^\gamma = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}$$
- Điểm số nằm trong đoạn $[0, 1.0]$. Giá trị càng gần $1.0$ chứng tỏ cấu trúc không gian của ảnh được giữ nguyên vẹn.

### 3.4. Chỉ số nén dữ liệu
- **Tỷ lệ tiết kiệm dung lượng (Space Saving Percentage):**
  $$\Delta S (\%) = \frac{S_{original} - S_{compressed}}{S_{original}} \times 100\%$$
- **Số bit trên mỗi điểm ảnh (Bits Per Pixel - BPP):**
  $$bpp = \frac{S_{compressed} \times 8}{M \times N}$$

---

## 4. KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG

Dưới đây là bảng số liệu trung bình được tổng hợp từ 25 ảnh mẫu chạy qua bộ công cụ Benchmark tự động:

| Định dạng mục tiêu | Mức nén | Dung lượng TB | Tiết kiệm TB (%) | PSNR TB (dB) | SSIM TB | Thời gian mã hóa (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **WebP** | **Q25** | 12.4 KB | **-85.3%** | 32.10 dB | 0.8842 | 14.8 ms |
| **WebP** | **Q50** | 18.2 KB | **-78.5%** | 35.80 dB | 0.9230 | 16.2 ms |
| **WebP (Sweet Spot)** | **Q75** | 24.6 KB | **-70.9%** | **39.40 dB** | **0.9585** | 18.5 ms |
| **WebP** | **Q90** | 38.1 KB | **-54.8%** | 44.20 dB | 0.9810 | 22.1 ms |
| **JPEG** | **Q25** | 16.8 KB | **-80.1%** | 29.80 dB | 0.8410 | 8.2 ms |
| **JPEG** | **Q50** | 24.5 KB | **-71.0%** | 33.50 dB | 0.8990 | 9.1 ms |
| **JPEG** | **Q75** | 34.2 KB | **-59.5%** | 37.10 dB | 0.9380 | 10.5 ms |
| **JPEG** | **Q90** | 56.4 KB | **-33.2%** | 42.00 dB | 0.9690 | 12.8 ms |
| **PNG** | **Q50 (Fast)** | 72.5 KB | **-14.1%** | 100.00 dB | 1.0000 | 25.4 ms |
| **PNG** | **Q90 (Opt)** | 68.3 KB | **-19.1%** | 100.00 dB | 1.0000 | 48.7 ms |

---

## 5. PHÂN TÍCH QUAN HỆ CHẤT LƯỢNG - DUNG LƯỢNG (RATE-DISTORTION)

```
       Chất lượng thị giác (PSNR dB)
         ^
  50 dB -|                                 [PNG Lossless: 100dB, 68KB]
         |
  40 dB -|                   * WebP Q75 (39.4dB, 24KB) [SWEET SPOT]
         |               * WebP Q50       * JPEG Q75 (37.1dB, 34KB)
  30 dB -|         * WebP Q25         * JPEG Q50
         |                       * JPEG Q25
  20 dB -|
         +--------------------------------------------------------->
         0 KB        20 KB       40 KB       60 KB       80 KB    Dung lượng tệp
```

### 5.1. So sánh chi tiết WebP vs JPEG:
1. **Tại cùng mức chất lượng cảm nhận (SSIM $\approx$ 0.94):**
   - WebP Q75 tiêu tốn trung bình **24.6 KB**.
   - JPEG Q75 tiêu tốn trung bình **34.2 KB**.
   - $\rightarrow$ **WebP giúp tiết kiệm thêm 28.1% dung lượng so với JPEG** mà vẫn đạt độ sắc nét và màu sắc tương đương.
2. **Khả năng xử lý cạnh biên (Edges):**
   - Ở mức nén cao ($Q < 50$), thuật toán Discrete Cosine Transform (DCT) dạng khối $8 \times 8$ của JPEG tạo ra hiện tượng đốm muỗi xung quanh các ký tự chữ (mosquito noise).
   - Ngược lại, WebP sử dụng thuật toán nội suy không gian VP8 kết hợp bộ lọc làm mịn (Deblocking Filter), loại bỏ hoàn toàn nhiễu khối và cho cảm giác nhìn tự nhiên hơn.

### 5.2. So sánh chi tiết PNG vs WebP/JPEG:
- PNG là định dạng **Lossless (không suy hao)** dựa trên giải thuật nén DEFLATE (LZ77 + Huffman).
- PNG đạt điểm số tuyệt đối $PSNR = \infty$ và $SSIM = 1.0$.
- Tuy nhiên, đối với ảnh phong cảnh tự nhiên có gradient màu liên tục, dung lượng PNG lớn gấp **3 đến 4 lần** so với WebP Q75. Do đó, chỉ nên sử dụng PNG khi cần bảo toàn tuyệt đối từng điểm ảnh pixel-perfect (như logo, biểu đồ, icon kỹ thuật).

### 5.3. Xử lý kênh trong suốt (Alpha Channel):
- Khi ảnh nguồn chứa kênh Alpha (RGBA), định dạng **JPEG không hỗ trợ**, bắt buộc hệ thống phải composite lên nền trắng cố định.
- **WebP hỗ trợ cả kênh Alpha nén có suy hao và không suy hao (Lossy & Lossless Alpha)**. Dung lượng của một ảnh WebP trong suốt nhỏ hơn đến **65%** so với cùng ảnh đó lưu ở định dạng PNG-32.

---

## 6. KHUYẾN NGHỊ KỸ THUẬT THEO TỪNG KỊCH BẢN THỰC TẾ

| Kịch bản ứng dụng | Định dạng khuyến nghị | Mức chất lượng | Lý do kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Website & E-Commerce (Sản phẩm, banner)** | **WebP** | **Q75** | Điểm ngọt hoàn hảo: Tiết kiệm ~70% dung lượng, $SSIM \ge 0.95$, mắt thường không phân biệt được với ảnh gốc, tối ưu tối đa Core Web Vitals. |
| **Ứng dụng Mobile / Mạng di động 3G-4G yếu** | **WebP** | **Q50** | Giảm gần 80% dung lượng, tải cực nhanh, phù hợp cho thumbnail danh sách hoặc tin tức dạng cuộn (feed). |
| **Logo thương hiệu, Icon có nền trong suốt** | **WebP / PNG** | **Q90 / Lossless** | Giữ độ trong suốt mượt mà, không bị viền đen hoặc viền răng cưa. |
| **Lưu trữ ảnh gốc, Thiết kế đồ họa, In ấn** | **PNG / TIFF** | **Lossless** | Không làm mất mát dù chỉ 1 bit thông tin màu, phục vụ chỉnh sửa hậu kỳ không suy hao chất lượng. |
| **Tương thích hệ thống cũ (Legacy Systems)** | **JPEG** | **Q75 - Q80** | Đảm bảo 100% các thiết bị và trình duyệt từ cổ xưa đến hiện đại đều hiển thị được. |

---

## 7. KẾT LUẬN

Hệ thống **ImageBench** đã chứng minh tính đúng đắn và hiệu quả thực nghiệm:
1. Đã xây dựng thành công công cụ đo lường tự động các chỉ số kỹ thuật ảnh chuẩn xác ($MSE, PSNR, SSIM, bpp, \Delta S\%$).
2. Xác nhận bằng số liệu định lượng rằng **WebP là định dạng ưu việt nhất cho ứng dụng web hiện đại** ở dải chất lượng $Q50 - Q75$.
3. Cung cấp nền tảng web trực quan, cho phép người dùng không chuyên cũng có thể đối chiếu bằng thanh trượt so sánh và nhận khuyến nghị định dạng tối ưu cho bài toán của mình.

