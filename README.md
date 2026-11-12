# Appcuatao — Hướng Dẫn Sử Dụng Chi Tiết

**Appcuatao** là công cụ phản chiếu (mirror) và điều khiển toàn diện màn hình điện thoại Android lên máy tính Windows. 

Ứng dụng phục vụ đa mục đích:
- **Giải trí hàng ngày:** Xem phim, lướt TikTok, xem YouTube, chơi game trên màn hình lớn của laptop/máy tính với âm thanh phát trực tiếp qua loa máy tính.
- **Lập trình viên (Developer):** Thao tác và kiểm thử ứng dụng trực tiếp từ máy tính khi code với VS Code, thay thế hoàn toàn trình giả lập Android Studio nặng nề và ngốn RAM.

---

## 🌟 Điểm Nổi Bật

1. **Zero-Install (Không cài đặt):** 
   - Không cần chạy bộ cài trên Windows (dạng Portable, mở lên là dùng).
   - Không cần cài bất kỳ ứng dụng nào lên điện thoại (không tốn dung lượng bộ nhớ máy).
2. **Siêu nhẹ & Mượt mà:**
   - Tiêu tốn cực ít tài nguyên (chỉ chiếm ~35MB RAM, CPU ~1-2%).
   - Tốc độ khung hình 60 FPS, độ trễ phản hồi siêu thấp (< 25ms, nhanh hơn máy ảo Android Studio).
3. **Thanh công cụ bên cạnh (Sidebar) tiện lợi:**
   - Đầy đủ các nút điều hướng (Back, Home, Đa nhiệm, Xoay ngang, Căn vừa khít, Toàn màn hình...).
   - Hỗ trợ đổi vị trí thanh công cụ sang **bên Trái** hoặc **bên Phải** tùy thói quen.
4. **Truyền tải âm thanh:** Tự động phát tiếng từ điện thoại qua hệ thống loa của laptop/máy tính.

---

## 📱 BƯỚC 1: Chuẩn Bị Trên Điện Thoại (Chỉ làm 1 lần duy nhất)

Để máy tính có thể nhận diện màn hình điện thoại qua cáp USB, bạn cần bật tính năng **Gỡ lỗi USB (USB Debugging)**:

1. **Bật "Tùy chọn nhà phát triển":**
   * Vào **Cài đặt** -> **Thông tin điện thoại** (About phone).
   * Tìm dòng **Số hiệu bản dựng** (Build Number) và chạm liên tục **7 lần** vào dòng này cho đến khi xuất hiện thông báo: *"Bạn đã là nhà phát triển"*.
2. **Bật "Gỡ lỗi USB":**
   * Quay lại **Cài đặt** -> vào **Hệ thống** (hoặc **Cài đặt bổ sung**) -> chọn **Tùy chọn cho nhà phát triển**.
   * Gạt bật công tắc mục **Gỡ lỗi USB** (USB Debugging).
   * *(Lưu ý riêng với điện thoại Xiaomi / Redmi / POCO chạy MIUI hoặc HyperOS):* Bật thêm mục **Gỡ lỗi USB (Cài đặt bảo mật)** để cho phép máy tính click chuột và gõ phím.
3. **Cắm cáp kết nối:**
   * Cắm cáp USB nối điện thoại vào cổng USB của máy tính.
   * Trên màn hình điện thoại sẽ xuất hiện hộp thoại: *"Cho phép gỡ lỗi USB từ máy tính này?"*
   * Bạn hãy **tích chọn vào ô: "Luôn cho phép từ máy tính này"** rồi nhấn **OK / Cho phép**.

---

## 💻 BƯỚC 2: Khởi Chạy Trên Máy Tính

Mỗi khi muốn phản chiếu màn hình điện thoại lên máy tính, bạn chỉ cần:

1. Cắm cáp USB nối điện thoại với máy tính.
2. Mở thư mục dự án và **Click đúp vào file:**
   👉 **`Appcuatao.bat`**
3. Cửa sổ màn hình điện thoại và thanh công cụ điều khiển sẽ tự động xuất hiện ngay lập tức!

---

## 🛠️ BƯỚC 3: Hướng Dẫn Sử Dụng & Thanh Công Cụ

### 1. Thanh Công Cụ Tiện Ích (Sidebar)

Một thanh công cụ màu tối hiện đại sẽ tự động đính kèm ở cạnh cửa sổ điện thoại và di chuyển theo cửa sổ:

| Biểu tượng | Tên chức năng | Chi tiết |
|:---:|:---|:---|
| **⇄** | **Đổi bên** | Nhấn để chuyển thanh công cụ sang **bên Trái** hoặc **bên Phải** |
| **🔙** | **Quay lại (Back)** | Tương đương nút Back trên điện thoại hoặc Click chuột phải |
| **🏠** | **Trang chủ (Home)** | Quay về màn hình chính hoặc Bấm con lăn chuột |
| **📑** | **Đa nhiệm** | Mở danh sách các ứng dụng đang chạy gần đây (Recent Apps) |
| **🔄** | **Xoay màn hình** | Xoay ngang để xem phim 16:9 / Xoay dọc để lướt mạng xã hội |
| **📐** | **Căn vừa khít** | Tự động loại bỏ hoàn toàn viền đen khi kéo co giãn cửa sổ |
| **🔲** | **Toàn màn hình** | Phóng to toàn bộ màn hình laptop để xem phim cực đã (F11) |
| **🔊** | **Tăng âm lượng** | Tăng âm lượng loa điện thoại/máy tính |
| **🔉** | **Giảm âm lượng** | Giảm âm lượng loa điện thoại/máy tính |
| **🔔** | **Thông báo** | Kéo mở thanh thông báo của điện thoại xuống |
| **⚡** | **Tắt/Bật màn hình** | Tắt hoặc bật màn hình điện thoại vật lý |
| **✕** | **Đóng thanh công cụ** | Ẩn thanh công cụ điều khiển |

---

### 2. Kéo Dãn Kích Thước & Tối Ưu Xem Phim

- **Kéo to / nhỏ cửa sổ:** Rê chuột vào 4 góc hoặc các cạnh viền của cửa sổ để kéo ngang/dọc tự do.
- **Xóa viền đen:** Khi kéo cửa sổ bị dư khoảng đen xung quanh:
  - Bấm nút **`📐` (Căn vừa khít)** trên thanh công cụ.
  - Hoặc **Click đúp chuột trực tiếp vào vùng viền đen**.
  - Hoặc bấm tổ hợp phím **`Alt + W`**.
- **Xem phim toàn màn hình:**
  - Bấm nút **`🔲`** trên thanh công cụ hoặc bấm phím **`F11`** (hoặc `Ctrl + F`).
  - Bấm lại `F11` hoặc phím `Esc` để thoát chế độ toàn màn hình.

---

### 3. Bảng Thao Tác Chuột & Phím Tắt Đầy Đủ

| Thao tác | Chức năng tương ứng |
|---|---|
| **Chuột trái** | Chạm (Tap) để mở ứng dụng, chọn link, bấm nút |
| **Giữ & Rê chuột trái** | Vuốt màn hình (Swipe / Drag) để chuyển trang, lướt TikTok/Facebook |
| **Chuột phải** | Nút **Back** (Quay lại) |
| **Bấm con lăn chuột** | Nút **Home** (Về màn hình chính) |
| **Cuộn con lăn chuột** | Cuộn trang lên / xuống mượt mà |
| **Bàn phím máy tính** | Nhập liệu trực tiếp vào ô tìm kiếm hoặc khung chat |
| **`Ctrl + V`** | Dán văn bản vừa copy trên máy tính vào điện thoại |
| **`Ctrl + C`** | Copy văn bản đang chọn trên điện thoại về máy tính |
| **`Ctrl + T`** | Bật/Tắt ghim cửa sổ luôn nổi trên cùng (**Always-on-Top**) |
| **Kéo thả file `.apk`** | Kéo file `.apk` thả vào cửa sổ -> Tự động cài đặt ứng dụng vào điện thoại |

---

## ❓ Câu Hỏi Thường Gặp & Xử Lý Sự Cố

**1. Mở file `Appcuatao.bat` lên báo "CHƯA PHÁT HIỆN ĐIỆN THOẠI"?**
* Kiểm tra lại cáp sạc USB xem đã cắm chắc chắn chưa (nên cắm trực tiếp vào cổng USB máy tính, tránh dùng hub lỏng).
* Mở khóa màn hình điện thoại xem có hiện bảng thông báo hỏi *"Cho phép gỡ lỗi USB từ máy tính này?"* không. Nếu có, hãy bấm **Cho phép**.

**2. Nhìn thấy màn hình nhưng chuột không bấm được (click không ăn)?**
* Thường xảy ra trên máy **Xiaomi / Redmi / POCO**: Bạn cần vào *Tùy chọn nhà phát triển* -> Bật mục **Gỡ lỗi USB (Cài đặt bảo mật)**.

**3. Làm sao để phát âm thanh qua máy tính?**
* Tính năng truyền âm thanh hoạt động tự động trên các thiết bị chạy Android 11 trở lên. Bạn chỉ cần cắm cáp và mở phim, âm thanh sẽ tự động phát ra loa ngoài của máy tính.
