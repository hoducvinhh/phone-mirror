"""
Appcuatao - Giao diện hợp nhất liền khối: Màn hình điện thoại tràn viền + Thanh công cụ siêu mỏng
"""
import ctypes
from ctypes import wintypes
import os
import subprocess
import time
import threading
import tkinter as tk

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
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 4
        y = self.widget.winfo_rooty() + 2
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#2b2d42", foreground="#edf2f4",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=6, pady=3)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class AppcuataoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Appcuatao")
        self.root.configure(bg="#11111b")

        self.toolbar_width = 38
        self.side = "right"  # "right" hoặc "left"
        self.is_landscape = False
        self.is_fullscreen = False
        self.scrcpy_proc = None
        self.scrcpy_hwnd = None
        self.is_embedded = False

        # Tỉ lệ điện thoại chuẩn (Samsung A13: 1088x2416 ~ 0.45)
        init_h = 720
        init_w = int(init_h * (1088 / 2416)) + self.toolbar_width
        self.root.geometry(f"{init_w}x{init_h}")
        self.root.minsize(280, 420)

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.start_scrcpy, daemon=True).start()

    def setup_ui(self):
        # Frame chứa màn hình điện thoại (tràn viền, không khoảng đen thừa)
        self.video_container = tk.Frame(self.root, bg="#000000")
        self.video_container.bind("<Configure>", self.on_video_resize)

        self.lbl_status = tk.Label(self.video_container, text="Đang kết nối điện thoại...",
                                   font=("Segoe UI", 10), bg="#000000", fg="#89b4fa")
        self.lbl_status.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Thanh công cụ siêu mỏng liền khối kiểu giả lập
        self.toolbar = tk.Frame(self.root, width=self.toolbar_width, bg="#181825")
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
        # 1. Nút đổi bên
        self.create_btn("⇄", self.toggle_side, "Đổi thanh công cụ sang bên Trái / Phải", fg="#89b4fa")

        self.add_sep()

        # 2. Xoay màn hình (Xem phim / Đọc báo)
        self.btn_rot = self.create_btn("🔄", self.toggle_rotation, "Xoay ngang màn hình (xem phim) / Xoay dọc", fg="#89dceb")

        # 3. Kích cỡ & Căn vừa
        self.create_btn("📐", self.cmd_fit, "Căn vừa khít tỉ lệ chuẩn điện thoại", fg="#f9e2af")
        self.create_btn("↔+", self.cmd_widen, "Kéo dài chiều ngang (+40px)", fg="#a6e3a1")
        self.create_btn("↔-", self.cmd_narrow, "Thu hẹp chiều ngang (-40px)", fg="#f38ba8")
        self.create_btn("↕+", self.cmd_heighten, "Kéo dài chiều cao (+40px)", fg="#a6e3a1")
        self.create_btn("↕-", self.cmd_shorten, "Thu gọn chiều cao (-40px)", fg="#f38ba8")
        self.create_btn("🔲", self.cmd_fullscreen, "Phóng to toàn màn hình (F11)", fg="#cba6f7")

        self.add_sep()

        # 4. Điều hướng Android
        self.create_btn("🔙", self.cmd_back, "Quay lại (Back / Chuột phải)")
        self.create_btn("🏠", self.cmd_home, "Trang chủ (Home / Bấm con lăn)")
        self.create_btn("📑", self.cmd_recent, "Đa nhiệm (Recent Apps)")
        self.create_btn("⚡", self.cmd_power, "Tắt/Bật màn hình điện thoại (chống nóng máy)", fg="#fab387")

    def create_btn(self, icon, command, tooltip="", fg="#cdd6f4"):
        btn = tk.Button(self.toolbar, text=icon, command=command,
                        font=("Segoe UI Emoji", 11, "bold"),
                        bg="#181825", fg=fg, activebackground="#313244", activeforeground="#ffffff",
                        relief=tk.FLAT, bd=0, width=3, height=1, cursor="hand2")
        btn.pack(pady=2, padx=1, fill=tk.X)
        if tooltip:
            ToolTip(btn, tooltip)
        return btn

    def add_sep(self):
        sep = tk.Frame(self.toolbar, height=1, bg="#313244")
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
            "--render-fit=stretched",
            "--no-window-aspect-ratio-lock",
            "--stay-awake",
            "--max-fps=60"
        ]

        self.scrcpy_proc = subprocess.Popen(cmd, env=env, creationflags=0x08000000)

        for _ in range(100):
            time.sleep(0.1)
            hwnd = user32.FindWindowW(None, unique_title)
            if hwnd:
                self.scrcpy_hwnd = hwnd
                break

        if self.scrcpy_hwnd:
            self.root.after(0, self.embed_scrcpy)
        else:
            self.root.after(0, lambda: self.lbl_status.config(text="Không thể kết nối.\nVui lòng cắm lại cáp USB.", fg="#f38ba8"))

    def embed_scrcpy(self):
        self.lbl_status.place_forget()
        container_hwnd = self.video_container.winfo_id()

        user32.SetParent(self.scrcpy_hwnd, container_hwnd)

        style = user32.GetWindowLongW(self.scrcpy_hwnd, GWL_STYLE)
        style &= ~WS_CAPTION
        style &= ~WS_THICKFRAME
        style &= ~WS_BORDER
        style |= WS_CHILD
        user32.SetWindowLongW(self.scrcpy_hwnd, GWL_STYLE, style)

        self.is_embedded = True
        w = max(50, self.video_container.winfo_width())
        h = max(50, self.video_container.winfo_height())
        user32.MoveWindow(self.scrcpy_hwnd, 0, 0, w, h, True)

    def run_adb(self, *args):
        adb_path = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        if not os.path.exists(adb_path):
            adb_path = "adb"
        cmd = [adb_path] + list(args)
        subprocess.Popen(cmd, creationflags=0x08000000)

    # --- Xoay màn hình ---
    def toggle_rotation(self):
        self.is_landscape = not self.is_landscape
        if self.is_landscape:
            # Xoay ngang điện thoại và mở rộng cửa sổ
            self.run_adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
            self.run_adb("shell", "settings", "put", "system", "user_rotation", "1")
            h = 480
            w = int(h * (2416 / 1088)) + self.toolbar_width
            self.root.geometry(f"{w}x{h}")
        else:
            # Xoay dọc lại bình thường
            self.run_adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
            self.run_adb("shell", "settings", "put", "system", "user_rotation", "0")
            h = 720
            w = int(h * (1088 / 2416)) + self.toolbar_width
            self.root.geometry(f"{w}x{h}")

    # --- Kích cỡ tự do ---
    def cmd_widen(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.root.geometry(f"{w + 40}x{h}")

    def cmd_narrow(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.root.geometry(f"{max(280, w - 40)}x{h}")

    def cmd_heighten(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.root.geometry(f"{w}x{h + 40}")

    def cmd_shorten(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.root.geometry(f"{w}x{max(380, h - 40)}")

    def cmd_fit(self):
        h = self.root.winfo_height()
        ratio = (2416 / 1088) if self.is_landscape else (1088 / 2416)
        w = int(h * ratio) + self.toolbar_width
        self.root.geometry(f"{w}x{h}")

    def cmd_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    # --- Điều hướng ---
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
