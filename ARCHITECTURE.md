# CODS Modular Architecture & Component Reference
**ระบบจัดเก็บและสร้างเอกสารศาลแบบแยกส่วน (Modular Clean Architecture)**  
*Court Official Document System (CODS) - Python Standalone 100% Offline*

---

## 1. ภาพรวมสถาปัตยกรรมระบบ (System Architecture Overview)

ระบบได้รับการออกแบบใหม่ตามหลักการ **Single Responsibility Principle (SRP)** และ **Component-Based Architecture** โดยแยกส่วนการทำงานที่เคยถูกรวมไว้ในไฟล์ monolithic ขนาดใหญ่ (เช่น `form_page.py` และ `online_form_page.py` ที่เคยมีขนาดยาวกว่า 2,200 บรรทัด) ออกมาเป็น Component ย่อยๆ ในโครงสร้างโฟลเดอร์ที่เป็นระเบียบ อ่านง่าย ตรวจสอบง่าย และบำรุงรักษาได้สะดวก

```
jads-python/
│
├── main.py                     # Entry point หลัก (Instant Splash & Fast Bootstrap)
├── constants.py                # ค่าคงที่และค่าคอนฟิกพื้นฐานของระบบ
│
├── ui/                         # ชั้นส่วนติดต่อผู้ใช้ (User Interface Layer)
│   ├── main_window.py          # Window Controller ควบคุม Navigation และ Flow ทั้งหมด
│   ├── theme.py                # ระบบธีม Imperial Amethyst, Fonts และ Stylesheet
│   │
│   ├── pages/                  # หน้าการทำงานหลัก (Wizard Pages)
│   │   ├── menu_page.py        # [หน้า 0] เมนูหลักและ Dashboard
│   │   ├── import_page.py      # [หน้า 1] อัปโหลดไฟล์ Excel (Drag & Drop)
│   │   ├── table_page.py       # [หน้า 2] ตารางเลือกคดีและตัวกรองค้นหา
│   │   ├── doc_type_page.py    # [หน้า 3] เลือกประเภทเอกสาร (รายงานฯ / คำพิพากษาตามยอม)
│   │   ├── form_page.py        # [หน้า 4] วิซาร์ดจัดทำรายงานกระบวนพิจารณา & คำพิพากษาตามยอม
│   │   └── online_form_page.py # [หน้า 4 ออนไลน์] วิซาร์ดจัดทำรายงานกระบวนพิจารณาคดีออนไลน์
│   │
│   ├── components/             # คอมโพเนนต์ UI พื้นฐานและคอมโพเนนต์ย่อย
│   │   │
│   │   ├── form_sections/      # ★ [NEW] คอมโพเนนต์แยกส่วนของแบบฟอร์ม (Form Section Widgets)
│   │   │   ├── case_info_section.py      # CaseInfoSectionWidget: ข้อมูลคดี, ศาล, วันเวลานัด, คู่ความ
│   │   │   ├── bench_pairing_section.py  # BenchPairingWidget: องค์คณะผู้พิพากษา & การจับคู่คู่เวร
│   │   │   ├── compromise_details_section.py # CompromiseDetailsWidget: สัญญาตามยอม & คืนค่าขึ้นศาล
│   │   │   ├── paragraphs_section.py     # ParagraphsSectionWidget: รายการย่อหน้า & ตัวจัดการการ์ด
│   │   │   ├── dynamic_variables_panel.py# DynamicVariablesPanel: แผงกรอกตัวแปรไดนามิกจากแม่แบบ
│   │   │   └── __init__.py               # รวม Export โมดูล Form Sections
│   │   │
│   │   ├── variable_inputs/    # คอมโพเนนต์ช่องกรอกข้อมูลตัวแปรตามชนิด (Typed Variable Inputs)
│   │   │   ├── date_picker.py  # ThaiDatePickerWidget: ตัวเลือกวันที่ปฏิทินไทย
│   │   │   ├── time_input.py   # TimeVariableInputWidget: ตัวเลือกเวลานัด
│   │   │   ├── number_input.py # NumberVariableInputWidget: ช่องกรอกตัวเลขและเงิน
│   │   │   ├── select_input.py # SelectVariableInputWidget: เมนูตัวเลือก Dropdown
│   │   │   ├── factory.py      # Factory สำหรับสร้าง Input Widget ตาม Tag ตัวแปร
│   │   │   └── __init__.py
│   │   │
│   │   ├── signatories_manager.py        # SignatoriesManagerWidget: จัดการรายชื่อผู้มาศาล
│   │   ├── online_signatories_manager.py # OnlineSignatoriesManagerWidget: จัดการผู้มาศาลออนไลน์
│   │   ├── paragraph_card.py             # ParagraphCard: การ์ดย่อหน้าข้อความกระบวนพิจารณา
│   │   ├── autocomplete_input.py         # JudicialAutocompleteInput: ช่องพิมพ์พร้อมตัวเลือกอัตโนมัติ
│   │   ├── sidebar.py                    # SidebarWidget: แถบนำทางด้านซ้าย
│   │   ├── shortcut_bar.py               # ShortcutTipBar: แถบคีย์ลัดด้านล่าง
│   │   ├── splash_screen.py              # CODSSplashScreen: หน้าจอโหลดเริ่มต้น
│   │   ├── tutorial_overlay.py           # TutorialOverlay: แนะนำการใช้งานระบบ
│   │   ├── template_chip_highlighter.py  # ระบบไฮไลต์ชิปตัวแปรใน Text Editor
│   │   ├── template_chip_menu.py         # เมนูแทรกชิปตัวแปร
│   │   ├── variable_chip_widget.py       # ชิปแสดงตัวแปรใต้การ์ดย่อหน้า
│   │   ├── draggable_list.py             # Drag-and-drop List Widget
│   │   ├── judicial_card.py              # JudicialAccentCard: การ์ดเน้นขอบสีม่วงศาล
│   │   └── __init__.py                   # PEP 562 Lazy Loading Architecture
│   │
│   └── dialogs/                # กล่องข้อความและการตั้งค่า (Modal Dialogs)
│       ├── template_manager_dialog.py    # จัดการแม่แบบข้อความสำเร็จรูป
│       ├── template_select_dialog.py     # หน้าต่างเลือกแม่แบบข้อความ
│       ├── template_recovery_dialog.py   # ตรวจสอบและกู้คืนแม่แบบ Word
│       ├── bench_manager_dialog.py       # จัดการคู่เวรองค์คณะผู้พิพากษา
│       ├── signatory_role_manager_dialog.py # จัดการตำแหน่งผู้มาศาล
│       ├── court_settings_dialog.py      # ตั้งค่าชื่อศาลเริ่มต้น
│       ├── welcome_wizard_dialog.py      # วิซาร์ดต้อนรับการใช้งานครั้งแรก
│       ├── shortcuts_guide_dialog.py     # คู่มือแนะนำคีย์ลัด
│       ├── about_dialog.py               # เกี่ยวกับโปรแกรมและข้อมูลลิขสิทธิ์
│       └── __init__.py
│
├── services/                   # ชั้นประมวลผลทางธุรกิจและข้อมูล (Business Logic & Services)
│   ├── storage_service.py      # จัดการฐานข้อมูล SQLite (cods.db) และไฟล์สำรอง JSON
│   ├── docx_service.py         # สร้างเอกสาร Word (.docx) และประมวลผล XML Template
│   ├── excel_service.py        # นำเข้าไฟล์ Excel ตารางนัดความ และจัดรูปแบบข้อมูล
│   ├── icon_service.py         # จัดการไอคอน SVG และ Pixmap Cache
│   ├── template_variable_service.py # วิเคราะห์ Tag ตัวแปรและจัดรูปแบบวันที่ไทย
│   ├── template_recovery_service.py # วิเคราะห์โครงสร้างแม่แบบ Word และกู้คืนไฟล์เสีย
│   └── __init__.py
│
└── tests/                      # ชุดทดสอบอัตโนมัติ (Automated Unit Tests)
    ├── test_template_variables.py # ทดสอบระบบตัวแปรแม่แบบและการแปลงวันที่
    └── test_form_sections.py      # ทดสอบคอมโพเนนต์ย่อยของแบบฟอร์ม (Form Sections)
```

---

## 2. รายละเอียดของโมดูลย่อยที่แยกออกมา (Component Breakdown)

### 2.1 `CaseInfoSectionWidget` (`ui/components/form_sections/case_info_section.py`)
- **หน้าที่**: รับผิดชอบเฉพาะส่วนการกรอกและแสดงผลข้อมูลคดีความ
- **ส่วนประกอบ**:
  - `txt_case_black`: เลขคดีดำ
  - `txt_case_red`: เลขคดีแดง
  - `txt_court_name`: ชื่อศาล (พร้อมปุ่ม "ตั้งเป็นศาลเริ่มต้น")
  - `txt_case_type`: ประเภทคดี (ความแพ่ง, ความอาญา, ผบE, ฯลฯ)
  - `txt_hearing_purpose`: เหตุที่นัด (สืบพยาน, ชี้สองสถาน, นัดพร้อม, ฯลฯ)
  - `txt_day`, `txt_month`, `txt_year`, `txt_time`: วันเวลานัดพิจารณา
  - `txt_plaintiff`, `txt_defendant`: คู่ความ (โจทก์ / จำเลย)
- **API สำคัญ**:
  - `load_case_row(row, mapping)`: แยกข้อมูลจาก Excel เข้าสู่ฟิลด์โดยอัตโนมัติ
  - `get_case_data() -> dict`: รวบรวมข้อมูลคดีทั้งหมดส่งออกไปสร้างเอกสาร
  - `save_current_court_as_default()`: บันทึกศาลเริ่มต้นลงฐานข้อมูล
  - `focus_first_empty_field()`: เลื่อนเคอร์เซอร์ไปยังช่องที่ยังไม่ได้กรอก

### 2.2 `BenchPairingWidget` (`ui/components/form_sections/bench_pairing_section.py`)
- **หน้าที่**: จัดการองค์คณะผู้พิพากษาและการจับคู่คู่เวรโดยเฉพาะ
- **ส่วนประกอบ**:
  - `txt_judge1`: ผู้พิพากษาเจ้าของสำนวน
  - `txt_judge2`: ผู้พิพากษาองค์คณะ
  - `lbl_bench_status`: สถานะการจับคู่ (สีเขียวเมื่อพบคู่เวรเดิม)
  - `btn_save_pairing`: ปุ่มบันทึกการจับคู่นี้สำหรับครั้งต่อไป
  - `btn_bench_config`: ปุ่มเปิดหน้าต่างจัดการคู่องค์คณะ
- **API สำคัญ**:
  - `refresh_completers()`: โหลดรายชื่อผู้พิพากษาที่เคยบันทึกไว้เข้าตัวช่วยพิมพ์
  - `handle_judge1_changed(text)`: ค้นหาองค์คณะคู่เวรโดยอัตโนมัติเมื่อพิมพ์ชื่อเจ้าของสำนวน
  - `confirm_bench_pair_if_needed() -> bool`: ตรวจสอบและถามผู้ใช้ว่าต้องการบันทึกคู่เวรใหม่หรือไม่
  - `get_judges() -> tuple[str, str]`: ดึงชื่อองค์คณะทั้งสองท่าน

### 2.3 `CompromiseDetailsWidget` (`ui/components/form_sections/compromise_details_section.py`)
- **หน้าที่**: ดูแลเฉพาะข้อมูลสำหรับเอกสาร "คำพิพากษาตามยอม"
- **ส่วนประกอบ**:
  - `txt_compromise_subject`: ข้อหา/เรื่องแห่งคดี
  - `txt_compromise_date`: วันที่ในสัญญาประนีประนอมยอมความ (มีปุ่มดึงวันนัดจากคดี / ใช้วันนี้)
  - `txt_refund_total`: จำนวนเงินคืนค่าขึ้นศาล (มีระบบจัดรูปแบบลูกน้ำคั่นหลักพันอัตโนมัติ และปุ่มสลับเลขไทย/อารบิก)
  - `lbl_comp_summary_text`: การ์ดสรุปภาพรวมของคำพิพากษาตามยอม
- **API สำคัญ**:
  - `format_thai_currency(text) -> str`: จัดฟอร์แมตตัวเลขเงินบาท
  - `update_summary(case_data, j1, j2)`: อัปเดตการ์ดสรุปข้อมูล
  - `get_compromise_data() -> dict`: ดึงข้อมูลคำพิพากษาตามยอม

### 2.4 `ParagraphsSectionWidget` (`ui/components/form_sections/paragraphs_section.py`)
- **หน้าที่**: ควบคุมและบริหารจัดการรายการย่อหน้าข้อความกระบวนพิจารณา (`ParagraphCard`)
- **ส่วนประกอบ**:
  - ป้ายแสดงจำนวนย่อหน้า
  - Placeholder Card เมื่อยังไม่มีการเพิ่มย่อหน้า
  - ปุ่ม "เพิ่มย่อหน้าจาก Template" และ "เพิ่มย่อหน้าเปล่า" ทั้งด้านบนและด้านล่าง
  - ระบบ Reorder (สลับตำแหน่งการ์ดขึ้น-ลง หรือลบการ์ด)
- **API สำคัญ**:
  - `add_paragraph_card(initial_text="") -> ParagraphCard`: เพิ่มการ์ดย่อหน้าใหม่
  - `move_paragraph_up(card)` / `move_paragraph_down(card)`: สลับลำดับ
  - `delete_paragraph_card(card)`: ลบการ์ดย่อหน้า
  - `get_paragraph_texts() -> list[str]`: รวบรวมข้อความทั้งหมดเพื่อนำไปสร้างเอกสาร Word

### 2.5 `DynamicVariablesPanel` (`ui/components/form_sections/dynamic_variables_panel.py`)
- **หน้าที่**: สแกนหาตัวแปรที่ผู้ใช้กำหนดเอง (เช่น `{{วันนัด:วันที่}}`, `{{จำนวนเงิน:ตัวเลข}}`) จากแม่แบบ Word และจากย่อหน้า แล้วสร้างช่องกรอกข้อมูลเฉพาะทาง (Typed Inputs) ให้โดยอัตโนมัติ
- **ส่วนประกอบ**:
  - แผงการ์ดสีม่วงอ่อน แสดงช่องกรอกตัวแปรแยกตามหมวดหมู่
  - ปุ่ม "นำค่าทั้งหมดไปแทนที่ในข้อความ"
- **API สำคัญ**:
  - `scan_and_update(cards, doc_type, tpl_path)`: สแกนหาตัวแปรและแสดงหรือซ่อนแผงโดยอัตโนมัติ
  - `apply_dynamic_values_to_paragraph_cards(cards)`: แทนที่ค่าจริงลงในกล่องข้อความย่อหน้า
  - `get_dynamic_values() -> dict`: รวบรวมค่าตัวแปรเพื่อส่งให้ Word Engine

---

## 3. สรุปผลการปรับปรุง (Key Architectural Improvements)

| หัวข้อ | ก่อนปรับปรุง | หลังปรับปรุง |
| :--- | :--- | :--- |
| **ขนาดไฟล์ `form_page.py`** | 2,270 บรรทัด (dump ทุกอย่างในไฟล์เดียว) | **650 บรรทัด** (Modular Controller ที่อ่านง่าย) |
| **ขนาดไฟล์ `online_form_page.py`** | 1,595 บรรทัด | **570 บรรทัด** (ใช้ sub-components ร่วมกัน) |
| **ระบบ File System & Package** | มี import ปะปนระหว่าง root forwarders กับ sub-packages | จัดกลุ่มเป็น `services.*`, `ui.components.*`, `ui.dialogs.*` ชัดเจน 100% |
| **ความง่ายในการอ่านโค้ด** | โค้ด UI, ตรรกะจับคู่ผู้พิพากษา, ตรรกะคำนวณเงิน, และการสร้างเอกสารปนกัน | แยกไฟล์ตามหน้าที่ชัดเจน (Case Info, Bench, Compromise, Paragraphs, Dynamic Vars) |
| **ความเข้ากันได้ย้อนหลัง** | - | **100% Backward Compatible** (รักษา Public APIs, Signals, Attributes ครบถ้วน) |
| **Unit Test Coverage** | 22 tests | **27 tests (ผ่าน 100%)** ครอบคลุม components ใหม่ทั้งหมด |
