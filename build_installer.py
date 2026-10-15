"""
CODS Build & Packaging Automation Script
100% Native Python - Full Unicode & Path Safety
"""

import sys
import os
import shutil
import subprocess
import winreg
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def log(msg: str):
    print(f"[*] {msg}", flush=True)


def log_success(msg: str):
    print(f"[+] {msg}", flush=True)


def log_error(msg: str):
    print(f"[-] {msg}", flush=True)


def find_iscc_path() -> str:
    """Find Inno Setup Compiler (ISCC.exe) on the system."""
    # 1. Known machine path
    known_path = r"D:\.PHONGPHAT\Inno Setup 6\ISCC.exe"
    if os.path.exists(known_path):
        return known_path

    # 2. Check PATH
    sh_iscc = shutil.which("iscc")
    if sh_iscc and os.path.exists(sh_iscc):
        return sh_iscc

    # 3. Check Windows Registry
    reg_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for root, subkey in reg_keys:
        try:
            with winreg.OpenKey(root, subkey) as k:
                num_subkeys = winreg.QueryInfoKey(k)[0]
                for i in range(num_subkeys):
                    try:
                        name = winreg.EnumKey(k, i)
                        with winreg.OpenKey(k, name) as app_key:
                            disp, _ = winreg.QueryValueEx(app_key, "DisplayName")
                            if "inno setup" in disp.lower():
                                loc, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                                iscc_cand = os.path.join(loc, "ISCC.exe")
                                if os.path.exists(iscc_cand):
                                    return iscc_cand
                    except Exception:
                        pass
        except Exception:
            pass

    # 4. Standard directories
    standard_paths = [
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
    ]
    for p in standard_paths:
        if os.path.exists(p):
            return p

    return ""


def main():
    root_dir = Path(__file__).resolve().parent
    os.chdir(root_dir)

    print("=" * 70)
    print("   CODS - Inno Setup Build Automation (v1.2.0)")
    print("   คอมไพล์โปรแกรมจากโค้ดปัจจุบัน และสร้างตัวติดตั้ง Inno Setup")
    print("=" * 70)
    print()

    # Step 1: Ensure logo.ico
    log("ตรวจสอบไฟล์โลโก้...")
    logo_ico = root_dir / "logo.ico"
    logo_png = root_dir / "logo.png"
    if not logo_ico.exists() and logo_png.exists():
        try:
            from PySide6.QtGui import QImage
            img = QImage(str(logo_png))
            img.save(str(logo_ico))
        except Exception:
            pass

    # Step 2: Compile with PyInstaller from current source files
    log("[1/3] กำลังคอมไพล์โปรแกรมจากซอร์สโค้ดปัจจุบันด้วย PyInstaller...")
    spec_file = root_dir / "cods.spec"
    if not spec_file.exists():
        log_error("ไม่พบไฟล์ cods.spec")
        return 1

    cmd_pyi = [sys.executable, "-m", "PyInstaller", str(spec_file), "--noconfirm"]
    ret = subprocess.run(cmd_pyi, cwd=str(root_dir))
    if ret.returncode != 0:
        log_error("การคอมไพล์ PyInstaller ล้มเหลว")
        return ret.returncode

    # Step 3: Copy assets into dist\CODS
    log("[2/3] กำลังจัดเตรียมแม่แบบเอกสาร (templates) และไอคอน...")
    dist_cods = root_dir / "dist" / "CODS"
    dist_templates = dist_cods / "templates"
    src_templates = root_dir / "templates"

    if src_templates.exists():
        dist_templates.mkdir(parents=True, exist_ok=True)
        for tpl in src_templates.glob("*"):
            if tpl.is_file():
                shutil.copy2(tpl, dist_templates / tpl.name)

    if logo_ico.exists():
        shutil.copy2(logo_ico, dist_cods / "logo.ico")
    if logo_png.exists():
        shutil.copy2(logo_png, dist_cods / "logo.png")

    log_success("อัปเดตไฟล์ใน dist\\CODS จากโค้ดปัจจุบันเรียบร้อยแล้ว")
    print()

    # Step 4: Find Inno Setup Compiler
    log("[3/3] กำลังค้นหา Inno Setup Compiler (ISCC.exe)...")
    iscc_path = find_iscc_path()
    if not iscc_path:
        log_error("ไม่พบโปรแกรม Inno Setup Compiler (ISCC.exe) ในเครื่อง")
        print()
        print("ท่านสามารถ:")
        print("1. เปิดไฟล์ 'installer_inno.iss' ด้วยโปรแกรม Inno Setup Compiler แล้วกด F9 (Compile)")
        print("2. หรือดาวน์โหลด Inno Setup ได้ที่: https://jrsoftware.org/isdl.php")
        print()
        return 1

    log(f"พบ Inno Setup ที่: {iscc_path}")
    log("กำลังคอมไพล์ installer_inno.iss เพื่อสร้างตัวติดตั้ง...")
    print()

    iss_file = root_dir / "installer_inno.iss"
    cmd_inno = [iscc_path, str(iss_file)]
    ret_inno = subprocess.run(cmd_inno, cwd=str(root_dir))
    if ret_inno.returncode != 0:
        log_error("การสร้างตัวติดตั้ง Inno Setup ล้มเหลว")
        return ret_inno.returncode

    out_file = root_dir / "dist_installer" / "CODS_Setup_v1.2.exe"
    print()
    print("=" * 70)
    print("   [สำเร็จ 100%] สร้างตัวติดตั้ง CODS จากไฟล์ปัจจุบันเรียบร้อยแล้ว!")
    print("=" * 70)
    if out_file.exists():
        size_mb = out_file.stat().st_size / (1024 * 1024)
        print(f"ไฟล์ตัวติดตั้ง: {out_file} ({size_mb:.1f} MB)")
    print()
    return 0


if __name__ == "__main__":
    exit_code = main()
    print()
    if sys.stdin.isatty():
        try:
            input("กด Enter เพื่อปิดหน้าต่าง...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(exit_code)
