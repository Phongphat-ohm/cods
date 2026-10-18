"""
CODS (Court Official Document System) - Python Standalone 100% Offline
Ultra-Fast Bootstrap Launcher with Instant Splash Screen & Lazy Module Loading
"""

import sys
import os
import traceback
from datetime import datetime

# Configure Windows Taskbar AppUserModelID for judicial branding
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("coj.cods.desktop.app")
    except Exception:
        pass

# Ultra-lean imports for instantaneous (< 150ms) startup splash display
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from constants import APP_NAME, APP_VERSION
from services.icon_service import get_app_logo_icon
from ui.components.splash_screen import CODSSplashScreen


def setup_global_exception_handler():
    """Catch unhandled exceptions and log them to crash.log, preventing silent crashes."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            from services import storage_service
            log_dir = storage_service.resolve_data_dir()
            crash_file = os.path.join(log_dir, "crash.log")
            with open(crash_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- CRASH AT {datetime.now().isoformat()} ---\n{err_msg}\n")
        except Exception:
            pass

        try:
            QMessageBox.critical(
                None,
                "ข้อผิดพลาดที่ไม่คาดคิด (Application Error)",
                f"เกิดข้อผิดพลาดในการทำงานของระบบ:\n{str(exc_value)}\n\n"
                f"ระบบได้บันทึกรายละเอียดข้อผิดพลาดลงใน crash.log เรียบร้อยแล้ว"
            )
        except Exception:
            pass

    sys.excepthook = handle_exception


class SingleApplicationManager:
    """Ensure single instance of the application to prevent SQLite database conflicts."""
    def __init__(self, app_id="coj.cods.single_instance"):
        self.app_id = app_id
        self.server = None

    def is_running(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        if socket.waitForConnected(300):
            socket.close()
            return True
        QLocalServer.removeServer(self.app_id)
        self.server = QLocalServer()
        self.server.listen(self.app_id)
        return False


def __getattr__(name: str):
    """Dynamic resolution for backward compatibility if CODSMainWindow is imported from main."""
    if name in ("CODSMainWindow", "JADSMainWindow"):
        from ui.main_window import CODSMainWindow
        return CODSMainWindow
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def setup_qt_message_handler():
    """
    Filter out benign Windows DirectWrite font metric calculation warnings
    (e.g., QWindowsFontEngineDirectWrite::recalcAdvances: GetDesignGlyphMetrics failed)
    which occur on Windows when text layouts measure fallback characters.
    """
    from PySide6.QtCore import qInstallMessageHandler, QtMsgType

    def qt_message_handler(msg_type, context, message):
        msg_str = str(message or "")
        if any(w in msg_str for w in ("GetDesignGlyphMetrics", "recalcAdvances", "QWindowsFontEngineDirectWrite", "setPointSize")):
            return
        cat_str = str(getattr(context, "category", "") or "")
        if "qt.qpa.fonts" in cat_str or "qt.text" in cat_str:
            return

        if msg_type == QtMsgType.QtFatalMsg:
            sys.stderr.write(f"[FATAL] {message}\n")
        elif msg_type == QtMsgType.QtCriticalMsg:
            sys.stderr.write(f"[CRITICAL] {message}\n")
        elif msg_type == QtMsgType.QtWarningMsg:
            if not any(f in msg_str for f in ("QWindowsFontEngine", "DirectWrite", "glyph", "GetDesignGlyphMetrics", "setPointSize")):
                sys.stderr.write(f"[WARN] {message}\n")

    qInstallMessageHandler(qt_message_handler)


def main():
    # Mute noisy internal Windows DirectWrite font warnings before Qt initializes
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false;qt.text.*=false")

    setup_global_exception_handler()
    setup_qt_message_handler()

    # High DPI rendering policy
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setWindowIcon(get_app_logo_icon())

    # Prevent concurrent instances and database locking
    single_app = SingleApplicationManager()
    if single_app.is_running():
        QMessageBox.information(
            None,
            "โปรแกรมกำลังทำงานอยู่",
            "ระบบ CODS กำลังทำงานอยู่แล้วในหน้าต่างอื่น\nกรุณาสลับไปยังหน้าต่างโปรแกรมที่เปิดอยู่"
        )
        sys.exit(0)

    # =========================================================================
    # STEP 1: INSTANT SPLASH SCREEN LAUNCH (< 150ms from user click)
    # Shown and painted immediately before any heavy subsystem is touched!
    # =========================================================================
    splash = CODSSplashScreen()
    splash.show()
    splash.raise_()
    splash.activateWindow()
    splash.repaint()
    app.processEvents()

    class AppInitializer:
        def __init__(self, qapp, splash_screen):
            self.app = qapp
            self.splash = splash_screen
            self.window = None
            self.CODSMainWindow = None

        def start(self):
            self.splash.set_progress(15, "กำลังเริ่มต้นระบบ CODS...")
            QTimer.singleShot(50, self.step1_fonts)

        def step1_fonts(self):
            # Phase 1: Load fonts (35%)
            from ui.theme import load_application_fonts, get_default_font
            load_application_fonts()
            self.app.setFont(get_default_font(11))
            self.splash.set_progress(35, "กำลังโหลดฟอนต์ระบบและธีมศาลยุติธรรม...")
            QTimer.singleShot(40, self.step2_database)

        def step2_database(self):
            # Phase 2: SQLite court database verification & auto-recovery (60%)
            from services import storage_service
            try:
                storage_service.init_db()
                storage_service.check_and_recover_db()
            except Exception as e:
                print(f"[WARN] Database initialization notice: {e}")
            self.splash.set_progress(60, "กำลังตรวจสอบความสมบูรณ์ของฐานข้อมูลคดี...")
            QTimer.singleShot(40, self.step3_modules)

        def step3_modules(self):
            # Phase 3: Lazy load document engines & page modules (80%)
            self.splash.set_progress(80, "กำลังโหลดโมดูลเอกสารและแบบฟอร์ม...")
            from ui.main_window import CODSMainWindow
            self.CODSMainWindow = CODSMainWindow
            QTimer.singleShot(40, self.step4_ui)

        def step4_ui(self):
            # Phase 4: Construct main window UI layout & state (95%)
            self.splash.set_progress(95, "กำลังจัดเตรียมหน้าต่างการทำงานและแม่แบบ...")
            self.window = self.CODSMainWindow()
            QTimer.singleShot(40, self.step5_finish)

        def step5_finish(self):
            # Phase 5: 100% complete with smooth transition
            self.splash.set_progress(100, "ระบบพร้อมใช้งาน กำลังเปิดโปรแกรม...")
            QTimer.singleShot(180, self.open_main_window)

        def open_main_window(self):
            self.splash.finish(self.window)
            self.window.showMaximized()

    initializer = AppInitializer(app, splash)
    QTimer.singleShot(20, initializer.start)

    sys.exit(app.exec())



if __name__ == '__main__':
    main()
