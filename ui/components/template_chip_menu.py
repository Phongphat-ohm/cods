"""
Template Chip Preset Menu Builder
Reusable helper component for creating quick variable insertion menus
(Date, Time, Money, Select, and Text presets).
"""

from typing import Callable
from PySide6.QtWidgets import QMenu, QPushButton, QWidget
from ui.dialogs.variable_define_dialog import VariableDefineDialog


def create_base_chip_menu(parent: QWidget) -> QMenu:
    """Build a styled popup menu for chip selection."""
    menu = QMenu(parent)
    menu.setStyleSheet("""
        QMenu {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 6px;
            font-size: 13px;
        }
        QMenu::item {
            padding: 6px 18px;
            border-radius: 4px;
            color: #1e293b;
        }
        QMenu::item:selected {
            background-color: #f3e8ff;
            color: #4c1d95;
            font-weight: 500;
        }
    """)
    return menu


def prompt_custom_variable_define(
    parent: QWidget,
    on_insert: Callable[[str], None],
    initial_type: str = "date"
):
    """Open VariableDefineDialog and invoke on_insert with clean tag without brackets."""
    dlg = VariableDefineDialog(initial_type=initial_type, parent=parent)
    if dlg.exec() and dlg.generated_tag:
        clean_tag = dlg.generated_tag.strip().lstrip('[').rstrip(']')
        on_insert(clean_tag)


def show_date_chip_menu(btn: QPushButton, parent: QWidget, on_insert: Callable[[str], None]):
    """Show dropdown menu offering date formats."""
    menu = create_base_chip_menu(parent)
    formats = [
        ("แบบเต็ม (เช่น 18 ตุลาคม 2569)", "วันนัด:วันที่:เต็ม"),
        ("แบบย่อ (เช่น 18 ต.ค. 2569)", "วันนัด:วันที่:ย่อ"),
        ("แบบตัวเลข (เช่น 18/10/2569)", "วันนัด:วันที่:ตัวเลข"),
        ("แบบทางการศาล (เช่น วันที่ 18 เดือน ตุลาคม พ.ศ. 2569)", "วันนัด:วันที่:ทางการ"),
        ("วันและเดือน (เช่น 18 ตุลาคม)", "วันนัด:วันที่:วันเดือน"),
        ("มีชื่อวันในสัปดาห์ (เช่น วันอาทิตย์ที่ 18 ตุลาคม 2569)", "วันนัด:วันที่:วันในสัปดาห์"),
    ]
    for label, tag_code in formats:
        act = menu.addAction(label)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))
    menu.addSeparator()
    act_custom = menu.addAction("⚙️ กำหนดชื่อและรูปแบบวันที่เอง...")
    act_custom.triggered.connect(lambda: prompt_custom_variable_define(parent, on_insert, "date"))
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))


def show_time_chip_menu(btn: QPushButton, parent: QWidget, on_insert: Callable[[str], None]):
    """Show dropdown menu offering time formats."""
    menu = create_base_chip_menu(parent)
    time_items = [
        ("เวลานัดทางการ (เช่น 09.00 นาฬิกา)", "เวลานัด:เวลา"),
        ("เวลานัดแบบย่อ (เช่น 09.30 น.)", "เวลานัด:เวลา:น"),
        ("เวลาเริ่มพิจารณา (ทางการ)", "เวลาเริ่มพิจารณา:เวลา"),
    ]
    for label, tag_code in time_items:
        act = menu.addAction(label)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))
    menu.addSeparator()
    act_custom = menu.addAction("⚙️ กำหนดชื่อตัวแปรเวลาเอง...")
    act_custom.triggered.connect(lambda: prompt_custom_variable_define(parent, on_insert, "time"))
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))


def show_money_chip_menu(btn: QPushButton, parent: QWidget, on_insert: Callable[[str], None]):
    """Show dropdown menu offering number and currency variables."""
    menu = create_base_chip_menu(parent)
    money_items = [
        ("จำนวนเงิน (เช่น 50,000 บาท)", "จำนวนเงิน:ตัวเลข"),
        ("ทุนทรัพย์ (ตัวเลข/บาท)", "ทุนทรัพย์:ตัวเลข"),
        ("อัตราดอกเบี้ย (ตัวเลข)", "อัตราดอกเบี้ย:ตัวเลข"),
        ("ค่าเสียหาย (ตัวเลข/บาท)", "ค่าเสียหาย:ตัวเลข"),
    ]
    for label, tag_code in money_items:
        act = menu.addAction(label)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))
    menu.addSeparator()
    act_custom = menu.addAction("⚙️ กำหนดชื่อตัวเลข/เงินเอง...")
    act_custom.triggered.connect(lambda: prompt_custom_variable_define(parent, on_insert, "number"))
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))


def show_select_chip_menu(btn: QPushButton, parent: QWidget, on_insert: Callable[[str], None]):
    """Show dropdown menu offering dropdown/select variables."""
    menu = create_base_chip_menu(parent)
    select_items = [
        ("ผลการเจรจา (ไกล่เกลี่ยสำเร็จ, เจรจาไม่สำเร็จ, เลื่อนนัด)", "ผลการเจรจา:เลือก:ไกล่เกลี่ยสำเร็จ,เจรจาไม่สำเร็จ,เลื่อนนัด"),
        ("การมาศาล (โจทก์และจำเลยมาศาล, โจทก์มาศาล จำเลยไม่มา, ทนายความมาศาล)", "การมาศาล:เลือก:โจทก์และจำเลยมาศาล,โจทก์มาศาล จำเลยไม่มา,ทนายความมาศาล"),
        ("สถานะพยาน (สืบพยานเสร็จสิ้น, สืบพยานยังไม่เสร็จ, เลื่อนสืบพยาน)", "สถานะพยาน:เลือก:สืบพยานเสร็จสิ้น,สืบพยานยังไม่เสร็จ,เลื่อนสืบพยาน"),
    ]
    for label, tag_code in select_items:
        act = menu.addAction(label)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))
    menu.addSeparator()
    act_custom = menu.addAction("⚙️ กำหนดรายการตัวเลือก (Dropdown) เอง...")
    act_custom.triggered.connect(lambda: prompt_custom_variable_define(parent, on_insert, "select"))
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))


def show_text_chip_menu(btn: QPushButton, parent: QWidget, on_insert: Callable[[str], None]):
    """Show dropdown menu offering common text variables."""
    menu = create_base_chip_menu(parent)
    text_items = [
        ("ชื่อพยาน", "ชื่อพยาน"),
        ("หมายเหตุ", "หมายเหตุ"),
        ("ข้อตกลง", "ข้อตกลง"),
        ("คำสั่งศาล", "คำสั่งศาล"),
    ]
    for label, tag_code in text_items:
        act = menu.addAction(label)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))
    menu.addSeparator()
    act_custom = menu.addAction("⚙️ กำหนดชื่อข้อความทั่วไปเอง...")
    act_custom.triggered.connect(lambda: prompt_custom_variable_define(parent, on_insert, "text"))
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))


def show_combined_chip_menu(btn: QPushButton, parent: QWidget, on_insert: Callable[[str], None]):
    """Display quick cascading menu to pick or create template variable chips with formats."""
    menu = create_base_chip_menu(parent)

    # 1. Date Submenu
    menu_date = menu.addMenu("📅 วันนัด (วันที่)")
    menu_date.setStyleSheet(menu.styleSheet())
    date_formats = [
        ("แบบเต็ม (18 ตุลาคม 2569)", "วันนัด:วันที่:เต็ม"),
        ("แบบย่อ (18 ต.ค. 2569)", "วันนัด:วันที่:ย่อ"),
        ("แบบตัวเลข (18/10/2569)", "วันนัด:วันที่:ตัวเลข"),
        ("แบบทางการศาล (วันที่ 18 เดือน ตุลาคม พ.ศ. 2569)", "วันนัด:วันที่:ทางการ"),
        ("วันและเดือน (18 ตุลาคม)", "วันนัด:วันที่:วันเดือน"),
        ("มีชื่อวันในสัปดาห์ (วันอาทิตย์ที่ 18 ตุลาคม 2569)", "วันนัด:วันที่:วันในสัปดาห์"),
    ]
    for lbl, tag_code in date_formats:
        act = menu_date.addAction(lbl)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))

    # 2. Time Submenu
    menu_time = menu.addMenu("⏰ เวลานัด (เวลา)")
    menu_time.setStyleSheet(menu.styleSheet())
    time_formats = [
        ("แบบทางการ (09.00 นาฬิกา)", "เวลานัด:เวลา"),
        ("แบบย่อ (09.30 น.)", "เวลานัด:เวลา:น"),
    ]
    for lbl, tag_code in time_formats:
        act = menu_time.addAction(lbl)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))

    # 3. Number / Currency Submenu
    menu_num = menu.addMenu("🔢 จำนวนเงิน / ตัวเลข")
    menu_num.setStyleSheet(menu.styleSheet())
    num_formats = [
        ("จำนวนเงิน (เช่น 50,000 บาท)", "จำนวนเงิน:ตัวเลข"),
        ("ทุนทรัพย์ (ตัวเลข/บาท)", "ทุนทรัพย์:ตัวเลข"),
        ("อัตราดอกเบี้ย (ตัวเลข)", "อัตราดอกเบี้ย:ตัวเลข"),
        ("ค่าเสียหาย (ตัวเลข/บาท)", "ค่าเสียหาย:ตัวเลข"),
    ]
    for lbl, tag_code in num_formats:
        act = menu_num.addAction(lbl)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))

    # 4. Dropdown / Select Submenu
    menu_select = menu.addMenu("📋 ตัวเลือก (Dropdown)")
    menu_select.setStyleSheet(menu.styleSheet())
    select_formats = [
        ("ผลการเจรจา (ไกล่เกลี่ยสำเร็จ, เจรจาไม่สำเร็จ, เลื่อนนัด)", "ผลการเจรจา:เลือก:ไกล่เกลี่ยสำเร็จ,เจรจาไม่สำเร็จ,เลื่อนนัด"),
        ("การมาศาล (โจทก์และจำเลยมาศาล, โจทก์มาศาล จำเลยไม่มา, ทนายความมาศาล)", "การมาศาล:เลือก:โจทก์และจำเลยมาศาล,โจทก์มาศาล จำเลยไม่มา,ทนายความมาศาล"),
        ("สถานะพยาน (สืบพยานเสร็จสิ้น, สืบพยานยังไม่เสร็จ, เลื่อนสืบพยาน)", "สถานะพยาน:เลือก:สืบพยานเสร็จสิ้น,สืบพยานยังไม่เสร็จ,เลื่อนสืบพยาน"),
    ]
    for lbl, tag_code in select_formats:
        act = menu_select.addAction(lbl)
        act.triggered.connect(lambda checked=False, tc=tag_code: on_insert(tc))

    # 5. Text Presets
    presets = [
        ("✏️ ชื่อพยาน", "ชื่อพยาน"),
        ("✏️ หมายเหตุ", "หมายเหตุ"),
        ("✏️ ข้อตกลง", "ข้อตกลง"),
        ("✏️ คำสั่งศาล", "คำสั่งศาล"),
    ]
    for label, var_name in presets:
        act = menu.addAction(label)
        act.triggered.connect(lambda checked=False, v=var_name: on_insert(v))

    menu.addSeparator()
    action_custom = menu.addAction("⚙️ กำหนดตัวแปรและประเภทเอง...")
    action_custom.triggered.connect(lambda: prompt_custom_variable_define(parent, on_insert, "date"))

    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
