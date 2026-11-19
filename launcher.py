"""
Appcuatao Smart Launcher
Tu dong nhan dien 2 che do:
1. Uu tien tuyet doi CAP USB de dat do muot ma toi da (60 FPS, khong do tre).
2. Neu khong thay cap USB -> Tu dong tim kiem va ket noi khong day qua WI-FI.
"""
import os
import re
import shutil
import subprocess
import sys
import time

def get_adb_path():
    p1 = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
    if os.path.exists(p1):
        return p1
    p2 = shutil.which("adb")
    if p2:
        return p2
    return "adb"

def run_adb(*args):
    adb = get_adb_path()
    cmd = [adb] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    return res.stdout.strip()

def cleanup_stale_devices():
    """Don dep cac thiet bi offline tren ADB de tranh loi scrcpy bi trung lap"""
    out = run_adb("devices")
    for line in out.splitlines()[1:]:
        line = line.strip()
        if "offline" in line and ":" in line:
            ip_port = line.split()[0]
            run_adb("disconnect", ip_port)

def get_devices():
    out = run_adb("devices")
    usb_devs = []
    wifi_devs = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serial = parts[0]
            if ":" in serial:
                wifi_devs.append(serial)
            else:
                usb_devs.append(serial)
    return usb_devs, wifi_devs

def save_wifi_ip(ip):
    try:
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cur_dir, ".last_wifi_ip.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(ip.strip())
    except Exception:
        pass

def load_saved_wifi_ip():
    try:
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cur_dir, ".last_wifi_ip.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                ip = f.read().strip()
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                    return ip
    except Exception:
        pass
    return None

def query_phone_wifi_ip(serial):
    out = run_adb("-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0")
    m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out)
    if m:
        return m.group(1)
    out2 = run_adb("-s", serial, "shell", "ip", "route")
    for line in out2.splitlines():
        if "wlan0" in line and "src" in line:
            parts = line.split()
            if "src" in parts:
                idx = parts.index("src")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    return None

def main():
    print("=" * 60)
    print("   APPCUATAO - SMART AUTO CONNECTION")
    print("=" * 60)

    # Dọn dẹp các IP offline cũ nếu có
    cleanup_stale_devices()

    usb_devs, wifi_devs = get_devices()
    target_serial = None
    mode = None

    # --- KỊCH BẢN 1: CÓ CÁP USB -> ƯU TIÊN SỐ 1 ---
    if usb_devs:
        target_serial = usb_devs[0]
        mode = "USB"
        print(f"\n[+] PHAT HIEN CAP USB: {target_serial}")
        print("    -> UU TIEN PHAN CHIEU QUA USB (60 FPS, khong do tre)!\n")

        # Lưu IP Wi-Fi ngầm để lần sau rút cáp vẫn nhớ
        try:
            phone_ip = query_phone_wifi_ip(target_serial)
            if phone_ip:
                save_wifi_ip(phone_ip)
        except Exception:
            pass

    # --- KỊCH BẢN 2: KHÔNG CÓ CÁP USB -> TỰ ĐỘNG DÙNG WI-FI ---
    else:
        print("\n[*] Khong thay cap USB. Dang chuyen sang che do WI-FI...")

        # 2a. Nếu đã có thiết bị Wi-Fi đang kết nối sẵn
        if wifi_devs:
            target_serial = wifi_devs[0]
            mode = "WI-FI"
            print(f"[v] Da ket noi qua Wi-Fi: {target_serial}\n")
        else:
            # 2b. Thử kết nối vào IP đã lưu
            saved_ip = load_saved_wifi_ip()
            if saved_ip:
                print(f"[*] Dang ket noi toi IP Wi-Fi da nho: {saved_ip}:5555...")
                res = run_adb("connect", f"{saved_ip}:5555")
                print(res)
                time.sleep(0.5)
                _, wifi_devs_after = get_devices()
                if wifi_devs_after:
                    target_serial = wifi_devs_after[0]
                    mode = "WI-FI"
                    print(f"[v] Ket noi Wi-Fi thanh cong toi {target_serial}!\n")

    # --- KỊCH BẢN 3: CHƯA THẤY CẢ HAI -> HƯỚNG DẪN HOẶC NHẬP IP ---
    if not target_serial:
        print("\n" + "=" * 60)
        print(" [!] CHUA THE KET NOI DEN DIEN THOAI")
        print("=" * 60)
        print(" Huong dan:")
        print("   1. Cam cap USB vao may tinh de xem sieu muot, HOAC:")
        print("   2. Nhap dia chi IP Wi-Fi cua dien thoai ben duoi (Xem trong")
        print("      Cai dat -> Wi-Fi tren dien thoai, vi du: 192.168.1.241)")
        print("=" * 60)
        user_ip = input("\nNhap IP Wi-Fi dien thoai (Enter de thoat): ").strip()
        if user_ip and re.match(r"^\d+\.\d+\.\d+\.\d+$", user_ip):
            print(f"[*] Dang ket noi toi {user_ip}:5555...")
            res = run_adb("connect", f"{user_ip}:5555")
            print(res)
            time.sleep(1)
            cleanup_stale_devices()
            _, wifi_devs_manual = get_devices()
            for dev in wifi_devs_manual:
                if user_ip in dev:
                    target_serial = dev
                    break
            if not target_serial and wifi_devs_manual:
                target_serial = wifi_devs_manual[0]

            if target_serial:
                mode = "WI-FI"
                save_wifi_ip(user_ip)
                print(f"[v] Ket noi thanh cong toi {target_serial}!\n")
            else:
                print("[!] Khong the ket noi toi IP nay. Vui long kiem tra lai.")
                input("Nhan Enter de thoat...")
                return 1
        else:
            return 1

    # --- KHỞI ĐỘNG CÁC THÀNH PHẦN ---
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    bar_script = os.path.join(cur_dir, "appcuatao_bar.py")

    # 1. Bật thanh công cụ tiện ích chạy ngầm (pythonw)
    py_exe = sys.executable
    pyw_exe = os.path.join(os.path.dirname(py_exe), "pythonw.exe")
    if not os.path.exists(pyw_exe):
        pyw_exe = "pythonw"

    print("[*] Dang khoi dong thanh tien ich Appcuatao...")
    subprocess.Popen([pyw_exe, bar_script])

    # 2. Khởi động scrcpy với đích đến chính xác
    scrcpy_exe = shutil.which("scrcpy")
    if not scrcpy_exe:
        scrcpy_exe = r"C:\Users\Admin\scoop\shims\scrcpy.exe"
        if not os.path.exists(scrcpy_exe):
            scrcpy_exe = "scrcpy"

    scrcpy_args = [
        scrcpy_exe,
        "-s", target_serial,  # CHỈ ĐỊNH RÕ THIẾT BỊ NÀY, KHÔNG BAO GIỜ BỊ NHẦM LẪN
        "--window-title", "Appcuatao",
        "--video-codec=h265",
        "--video-bit-rate=24M",
        "--max-size=1920",
        "--video-buffer=0",
        "--audio-buffer=20",
        "--max-fps=60",
        "--window-x", "160",
        "--window-y", "60",
        "--no-window-aspect-ratio-lock",
        "--stay-awake"
    ]

    print(f"[*] Dang phan chieu man hinh ({mode}: {target_serial})...")
    scrcpy_proc = subprocess.run(scrcpy_args)

    # 3. Dọn dẹp sau khi scrcpy đóng
    print("[*] Ung dung da dong. Dang don dep tien trinh...")
    subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq __Appcuatao_Docked_Ribbon__"],
                   capture_output=True)

    if scrcpy_proc.returncode != 0:
        print(f"\n[!] Ung dung ket thuc voi ma loi: {scrcpy_proc.returncode}")
        input("Nhan Enter de thoat...")

    return scrcpy_proc.returncode

if __name__ == "__main__":
    sys.exit(main())
