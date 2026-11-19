"""
Appcuatao - Ứng dụng phản chiếu và điều khiển màn hình điện thoại Android
Tích hợp trực tiếp màn hình phản chiếu và thanh công cụ tiện ích trong 1 cửa sổ duy nhất.
"""
import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

user32 = ctypes.windll.user32
GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_BORDER = 0x00800000

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

class AppcuataoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Appcuatao")
        self.root.geometry("490x750")
        self.root.minsize(380, 500)
        self.root.configure(bg="#11111b")

        # Đặt icon nếu có
        try:
            self.root.iconbitmap(default="")
        except:
            pass

        self.side = "right"  # "right" hoặc "left"
        self.toolbar_width = 100
        self.scrcpy_proc = None
        self.scrcpy_hwnd = None
        self.is_embedded = False
        self.is_fullscreen = False
        self.current_rotation = 0  # 0: portrait, 1: landscape
        self.phone_w = 1080
        self.phone_h = 2400

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Bắt đầu kết nối scrcpy trong luồng riêng
        threading.Thread(target=self.start_scrcpy, daemon=True).start()

    def setup_ui(self):
        # Frame chính chứa video màn hình điện thoại
        self.video_container = tk.Frame(self.root, bg="#000000")
        self.video_container.bind("<Configure>", self.on_video_resize)

        # Loading label trong khi chờ scrcpy kết nối
        self.lbl_status = tk.Label(self.video_container, text="Đang kết nối điện thoại qua USB...\nVui lòng mở sáng màn hình điện thoại",
                                   font=("Segoe UI", 11), bg="#000000", fg="#89b4fa", justify=tk.CENTER)
        self.lbl_status.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Frame chứa thanh công cụ bên cạnh
        self.toolbar = tk.Frame(self.root, width=self.toolbar_width, bg="#1e1e2e")
        self.toolbar.pack_propagate(False)

        self.build_toolbar()
        self.arrange_layout()

    def arrange_layout(self):
        self.video_container.pack_forget()
        self.toolbar.pack_forget()

        if self.side == "right":
            self.video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.toolbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
            self.video_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def build_toolbar(self):
        # 1. Nút đổi vị trí Trái/Phải
        btn_side = tk.Button(self.toolbar, text="⇄ Đổi bên", command=self.toggle_side,
                             font=("Segoe UI", 9, "bold"), bg="#313244", fg="#89b4fa",
                             activebackground="#45475a", activeforeground="#ffffff",
                             relief=tk.FLAT, bd=0, height=1, cursor="hand2")
        btn_side.pack(pady=(6, 4), padx=4, fill=tk.X)
        ToolTip(btn_side, "Chuyển thanh công cụ sang bên Trái hoặc bên Phải")

        self.add_sep()

        # 2. Nhóm xoay màn hình (Yêu cầu chính của người dùng)
        lbl_rot = tk.Label(self.toolbar, text="XOAY MÀN HÌNH", font=("Segoe UI", 8, "bold"),
                           bg="#1e1e2e", fg="#a6adc8")
        lbl_rot.pack(pady=(2, 1))

        self.btn_rotate_land = self.create_btn("🔄 Xoay ngang", self.cmd_rotate_landscape,
                                              tooltip="Xoay ngang màn hình (xem phim 16:9)",
                                              bg="#181825", fg="#89dceb")
        self.btn_rotate_port = self.create_btn("📱 Xoay dọc", self.cmd_rotate_portrait,
                                              tooltip="Xoay dọc màn hình trở lại bình thường",
                                              bg="#181825", fg="#cba6f7")

        self.add_sep()

        # 3. Nhóm kích cỡ tự do (Kéo dài ngang giữ nguyên cao & ngược lại)
        lbl_size = tk.Label(self.toolbar, text="KÍCH CỠ", font=("Segoe UI", 8, "bold"),
                            bg="#1e1e2e", fg="#a6adc8")
        lbl_size.pack(pady=(2, 1))

        self.create_btn("↔+ Rộng", self.cmd_widen, tooltip="Kéo dài chiều ngang (+60px), giữ nguyên chiều cao", bg="#181825", fg="#a6e3a1")
        self.create_btn("↔- Hẹp", self.cmd_narrow, tooltip="Thu hẹp chiều ngang (-60px), giữ nguyên chiều cao", bg="#181825", fg="#f38ba8")
        self.create_btn("↕+ Cao", self.cmd_heighten, tooltip="Kéo dài chiều cao (+60px), giữ nguyên chiều ngang", bg="#181825", fg="#a6e3a1")
        self.create_btn("↕- Thấp", self.cmd_shorten, tooltip="Thu gọn chiều cao (-60px), giữ nguyên chiều ngang", bg="#181825", fg="#f38ba8")
        self.create_btn("📐 Căn vừa", self.cmd_fit, tooltip="Tự động căn vừa khít, xóa viền đen", bg="#313244", fg="#f9e2af")
        self.create_btn("🔲 Toàn màn", self.cmd_fullscreen, tooltip="Phóng to toàn bộ màn hình laptop (F11)", bg="#313244", fg="#cdd6f4")

        self.add_sep()

        # 4. Nhóm điều hướng
        lbl_nav = tk.Label(self.toolbar, text="ĐIỀU HƯỚNG", font=("Segoe UI", 8, "bold"),
                           bg="#1e1e2e", fg="#a6adc8")
        lbl_nav.pack(pady=(2, 1))

        self.create_btn("🔙 Quay lại", self.cmd_back, tooltip="Nút Back / Quay lại")
        self.create_btn("🏠 Home", self.cmd_home, tooltip="Về màn hình chính")
        self.create_btn("📑 Đa nhiệm", self.cmd_recent, tooltip="Danh sách ứng dụng gần đây")
        self.create_btn("⚡ Tắt màn đt", self.cmd_power, tooltip="Tắt/Bật màn hình điện thoại (tiết kiệm pin)", bg="#181825", fg="#fab387")

    def create_btn(self, text, command, tooltip="", bg="#181825", fg="#cdd6f4"):
        btn = tk.Button(self.toolbar, text=text, command=command,
                        font=("Segoe UI", 9, "normal"),
                        bg=bg, fg=fg, activebackground="#45475a", activeforeground="#ffffff",
                        relief=tk.FLAT, bd=0, height=1, cursor="hand2", anchor="w", padx=6)
        btn.pack(pady=1, padx=4, fill=tk.X)
        if tooltip:
            ToolTip(btn, tooltip)
        return btn

    def add_sep(self):
        sep = tk.Frame(self.toolbar, height=1, bg="#45475a")
        sep.pack(fill=tk.X, padx=4, pady=3)

    def toggle_side(self):
        self.side = "left" if self.side == "right" else "right"
        self.arrange_layout()
        self.root.update_idletasks()
        if self.is_embedded and self.scrcpy_hwnd:
            w = self.video_container.winfo_width()
            h = self.video_container.winfo_height()
            user32.MoveWindow(self.scrcpy_hwnd, 0, 0, w, h, True)

    def on_video_resize(self, event):
        if self.is_embedded and self.scrcpy_hwnd:
            user32.MoveWindow(self.scrcpy_hwnd, 0, 0, event.width, event.height, True)

    def start_scrcpy(self):
        adb_dir = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools"
        env = os.environ.copy()
        env["PATH"] = adb_dir + ";" + env.get("PATH", "")

        unique_title = f"Appcuatao_Stream_{os.getpid()}"
        cmd = [
            "scrcpy",
            f"--window-title={unique_title}",
            "--window-borderless",
            "--no-window-aspect-ratio-lock",
            "--stay-awake",
            "--max-fps=60"
        ]

        self.scrcpy_proc = subprocess.Popen(cmd, env=env, creationflags=0x08000000)

        # Chờ cửa sổ scrcpy xuất hiện để nhúng vào
        for _ in range(100):
            time.sleep(0.1)
            hwnd = user32.FindWindowW(None, unique_title)
            if hwnd:
                self.scrcpy_hwnd = hwnd
                break

        if self.scrcpy_hwnd:
            self.root.after(0, self.embed_scrcpy)
        else:
            self.root.after(0, lambda: self.lbl_status.config(text="Không tìm thấy thiết bị Android.\nVui lòng cắm cáp USB và bật Gỡ lỗi USB.", fg="#f38ba8"))

    def embed_scrcpy(self):
        self.lbl_status.place_forget()
        container_hwnd = self.video_container.winfo_id()

        # Reparent cửa sổ scrcpy thành con của video_container
        user32.SetParent(self.scrcpy_hwnd, container_hwnd)

        style = user32.GetWindowLongW(self.scrcpy_hwnd, GWL_STYLE)
        style &= ~WS_CAPTION
        style &= ~WS_THICKFRAME
        style &= ~WS_BORDER
        style |= WS_CHILD
        user32.SetWindowLongW(self.scrcpy_hwnd, GWL_STYLE, style)

        self.is_embedded = True
        w = max(100, self.video_container.winfo_width())
        h = max(100, self.video_container.winfo_height())
        user32.MoveWindow(self.scrcpy_hwnd, 0, 0, w, h, True)

    def run_adb(self, *args):
        adb_path = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        if not os.path.exists(adb_path):
            adb_path = "adb"
        cmd = [adb_path] + list(args)
        subprocess.Popen(cmd, creationflags=0x08000000)

    # --- Các chức năng xoay màn hình (Yêu cầu chính) ---
    def cmd_rotate_landscape(self):
        """Xoay ngang màn hình (xem phim 16:9)"""
        self.run_adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
        self.run_adb("shell", "settings", "put", "system", "user_rotation", "1")
        # Đồng thời điều chỉnh kích thước cửa sổ mở rộng theo chiều ngang để xem phim sướng mắt
        curr_w = self.root.winfo_width()
        curr_h = self.root.winfo_height()
        if curr_w < curr_h:
            # Đảo kích thước cửa sổ sang ngang
            new_w = max(curr_h, 850)
            new_h = min(curr_w, 550)
            self.root.geometry(f"{new_w}x{new_h}")

    def cmd_rotate_portrait(self):
        """Xoay dọc màn hình trở lại bình thường"""
        self.run_adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
        self.run_adb("shell", "settings", "put", "system", "user_rotation", "0")
        # Đảo kích thước cửa sổ về dọc
        curr_w = self.root.winfo_width()
        curr_h = self.root.winfo_height()
        if curr_w > curr_h:
            new_w = min(curr_h, 490)
            new_h = max(curr_w, 750)
            self.root.geometry(f"{new_w}x{new_h}")

    # --- Các chức năng điều chỉnh kích thước tự do ---
    def cmd_widen(self):
        """Kéo dài chiều ngang (+60px), giữ nguyên chiều cao"""
        curr_w = self.root.winfo_width()
        curr_h = self.root.winfo_height()
        self.root.geometry(f"{curr_w + 60}x{curr_h}")

    def cmd_narrow(self):
        """Thu hẹp chiều ngang (-60px), giữ nguyên chiều cao"""
        curr_w = self.root.winfo_width()
        curr_h = self.root.winfo_height()
        self.root.geometry(f"{max(380, curr_w - 60)}x{curr_h}")

    def cmd_heighten(self):
        """Kéo dài chiều cao (+60px), giữ nguyên chiều ngang"""
        curr_w = self.root.winfo_width()
        curr_h = self.root.winfo_height()
        self.root.geometry(f"{curr_w}x{curr_h + 60}")

    def cmd_shorten(self):
        """Thu gọn chiều cao (-60px), giữ nguyên chiều ngang"""
        curr_w = self.root.winfo_width()
        curr_h = self.root.winfo_height()
        self.root.geometry(f"{curr_w}x{max(400, curr_h - 60)}")

    def cmd_fit(self):
        """Căn vừa khít theo tỉ lệ màn hình điện thoại, xóa viền đen"""
        curr_h = self.root.winfo_height()
        # Tính chiều rộng tối ưu dựa trên tỉ lệ màn hình điện thoại
        target_video_w = int(curr_h * (9 / 20))  # Tỉ lệ điện thoại hiện đại ~20:9
        new_w = target_video_w + self.toolbar_width
        self.root.geometry(f"{new_w}x{curr_h}")

    def cmd_fullscreen(self):
        """Bật/tắt toàn màn hình"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    # --- Điều hướng Android ---
    def cmd_back(self):
        self.run_adb("shell", "input", "keyevent", "4")

    def cmd_home(self):
        self.run_adb("shell", "input", "keyevent", "3")

    def cmd_recent(self):
        self.run_adb("shell", "input", "keyevent", "187")

    def cmd_power(self):
        self.run_adb("shell", "input", "keyevent", "26")

    def on_close(self):
        if self.scrcpy_proc:
            try:
                self.scrcpy_proc.terminate()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppcuataoApp(root)
    root.mainloop()
