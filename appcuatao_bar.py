"""
Appcuatao Sidebar - Thanh công cụ điều khiển và chỉnh kích cỡ màn hình
"""
import ctypes
from ctypes import wintypes
import os
import subprocess
import time
import tkinter as tk

user32 = ctypes.windll.user32

# Win32 Constants
VK_MENU = 0x12   # Alt
VK_W = 0x57      # W
VK_R = 0x52      # R
VK_F11 = 0x7A    # F11
KEYEVENTF_KEYUP = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010

class AppcuataoBar:
    def __init__(self, root):
        self.root = root
        self.root.title("Tiện ích")
        self.root.attributes("-toolwindow", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self.side = "right"  # "right" hoặc "left"
        self.bar_width = 105
        self.bar_height = 560
        self.scrcpy_hwnd = None
        self.has_connected = False
        self.missing_count = 0
        self.last_rect = None

        # Vị trí mặc định ở cạnh phải màn hình
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        init_x = screen_w - self.bar_width - 30
        init_y = max(40, (screen_h - self.bar_height) // 2)
        self.root.geometry(f"{self.bar_width}x{self.bar_height}+{init_x}+{init_y}")

        self.build_ui()
        self.root.update()
        self.check_window_loop()

    def build_ui(self):
        # Header / Nút đổi bên
        self.btn_side = tk.Button(self.root, text="⇄ Đổi bên", command=self.toggle_side,
                                  font=("Segoe UI", 9, "bold"), bg="#313244", fg="#89b4fa",
                                  activebackground="#45475a", activeforeground="#ffffff",
                                  relief=tk.FLAT, bd=0, height=1, cursor="hand2")
        self.btn_side.pack(pady=(4, 2), padx=4, fill=tk.X)

        sep0 = tk.Frame(self.root, height=1, bg="#45475a")
        sep0.pack(fill=tk.X, padx=4, pady=2)

        # Nhóm chỉnh kích cỡ độc lập (Yêu cầu chính của người dùng)
        lbl_size = tk.Label(self.root, text="KÍCH CỠ", font=("Segoe UI", 8, "bold"),
                            bg="#1e1e2e", fg="#a6adc8")
        lbl_size.pack(pady=(1, 1))

        self.create_btn("↔+ Rộng", self.cmd_widen, bg="#181825", fg="#a6e3a1")
        self.create_btn("↔- Hẹp", self.cmd_narrow, bg="#181825", fg="#f38ba8")
        self.create_btn("↕+ Cao", self.cmd_heighten, bg="#181825", fg="#a6e3a1")
        self.create_btn("↕- Thấp", self.cmd_shorten, bg="#181825", fg="#f38ba8")
        self.create_btn("📐 Căn vừa", self.cmd_fit, bg="#313244", fg="#f9e2af")

        sep1 = tk.Frame(self.root, height=1, bg="#45475a")
        sep1.pack(fill=tk.X, padx=4, pady=3)

        # Nhóm hiển thị & giải trí
        lbl_view = tk.Label(self.root, text="XEM PHIM", font=("Segoe UI", 8, "bold"),
                            bg="#1e1e2e", fg="#a6adc8")
        lbl_view.pack(pady=(1, 1))

        self.create_btn("🔄 Xoay", self.cmd_rotate, bg="#181825", fg="#89dceb")
        self.create_btn("🔲 Toàn màn", self.cmd_fullscreen, bg="#181825", fg="#cba6f7")

        sep2 = tk.Frame(self.root, height=1, bg="#45475a")
        sep2.pack(fill=tk.X, padx=4, pady=3)

        # Nhóm điều hướng
        lbl_nav = tk.Label(self.root, text="ĐIỀU HƯỚNG", font=("Segoe UI", 8, "bold"),
                           bg="#1e1e2e", fg="#a6adc8")
        lbl_nav.pack(pady=(1, 1))

        self.create_btn("🔙 Quay lại", self.cmd_back)
        self.create_btn("🏠 Home", self.cmd_home)
        self.create_btn("📑 Đa nhiệm", self.cmd_recent)
        self.create_btn("⚡ Tắt màn đt", self.cmd_power, bg="#181825", fg="#fab387")

    def create_btn(self, text, command, bg="#181825", fg="#cdd6f4"):
        btn = tk.Button(self.root, text=text, command=command,
                        font=("Segoe UI", 9, "normal"),
                        bg=bg, fg=fg, activebackground="#45475a", activeforeground="#ffffff",
                        relief=tk.FLAT, bd=0, height=1, cursor="hand2", anchor="w", padx=8)
        btn.pack(pady=1, padx=4, fill=tk.X)
        return btn

    def toggle_side(self):
        self.side = "left" if self.side == "right" else "right"
        self.sync_position(force=True)

    def find_target_window(self):
        # 1. Thử tìm chính xác theo tiêu đề
        hwnd = user32.FindWindowW(None, "Appcuatao")
        if hwnd and user32.IsWindowVisible(hwnd):
            return hwnd

        # 2. Quét các cửa sổ chứa chữ Appcuatao hoặc scrcpy
        hwnds = []
        def enum_cb(h, extra):
            if user32.IsWindowVisible(h):
                length = user32.GetWindowTextLengthW(h)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(h, buff, length + 1)
                    title = buff.value
                    if "Appcuatao" in title or "scrcpy" in title.lower():
                        hwnds.append(h)
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(CMPFUNC(enum_cb), 0)
        return hwnds[0] if hwnds else None

    def sync_position(self, force=False):
        if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
            return

        rect = wintypes.RECT()
        if not user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(rect)):
            return

        current_rect = (rect.left, rect.top, rect.right, rect.bottom)
        if not force and current_rect == self.last_rect:
            return

        self.last_rect = current_rect

        if user32.IsIconic(self.scrcpy_hwnd):
            self.root.withdraw()
            return
        else:
            self.root.deiconify()

        # Đặt thanh công cụ dính ngay sát mép cửa sổ phản chiếu
        if self.side == "right":
            bar_x = rect.right + 4
        else:
            bar_x = rect.left - self.bar_width - 8

        bar_y = rect.top
        self.root.geometry(f"{self.bar_width}x{self.bar_height}+{bar_x}+{bar_y}")

    def check_window_loop(self):
        found = self.find_target_window()
        if found:
            self.scrcpy_hwnd = found
            self.has_connected = True
            self.missing_count = 0
            self.sync_position()
        else:
            if self.has_connected:
                self.missing_count += 1
                # Nếu cửa sổ mirror đã đóng quá 5 giây thì đóng thanh công cụ
                if self.missing_count > 50:
                    self.root.destroy()
                    return

        self.root.after(100, self.check_window_loop)

    def run_adb(self, *args):
        adb_path = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        if not os.path.exists(adb_path):
            adb_path = "adb"
        cmd = [adb_path] + list(args)
        subprocess.Popen(cmd, creationflags=0x08000000)

    def send_scrcpy_hotkey(self, mod_key, key):
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            user32.SetForegroundWindow(self.scrcpy_hwnd)
            time.sleep(0.04)
            if mod_key:
                user32.keybd_event(mod_key, 0, 0, 0)
            user32.keybd_event(key, 0, 0, 0)
            user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)
            if mod_key:
                user32.keybd_event(mod_key, 0, KEYEVENTF_KEYUP, 0)

    # --- Điều chỉnh kích thước cửa sổ độc lập theo yêu cầu ---
    def cmd_widen(self):
        """Kéo dài chiều ngang +60px, giữ nguyên chiều cao"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            rect = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, rect.left, rect.top, w + 60, h, SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_narrow(self):
        """Thu hẹp chiều ngang -60px, giữ nguyên chiều cao"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            rect = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, rect.left, rect.top, max(200, w - 60), h, SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_heighten(self):
        """Kéo dài chiều cao +60px, giữ nguyên chiều ngang"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            rect = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, rect.left, rect.top, w, h + 60, SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_shorten(self):
        """Thu gọn chiều cao -60px, giữ nguyên chiều ngang"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            rect = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, rect.left, rect.top, w, max(300, h - 60), SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_fit(self):
        # Alt + W: Căn vừa khít, xóa viền đen
        self.send_scrcpy_hotkey(VK_MENU, VK_W)

    def cmd_rotate(self):
        # Alt + R: Xoay ngang / dọc màn hình
        self.send_scrcpy_hotkey(VK_MENU, VK_R)

    def cmd_fullscreen(self):
        # F11: Toàn màn hình
        self.send_scrcpy_hotkey(None, VK_F11)

    # --- Điều hướng & Tiện ích ---
    def cmd_back(self):
        self.run_adb("shell", "input", "keyevent", "4")

    def cmd_home(self):
        self.run_adb("shell", "input", "keyevent", "3")

    def cmd_recent(self):
        self.run_adb("shell", "input", "keyevent", "187")

    def cmd_power(self):
        self.run_adb("shell", "input", "keyevent", "26")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppcuataoBar(root)
    root.mainloop()
