"""
Appcuatao Docked Ribbon - Thanh tien ich co dinh gan chat vao cua so phan chieu
Tu dong bam chat 100% vao mep phai cua so dien thoai, dong bo vi tri lien tuc.
"""
import ctypes
from ctypes import wintypes
import os
import shutil
import subprocess
import time
import tkinter as tk

# Set Per-Monitor DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
dwmapi = ctypes.windll.dwmapi

# Win32 Constants
VK_MENU = 0x12       # Alt
VK_W = 0x57          # W
VK_R = 0x52          # R
VK_F11 = 0x7A        # F11
KEYEVENTF_KEYUP = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST = -1
GWLP_HWNDPARENT = -8
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259

class ToolTip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func if callable(text_func) else (lambda: text_func)
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window:
            return
        text = self.text_func()
        if not text:
            return

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)

        label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#181825", foreground="#cdd6f4",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=7, pady=4)
        label.pack()
        tw.update_idletasks()

        tip_w = tw.winfo_reqwidth()
        tip_h = tw.winfo_reqheight()

        wx = self.widget.winfo_rootx()
        wy = self.widget.winfo_rooty()
        ww = self.widget.winfo_width()
        screen_w = self.widget.winfo_screenwidth()

        if wx + ww + tip_w + 10 < screen_w:
            x = wx + ww + 6
        else:
            x = max(10, wx - tip_w - 6)
        y = max(10, wy + (self.widget.winfo_height() - tip_h) // 2)

        tw.geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class AppcuataoDockedBar:
    BAR_TITLE = "__Appcuatao_Docked_Ribbon__"

    def __init__(self, root):
        self.root = root
        self.root.title(self.BAR_TITLE)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#11111b")

        self.bar_width = 44
        self.scrcpy_hwnd = None
        self.scrcpy_pid = None
        self.my_hwnd = None
        self.has_connected = False
        self.wait_count = 0
        self.last_box = None
        self.is_hidden = True
        self.is_landscape = False

        # Biến kéo thả cả cửa sổ bằng grip
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._scrcpy_start_x = 0
        self._scrcpy_start_y = 0
        self._scrcpy_start_w = 0
        self._scrcpy_start_h = 0

        # Ban đầu ẩn hoàn toàn
        self.root.withdraw()

        self.build_ui()
        self.root.update_idletasks()
        self.my_hwnd = self.get_my_hwnd()

        self.check_loop()

    def get_my_hwnd(self):
        try:
            h = user32.FindWindowW(None, self.BAR_TITLE)
            if h:
                return h
        except Exception:
            pass
        top = user32.GetParent(self.root.winfo_id())
        return top if top else self.root.winfo_id()

    def exit_app(self):
        """Đóng hoàn toàn ứng dụng ngay lập tức, không để lại tiến trình ma"""
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

    def close_all(self):
        """Người dùng bấm nút X trên thanh công cụ để thoát cả app"""
        if self.scrcpy_pid:
            subprocess.Popen(["taskkill", "/F", "/PID", str(self.scrcpy_pid)],
                             creationflags=0x08000000)
        else:
            subprocess.Popen(["taskkill", "/F", "/IM", "scrcpy.exe"],
                             creationflags=0x08000000)
        self.exit_app()

    def build_ui(self):
        # 1. Grip kéo di chuyển toàn bộ cụm cửa sổ
        self.grip = tk.Label(self.root, text="⠿", font=("Segoe UI", 11, "bold"),
                             bg="#1e1e2e", fg="#89b4fa", cursor="fleur", height=1)
        self.grip.pack(fill=tk.X, pady=(0, 2))
        self.grip.bind("<Button-1>", self.on_drag_start)
        self.grip.bind("<B1-Motion>", self.on_drag_motion)
        ToolTip(self.grip, "Giữ chuột kéo để di chuyển cả cụm cửa sổ Appcuatao")

        # 2. Xoay màn hình (16:9 xem phim / xoay dọc)
        self.btn_rot = self.create_btn("🔄", self.toggle_rotation,
                                      lambda: "Đang xem ngang -> Bấm để Xoay Dọc" if self.is_landscape else "Bấm để Xoay Ngang xem phim (16:9)",
                                      fg="#89dceb")

        self.add_sep()

        # 3. Chỉnh kích cỡ độc lập (Rộng / Hẹp / Cao / Thấp / Căn vừa / Toàn màn)
        self.create_btn("↔+", self.cmd_widen, "Kéo dài chiều ngang (+50px, giữ nguyên cao)", fg="#a6e3a1")
        self.create_btn("↔-", self.cmd_narrow, "Thu hẹp chiều ngang (-50px, giữ nguyên cao)", fg="#f38ba8")
        self.create_btn("↕+", self.cmd_heighten, "Kéo dài chiều cao (+50px, giữ nguyên ngang)", fg="#a6e3a1")
        self.create_btn("↕-", self.cmd_shorten, "Thu gọn chiều cao (-50px, giữ nguyên ngang)", fg="#f38ba8")
        self.create_btn("📐", self.cmd_fit, "Căn vừa chuẩn tỷ lệ / Xóa viền đen (Alt + W)", fg="#f9e2af")
        self.create_btn("🔲", self.cmd_fullscreen, "Bật/Tắt Toàn màn hình xem phim (F11)", fg="#cba6f7")

        self.add_sep()

        # 4. Phím điều hướng Android
        self.create_btn("🔙", self.cmd_back, "Quay lại (Back / Chuột phải)")
        self.create_btn("🏠", self.cmd_home, "Màn hình chính (Home / Con lăn)")
        self.create_btn("📑", self.cmd_recent, "Đa nhiệm (Recent Apps)")
        self.create_btn("⚡", self.cmd_power, "Tắt/Bật màn hình điện thoại (chống nóng máy)", fg="#fab387")
        self.create_btn("🔊", self.cmd_volup, "Tăng âm lượng", fg="#94e2d5")
        self.create_btn("🔉", self.cmd_voldn, "Giảm âm lượng", fg="#94e2d5")

        self.add_sep()

        # 5. Nút đóng thoát ứng dụng dứt điểm
        self.create_btn("✖", self.close_all, "Đóng hoàn toàn Appcuatao", fg="#f38ba8")

    def create_btn(self, icon, command, tooltip, fg="#cdd6f4"):
        def wrapper():
            command()
            self.restore_focus()

        btn = tk.Button(self.root, text=icon, command=wrapper,
                        font=("Segoe UI Emoji", 10, "bold"),
                        bg="#181825", fg=fg, activebackground="#313244", activeforeground="#ffffff",
                        relief=tk.FLAT, bd=0, padx=2, pady=3, cursor="hand2")
        btn.pack(pady=1, padx=2, fill=tk.X)
        if tooltip:
            ToolTip(btn, tooltip)
        return btn

    def add_sep(self):
        sep = tk.Frame(self.root, height=1, bg="#313244")
        sep.pack(fill=tk.X, padx=4, pady=3)

    def restore_focus(self):
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            user32.SetForegroundWindow(self.scrcpy_hwnd)

    def get_adb_path(self):
        p1 = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        if os.path.exists(p1):
            return p1
        p2 = shutil.which("adb")
        if p2:
            return p2
        return "adb"

    def run_adb(self, *args):
        adb = self.get_adb_path()
        cmd = [adb] + list(args)
        subprocess.Popen(cmd, creationflags=0x08000000)

    def send_scrcpy_hotkey(self, mod_key, key):
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            user32.SetForegroundWindow(self.scrcpy_hwnd)
            time.sleep(0.015)
            if mod_key:
                user32.keybd_event(mod_key, 0, 0, 0)
            user32.keybd_event(key, 0, 0, 0)
            user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)
            if mod_key:
                user32.keybd_event(mod_key, 0, KEYEVENTF_KEYUP, 0)

    def get_process_image_name(self, hwnd):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return "", 0
        h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h_proc:
            return "", pid.value
        buff = ctypes.create_unicode_buffer(512)
        size = wintypes.DWORD(512)
        name = ""
        if kernel32.QueryFullProcessImageNameW(h_proc, 0, buff, ctypes.byref(size)):
            name = os.path.basename(buff.value).lower()
        kernel32.CloseHandle(h_proc)
        return name, pid.value

    def find_target_window(self):
        """Tìm chính xác cửa sổ scrcpy hiển thị màn hình Appcuatao"""
        # 1. Thử FindWindow chính xác
        hwnd = user32.FindWindowW(None, "Appcuatao")
        if hwnd and user32.IsWindowVisible(hwnd):
            proc_name, pid = self.get_process_image_name(hwnd)
            if proc_name == "scrcpy.exe":
                r = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                if r.right - r.left > 100:  # Không phải cửa sổ rỗng
                    return hwnd, pid

        # 2. Quét qua EnumWindows
        candidates = []
        def enum_cb(h, extra):
            if h == self.my_hwnd or not user32.IsWindowVisible(h):
                return True
            proc_name, pid = self.get_process_image_name(h)
            if proc_name == "scrcpy.exe":
                r = wintypes.RECT()
                user32.GetWindowRect(h, ctypes.byref(r))
                w = r.right - r.left
                h_val = r.bottom - r.top
                if w > 100 and h_val > 100:  # Chỉ lấy cửa sổ hiển thị thực sự
                    length = user32.GetWindowTextLengthW(h)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(h, buff, length + 1)
                        title = buff.value
                        if "Appcuatao" in title or title == "scrcpy":
                            candidates.append((h, pid))
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(CMPFUNC(enum_cb), 0)
        return candidates[0] if candidates else (None, None)

    def get_bounds(self, hwnd):
        try:
            r = wintypes.RECT()
            hr = dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r))
            if hr == 0 and (r.right > r.left) and (r.bottom > r.top):
                return r.left, r.top, r.right, r.bottom
        except Exception:
            pass
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        return r.left, r.top, r.right, r.bottom

    def sync_position(self, force=False):
        if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
            return

        if user32.IsIconic(self.scrcpy_hwnd):
            if not self.is_hidden:
                self.root.withdraw()
                self.is_hidden = True
            return
        else:
            if self.is_hidden:
                self.root.deiconify()
                self.is_hidden = False

        left, top, right, bottom = self.get_bounds(self.scrcpy_hwnd)
        h = bottom - top
        if h <= 0 or right <= left:
            return

        curr_box = (left, top, right, bottom)
        if not force and curr_box == self.last_box:
            return
        self.last_box = curr_box

        # Dính chặt vào mép phải cửa sổ scrcpy
        bar_x = right
        bar_y = top
        bar_w = self.bar_width
        bar_h = h

        # Đặt vị trí chính xác bằng geometry của Tkinter
        self.root.geometry(f"{bar_w}x{bar_h}+{bar_x}+{bar_y}")

    def check_loop(self):
        # 1. Kiểm tra tiến trình scrcpy nếu đã từng kết nối
        if self.has_connected:
            # Nếu cửa sổ bị đóng hoặc không còn tồn tại -> THOÁT NGAY LẬP TỨC
            if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
                self.exit_app()
                return

            if self.scrcpy_pid:
                h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, self.scrcpy_pid)
                if not h_proc:
                    self.exit_app()
                    return
                exit_code = wintypes.DWORD()
                kernel32.GetExitCodeProcess(h_proc, ctypes.byref(exit_code))
                kernel32.CloseHandle(h_proc)
                if exit_code.value != STILL_ACTIVE:
                    self.exit_app()
                    return

            self.sync_position()
        else:
            # Chưa kết nối: tìm kiếm scrcpy
            found_hwnd, found_pid = self.find_target_window()
            if found_hwnd:
                self.has_connected = True
                self.scrcpy_hwnd = found_hwnd
                self.scrcpy_pid = found_pid
                try:
                    bar_h = self.my_hwnd or self.root.winfo_id()
                    user32.SetWindowLongPtrW(bar_h, GWLP_HWNDPARENT, found_hwnd)
                except Exception:
                    pass
                self.sync_position(force=True)
            else:
                self.wait_count += 1
                if self.wait_count > 300:  # Quá 15s không thấy scrcpy -> tự hủy
                    self.exit_app()
                    return

        self.root.after(16, self.check_loop)

    # --- Kéo di chuyển toàn bộ cụm cửa sổ ---
    def on_drag_start(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(r))
            self._scrcpy_start_x = r.left
            self._scrcpy_start_y = r.top
            self._scrcpy_start_w = r.right - r.left
            self._scrcpy_start_h = r.bottom - r.top

    def on_drag_motion(self, event):
        if not self.scrcpy_hwnd or not user32.IsWindow(self.scrcpy_hwnd):
            return
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        new_x = self._scrcpy_start_x + dx
        new_y = self._scrcpy_start_y + dy
        user32.SetWindowPos(self.scrcpy_hwnd, 0, new_x, new_y,
                            self._scrcpy_start_w, self._scrcpy_start_h,
                            SWP_NOZORDER | SWP_NOACTIVATE)
        self.sync_position(force=True)

    # --- Xoay ngang màn hình (Mở rộng từ tâm, không lệch vị trí) ---
    def toggle_rotation(self):
        self.is_landscape = not self.is_landscape
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        if self.is_landscape:
            self.run_adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
            self.run_adb("shell", "settings", "put", "system", "user_rotation", "1")

            target_w = min(1200, max(880, int(screen_w * 0.58)))
            target_h = int(target_w * (1080.0 / 2408.0))
        else:
            self.run_adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
            self.run_adb("shell", "settings", "put", "system", "user_rotation", "0")

            target_h = min(960, max(750, int(screen_h * 0.85)))
            target_w = int(target_h * (1080.0 / 2408.0))

        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            left, top, right, bottom = self.get_bounds(self.scrcpy_hwnd)
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2

            new_x = center_x - target_w // 2
            new_y = center_y - target_h // 2

            new_x = max(10, min(new_x, screen_w - target_w - self.bar_width - 15))
            new_y = max(10, min(new_y, screen_h - target_h - 40))

            user32.SetWindowPos(self.scrcpy_hwnd, 0, new_x, new_y, target_w, target_h,
                                SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            self.send_scrcpy_hotkey(VK_MENU, VK_W)
            self.sync_position(force=True)

    # --- Kéo dãn kích cỡ tự do độc lập ---
    def cmd_widen(self):
        """Kéo dài chiều ngang +50px, giữ nguyên chiều cao"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, r.left, r.top, w + 50, h, SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_narrow(self):
        """Thu hẹp chiều ngang -50px, giữ nguyên chiều cao"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, r.left, r.top, max(240, w - 50), h, SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_heighten(self):
        """Kéo dài chiều cao +50px, giữ nguyên chiều ngang"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, r.left, r.top, w, h + 50, SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_shorten(self):
        """Thu gọn chiều cao -50px, giữ nguyên chiều ngang"""
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(self.scrcpy_hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top
            user32.SetWindowPos(self.scrcpy_hwnd, 0, r.left, r.top, w, max(360, h - 50), SWP_NOZORDER | SWP_NOACTIVATE)
            self.sync_position(force=True)

    def cmd_fit(self):
        """Căn vừa chuẩn tỷ lệ không còn viền đen"""
        self.send_scrcpy_hotkey(VK_MENU, VK_W)
        self.root.after(80, lambda: self.sync_position(force=True))

    def cmd_fullscreen(self):
        """F11 Toàn màn hình"""
        self.send_scrcpy_hotkey(None, VK_F11)

    # --- Điều hướng Android ---
    def cmd_back(self):
        self.run_adb("shell", "input", "keyevent", "4")

    def cmd_home(self):
        self.run_adb("shell", "input", "keyevent", "3")

    def cmd_recent(self):
        self.run_adb("shell", "input", "keyevent", "187")

    def cmd_power(self):
        self.run_adb("shell", "input", "keyevent", "26")

    def cmd_volup(self):
        self.run_adb("shell", "input", "keyevent", "24")

    def cmd_voldn(self):
        self.run_adb("shell", "input", "keyevent", "25")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppcuataoDockedBar(root)
    root.mainloop()
