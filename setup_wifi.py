"""
Longtoitannatnhanratoilagay - Script tự động kích hoạt kết nối Wi-Fi (Không dây)
Tự động dò IP wlan0, mở cổng 5555, kết nối và lưu cấu hình.
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

def run_cmd(*args):
    adb = get_adb_path()
    cmd = [adb] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    return res.stdout.strip()

def get_phone_ip():
    # Cách 1: ip -f inet addr show wlan0
    out = run_cmd("shell", "ip", "-f", "inet", "addr", "show", "wlan0")
    m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out)
    if m:
        return m.group(1)

    # Cách 2: ip route
    out2 = run_cmd("shell", "ip", "route")
    for line in out2.splitlines():
        if "wlan0" in line and "src" in line:
            parts = line.split()
            if "src" in parts:
                idx = parts.index("src")
                if idx + 1 < len(parts):
                    return parts[idx + 1]

    # Cách 3: getprop dhcp.wlan0.ipaddress
    out3 = run_cmd("shell", "getprop", "dhcp.wlan0.ipaddress")
    if out3 and re.match(r"^\d+\.\d+\.\d+\.\d+$", out3):
        return out3

    return None

def main():
    print("=" * 60)
    print("   LONGTOITANNATNHANRATOILAGAY - KET NOI KHONG DAY QUA WI-FI")
    print("=" * 60)
    print()

    # 1. Kiem tra xem co thiet bi nao cam USB khong
    out_devices = run_cmd("devices")
    devices = []
    for line in out_devices.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])

    ip_saved_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_wifi_ip.txt")

    if not devices:
        print("[!] CHUA PHAT HIEN DIEN THOAI NAO QUA CAP USB.")
        print()
        # Kiem tra xem da tung luu IP chua
        if os.path.exists(ip_saved_path):
            with open(ip_saved_path, "r", encoding="utf-8") as f:
                saved_ip = f.read().strip()
            if saved_ip:
                print(f"[*] Dang thu ket noi lai vao IP da nho: {saved_ip}...")
                conn_res = run_cmd("connect", f"{saved_ip}:5555")
                print(conn_res)
                if "connected" in conn_res.lower() and "cannot" not in conn_res.lower():
                    print()
                    print("========================================================")
                    print(" [v] KET NOI WI-FI THANH CONG!")
                    print("========================================================")
                    print(f" Dia chi IP: {saved_ip}")
                    print(" Gio ban co the mo Longtoitannatnhanratoilagay.bat de su dung khong day!")
                    print("========================================================")
                    return 0

        print("Huong dan kich hoat Wi-Fi lan dau:")
        print("  1. Cam cap USB noi dien thoai vao may tinh (khoang 3 giay).")
        print("  2. Dam bao dien thoai va may tinh dang bat CHUNG 1 mang Wi-Fi.")
        print("  3. Chay lai file nay (Ket_Noi_Wifi.bat).")
        print()
        user_input = input("Hoac neu ban da biet IP dien thoai, hay nhap vao day (Enter de thoat): ").strip()
        if user_input and re.match(r"^\d+\.\d+\.\d+\.\d+$", user_input):
            print(f"[*] Dang ket noi toi {user_input}:5555...")
            conn_res = run_cmd("connect", f"{user_input}:5555")
            print(conn_res)
            if "connected" in conn_res.lower() and "cannot" not in conn_res.lower():
                with open(ip_saved_path, "w", encoding="utf-8") as f:
                    f.write(user_input)
                print("[v] Ket noi thanh cong va da luu IP!")
                return 0
        return 1

    # 2. Phat hien dien thoai qua USB
    print(f"[*] Da tim thay thiet bi cam USB: {devices[0]}")
    print("[*] Dang lay dia chi IP Wi-Fi cua dien thoai...")
    ip = get_phone_ip()

    if not ip:
        print("[!] Khong the lay dia chi IP Wi-Fi.")
        print("    Vui long kiem tra xem dien thoai da ket noi vao Wi-Fi chua!")
        return 1

    print(f"[v] Da tim thay dia chi IP Wi-Fi: {ip}")
    print("[*] Dang kich hoat cong ket noi khong day (port 5555)...")
    tcpip_res = run_cmd("tcpip", "5555")
    print(tcpip_res or "Port 5555 da mo thanh cong.")
    time.sleep(1)

    print(f"[*] Dang thuc hien ket noi khong day toi {ip}:5555...")
    conn_res = run_cmd("connect", f"{ip}:5555")
    print(conn_res)

    if "connected" in conn_res.lower() and "cannot" not in conn_res.lower():
        # Luu IP lai cho cac lan sau
        with open(ip_saved_path, "w", encoding="utf-8") as f:
            f.write(ip)

        print()
        print("========================================================")
        print("   [v] KET NOI WI-FI THANH CONG!")
        print("========================================================")
        print(f"   Dia chi IP dien thoai : {ip}")
        print("   BAY GIO BAN CO THE RUT CAP USB RA!")
        print("   Tu nay chi can click dup vao Longtoitannatnhanratoilagay.bat")
        print("   la se tu dong bat khong day qua Wi-Fi!")
        print("========================================================")
        print()
        return 0
    else:
        print("[!] Ket noi chua thanh cong. Vui long thu lai.")
        return 1

if __name__ == "__main__":
    ret = main()
    print()
    input("Nhan phim Enter de thoat...")
    sys.exit(ret)
