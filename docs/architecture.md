# Architecture — Appcuatao

Ứng dụng gồm 2 thành phần chính:

1. **Android Server (`mirror-server.jar`):**
   - Được desktop app đẩy qua ADB vào `/data/local/tmp/mirror-server.jar` và chạy ngầm bằng `app_process` với quyền `shell` (UID 2000).
   - Tự động tạo VirtualDisplay thông qua API ẩn `SurfaceControl.createDisplay`, truyền trực tiếp vào `MediaCodec` để encode H.264 phần cứng ở chế độ độ trễ cực thấp (`low-latency`).
   - Lắng nghe kết nối qua UNIX domain socket (`LocalServerSocket("nativemirror")`).
   - Nhận các gói tin điều khiển từ desktop và gọi trực tiếp `InputManager.injectInputEvent` để mô phỏng sự kiện cảm ứng (Touch Down, Move, Up), phím bấm hệ thống (Back, Home, App Switcher, Power, Volume) và gõ văn bản.

2. **Windows Client Desktop App (`Appcuatao.exe`):**
   - Tự động quản lý thiết bị cắm vào qua ADB (`adb forward tcp:27183 localabstract:nativemirror`).
   - Kết nối vào socket và nhận các frame H.264 NAL units (đóng gói bằng header 8 byte `NMR2`).
   - Giải mã phần cứng bằng FFmpeg (`avcodec` + `swscale`).
   - Hiển thị trực tiếp lên cửa sổ SDL2 được tăng tốc phần cứng.
   - Bắt các sự kiện chuột (click, drag, right-click back, middle-click home, cuộn chuột) và bàn phím máy tính để gửi ngược lại cho server.
   - Hỗ trợ Always-on-Top (`Ctrl + T`) để ghim cửa sổ cạnh VS Code, kéo thả file `.apk` vào cửa sổ để tự động cài đặt.
