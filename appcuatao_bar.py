"""
Appcuatao Sidebar - Thanh công cụ điều khiển và chỉnh kích cỡ màn hình
"""
import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
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

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 6
        y = self.widget.winfo_rooty()
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#2b2d42", foreground="#edf2f4",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=8, pady=4)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class AppcuataoBar:
    def __init__(self, root):
        self.root = root
        self.root.title("AppcuataoBar")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#181825")
        self.root.overrideredirect(True)

        self.side = "right"  # "right" hoặc "left"
        self.bar_width = 48
        self.scrcpy_hwnd = None
        self.has_connected = False
        self.missing_count = 0
        self.last_rect = None

        # Đặt vị trí mặc định ban đầu ở giữa bên phải màn hình để luôn nhìn thấy
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        init_x = screen_w - self.bar_width - 20
        init_y = max(50, (screen_h - 520) // 2)
        self.root.geometry(f"{self.bar_width}x520+{init_x}+{init_y}")

        self.build_ui()
        self.root.update()
        self.check_window_loop()

    def build_ui(self):
        # Nút đổi vị trí (Trái / Phải)
        self.btn_side = self.create_btn("⇄", self.toggle_side, "Đổi thanh sang bên Trái / Phải", bg="#313244", fg="#89b4fa")
        self.btn_side.pack(pady=(4, 4), padx=3, fill=tk.X)

        sep1 = tk.Frame(self.root, height=1, bg="#45475a")
        sep1.pack(fill=tk.X, padx=4, pady=2)

        # Nhóm điều hướng
        self.create_btn("🔙", self.cmd_back, "Quay lại (Back)").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("🏠", self.cmd_home, "Màn hình chính (Home)").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("📑", self.cmd_recent, "Đa nhiệm (Recent Apps)").pack(pady=1, padx=3, fill=tk.X)

        sep2 = tk.Frame(self.root, height=1, bg="#45475a")
        sep2.pack(fill=tk.X, padx=4, pady=3)

        # Nhóm chỉnh kích thước tự do theo yêu cầu người dùng
        # Giữ nguyên cao, kéo dài rộng; giữ nguyên rộng, kéo dài cao
        self.create_btn("↔+", self.cmd_widen, "Kéo dài CHIỀU NGANG (Giữ nguyên chiều cao)", bg="#1e1e2e", fg="#a6e3a1").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("↔-", self.cmd_narrow, "Thu hẹp CHIỀU NGANG (Giữ nguyên chiều cao)", bg="#1e1e2e", fg="#f38ba8").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("↕+", self.cmd_heighten, "Kéo dài CHIỀU CAO (Giữ nguyên chiều ngang)", bg="#1e1e2e", fg="#a6e3a1").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("↕-", self.cmd_shorten, "Thu gọn CHIỀU CAO (Giữ nguyên chiều ngang)", bg="#1e1e2e", fg="#f38ba8").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("📐", self.cmd_fit, "Căn vừa khít / Xóa sạch viền đen (Alt + W)").pack(pady=1, padx=3, fill=tk.X)

        sep3 = tk.Frame(self.root, height=1, bg="#45475a")
        sep3.pack(fill=tk.X, padx=4, pady=3)

        # Nhóm hiển thị & giải trí
        self.create_btn("🔄", self.cmd_rotate, "Xoay ngang màn hình xem phim (Alt + R)").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("🔲", self.cmd_fullscreen, "Toàn màn hình (F11)").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("🔊", self.cmd_vol_up, "Tăng âm lượng").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("🔉", self.cmd_vol_down, "Giảm âm lượng").pack(pady=1, padx=3, fill=tk.X)
        self.create_btn("⚡", self.cmd_power, "Tắt/Bật màn hình điện thoại").pack(pady=1, padx=3, fill=tk.X)

        sep4 = tk.Frame(self.root, height=1, bg="#45475a")
        sep4.pack(fill=tk.X, padx=4, pady=3)
        self.create_btn("✕", self.root.destroy, "Đóng thanh công cụ", bg="#f38ba8", fg="#11111b").pack(pady=(1, 4), padx=3, fill=tk.X)

    def create_btn(self, icon, command, tooltip, bg="#1e1e2e", fg="#cdd6f4"):
        btn = tk.Button(self.root, text=icon, command=command,
                        font=("Segoe UI", 10, "bold"),
                        bg=bg, fg=fg, activebackground="#585b70", activeforeground="#ffffff",
                        relief=tk.FLAT, bd=0, width=3, height=1, cursor="hand2")
        ToolTip(btn, tooltip)
        return btn

    def toggle_side(self):
        self.side = "left" if self.side == "right" else "right"
        self.sync_position(force=True)

    def find_target_window(self):
        hwnds = []
        def enum_windows_callback(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "Appcuatao" in title or "scrcpy" in title.lower():
                        hwnds.append(hwnd)
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(CMPFUNC(enum_windows_callback), 0)
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

        # Tính vị trí dính vào cạnh cửa sổ điện thoại
        if self.side == "right":
            bar_x = rect.right + 2
        else:
            bar_x = rect.left - self.bar_width - 2

        bar_y = rect.top
        self.root.geometry(f"{self.bar_width}x520+{bar_x}+{bar_y}")

    def check_window_loop(self):
        if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
            found = self.find_target_window()
            if found:
                self.scrcpy_hwnd = found
                self.has_connected = True
                self.missing_count = 0
                self.sync_position(force=True)
            else:
                if self.has_connected:
                    self.missing_count += 1
                    # Chỉ tự đóng sau khi cửa sổ đã từng mở và giờ bị đóng quá 40 ticks (~4 giây)
                    if self.missing_count > 40:
                        self.root.destroy()
                        return
        else:
            self.sync_position()

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

    def cmd_vol_up(self):
        self.run_adb("shell", "input", "keyevent", "24")

    def cmd_vol_down(self):
        self.run_adb("shell", "input", "keyevent", "25")

    def cmd_power(self):
        self.run_adb("shell", "input", "keyevent", "26")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppcuataoBar(root)
    root.mainloop()
