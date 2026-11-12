"""
Appcuatao Sidebar - Thanh công cụ điều khiển tiện ích đính kèm cửa sổ phản chiếu
"""
import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

user32 = ctypes.windll.user32

# Win32 Constants
VK_MENU = 0x12   # Alt
VK_W = 0x57      # W
VK_R = 0x52      # R
VK_F11 = 0x7A    # F11
KEYEVENTF_KEYUP = 0x0002

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
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 45
        y = y + self.widget.winfo_rooty() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#2b2d42", foreground="#edf2f4",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=6, pady=3)
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class AppcuataoBar:
    def __init__(self, root):
        self.root = root
        self.root.title("Bar")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#181825")

        self.side = "right"  # "right" hoặc "left"
        self.bar_width = 46
        self.scrcpy_hwnd = None
        self.last_rect = None
        self.missing_count = 0

        self.build_ui()
        self.check_window_loop()

    def build_ui(self):
        # Nút đổi vị trí (Trái / Phải)
        self.btn_side = self.create_btn("⇄", self.toggle_side, "Đổi sang bên Trái/Phải", bg="#313244", fg="#cdd6f4")
        self.btn_side.pack(pady=(4, 6), padx=4, fill=tk.X)

        # Separator
        sep1 = tk.Frame(self.root, height=1, bg="#45475a")
        sep1.pack(fill=tk.X, padx=6, pady=2)

        # Các nút điều hướng cơ bản
        self.create_btn("🔙", self.cmd_back, "Quay lại (Back / Chuột phải)").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("🏠", self.cmd_home, "Màn hình chính (Home)").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("📑", self.cmd_recent, "Đa nhiệm (Recent Apps)").pack(pady=2, padx=4, fill=tk.X)

        # Separator
        sep2 = tk.Frame(self.root, height=1, bg="#45475a")
        sep2.pack(fill=tk.X, padx=6, pady=4)

        # Nút kích thước & Màn hình
        self.create_btn("🔄", self.cmd_rotate, "Xoay ngang / dọc màn hình (Alt + R)").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("📐", self.cmd_fit, "Căn vừa khít / Xóa viền đen (Alt + W)").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("🔲", self.cmd_fullscreen, "Toàn màn hình xem phim (F11)").pack(pady=2, padx=4, fill=tk.X)

        # Separator
        sep3 = tk.Frame(self.root, height=1, bg="#45475a")
        sep3.pack(fill=tk.X, padx=6, pady=4)

        # Nút tiện ích âm thanh & nguồn
        self.create_btn("🔊", self.cmd_vol_up, "Tăng âm lượng").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("🔉", self.cmd_vol_down, "Giảm âm lượng").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("🔔", self.cmd_notif, "Mở thanh thông báo").pack(pady=2, padx=4, fill=tk.X)
        self.create_btn("⚡", self.cmd_power, "Tắt/Bật màn hình điện thoại").pack(pady=2, padx=4, fill=tk.X)

        # Nút đóng
        sep4 = tk.Frame(self.root, height=1, bg="#45475a")
        sep4.pack(fill=tk.X, padx=6, pady=4)
        self.create_btn("✕", self.root.destroy, "Đóng thanh công cụ", bg="#f38ba8", fg="#11111b").pack(pady=(2, 6), padx=4, fill=tk.X)

    def create_btn(self, icon, command, tooltip, bg="#1e1e2e", fg="#cdd6f4"):
        btn = tk.Button(self.root, text=icon, command=command,
                        font=("Segoe UI Emoji", 12, "bold"),
                        bg=bg, fg=fg, activebackground="#585b70", activeforeground="#ffffff",
                        relief=tk.FLAT, bd=0, width=3, height=1, cursor="hand2")
        ToolTip(btn, tooltip)
        return btn

    def toggle_side(self):
        self.side = "left" if self.side == "right" else "right"
        self.sync_position(force=True)

    def find_target_window(self):
        def enum_windows_callback(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "Appcuatao" in title or "scrcpy" in title.lower():
                        extra.append(hwnd)
            return True

        hwnds = []
        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.POINTER(ctypes.c_void_p))
        user32.EnumWindows(CMPFUNC(enum_windows_callback), ctypes.byref(ctypes.c_void_p(0)))
        return hwnds[0] if hwnds else None

    def sync_position(self, force=False):
        if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
            self.scrcpy_hwnd = self.find_target_window()
            if not self.scrcpy_hwnd:
                return

        rect = wintypes.RECT()
        if not user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(rect)):
            return

        current_rect = (rect.left, rect.top, rect.right, rect.bottom)
        if not force and current_rect == self.last_rect:
            return

        self.last_rect = current_rect
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        # Nếu cửa sổ bị minimize (thu nhỏ xuống taskbar)
        if user32.IsIconic(self.scrcpy_hwnd):
            self.root.withdraw()
            return
        else:
            self.root.deiconify()

        # Tính toán tọa độ đặt thanh công cụ
        if self.side == "right":
            bar_x = rect.right + 2
        else:
            bar_x = rect.left - self.bar_width - 2

        bar_y = rect.top
        self.root.geometry(f"{self.bar_width}x420+{bar_x}+{bar_y}")

    def check_window_loop(self):
        if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
            found = self.find_target_window()
            if found:
                self.scrcpy_hwnd = found
                self.missing_count = 0
                self.sync_position(force=True)
            else:
                self.missing_count += 1
                # Nếu đã từng tìm thấy cửa sổ và giờ bị đóng quá 20 ticks (~2 giây) thì tự đóng toolbar
                if self.missing_count > 25:
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
            time.sleep(0.05)
            if mod_key:
                user32.keybd_event(mod_key, 0, 0, 0)
            user32.keybd_event(key, 0, 0, 0)
            user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)
            if mod_key:
                user32.keybd_event(mod_key, 0, KEYEVENTF_KEYUP, 0)

    # Các hành động
    def cmd_back(self):
        self.run_adb("shell", "input", "keyevent", "4")

    def cmd_home(self):
        self.run_adb("shell", "input", "keyevent", "3")

    def cmd_recent(self):
        self.run_adb("shell", "input", "keyevent", "187")

    def cmd_rotate(self):
        # Gửi Alt + R tới scrcpy
        self.send_scrcpy_hotkey(VK_MENU, VK_R)

    def cmd_fit(self):
        # Gửi Alt + W tới scrcpy (xóa viền đen, căn vừa khít)
        self.send_scrcpy_hotkey(VK_MENU, VK_W)

    def cmd_fullscreen(self):
        # Gửi F11 tới scrcpy
        self.send_scrcpy_hotkey(None, VK_F11)

    def cmd_vol_up(self):
        self.run_adb("shell", "input", "keyevent", "24")

    def cmd_vol_down(self):
        self.run_adb("shell", "input", "keyevent", "25")

    def cmd_power(self):
        self.run_adb("shell", "input", "keyevent", "26")

    def cmd_notif(self):
        self.run_adb("shell", "cmd", "statusbar", "expand-notifications")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppcuataoBar(root)
    root.mainloop()
