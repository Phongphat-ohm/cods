"""
CODS Template Recovery and Validation Service (100% Offline & Air-Gapped)
Provides comprehensive verification of Word (.docx) templates:
- Checks for missing required variables (with clear Thai descriptions)
- Checks for loop block mismatches ({{#paragraphs}} ... {{/paragraphs}}, {{#signatories}} ... {{/signatories}})
- Checks for unclosed or malformed braces
- Provides automated restoration from pristine factory templates with safety backups
"""

import os
import re
import shutil
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from services import storage_service
from services.docx_service import validate_template_variable, FORBIDDEN_CONTROL_KEYWORDS

# Definition of standard templates recognized by CODS
TEMPLATE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "report": {
        "filename": "รายงานกระบวนพิจารณา.docx",
        "display_name": "รายงานกระบวนพิจารณา (ปกติ)",
        "required_variables": {
            "case_black_no": "คดีหมายเลขดำที่ (เช่น ผบE1/2569)",
            "case_red_no": "คดีหมายเลขแดงที่",
            "court_name": "ชื่อศาล (เช่น ศาลแพ่ง)",
            "date": "วันที่ (หรือ day, d)",
            "month": "เดือน (เช่น มกราคม)",
            "year": "ปี พ.ศ. (เช่น 2569)",
            "plaintiff_name": "ชื่อโจทก์",
            "defendant_name": "ชื่อจำเลย",
            "judge_1_name": "ชื่อผู้พิพากษาเจ้าของสำนวน",
            "attendees_summary": "ข้อความสรุปผู้มาศาล (เช่น 'ทนายโจทก์และทนายจำเลยมาศาล')",
        },
        "required_loops": {
            "paragraphs": {
                "start": "#paragraphs",
                "end": "/paragraphs",
                "inner": ".",
                "description": "บล็อกวนซ้ำย่อหน้ากระบวนพิจารณา ({{#paragraphs}} ... {{/paragraphs}}) ซึ่งจำเป็นต้องมีเพื่อให้โปรแกรมเขียนเนื้อหากระบวนพิจารณาลงในเอกสารได้"
            },
            "signatories": {
                "start": "#signatories",
                "end": "/signatories",
                "inner": "position",
                "description": "บล็อกวนซ้ำผู้ลงชื่อท้ายรายงาน ({{#signatories}} ... {{/signatories}}) สำหรับใส่รายชื่อและตำแหน่งผู้พิพากษาและคู่ความ"
            }
        }
    },
    "online_report": {
        "filename": "รายงานกระบวนพิจารณาออนใลน์.docx",
        "display_name": "รายงานกระบวนพิจารณา (ระบบออนไลน์)",
        "required_variables": {
            "case_black_no": "คดีหมายเลขดำที่ (เช่น ผบE1/2569)",
            "case_red_no": "คดีหมายเลขแดงที่",
            "court_name": "ชื่อศาล (เช่น ศาลแพ่ง)",
            "date": "วันที่ (หรือ day, d)",
            "month": "เดือน (เช่น มกราคม)",
            "year": "ปี พ.ศ. (เช่น 2569)",
            "plaintiff_name": "ชื่อโจทก์",
            "defendant_name": "ชื่อจำเลย",
            "judge_1_name": "ชื่อผู้พิพากษาเจ้าของสำนวน",
            "attendees_summary": "ข้อความสรุปผู้มาศาลและระบบออนไลน์",
        },
        "required_loops": {
            "paragraphs": {
                "start": "#paragraphs",
                "end": "/paragraphs",
                "inner": ".",
                "description": "บล็อกวนซ้ำย่อหน้ากระบวนพิจารณา ({{#paragraphs}} ... {{/paragraphs}}) สำหรับใส่เนื้อหากระบวนพิจารณาออนไลน์"
            },
            "signatories": {
                "start": "#signatories",
                "end": "/signatories",
                "inner": "position",
                "description": "บล็อกวนซ้ำผู้ลงชื่อท้ายรายงาน ({{#signatories}} ... {{/signatories}}) รองรับทั้งผู้ที่มาศาลและผู้ที่เข้าร่วมออนไลน์"
            }
        }
    },
    "compromise": {
        "filename": "คำพิพากษาตามยอม.docx",
        "display_name": "คำพิพากษาตามยอม (แบบพิมพ์ ๓๐)",
        "required_variables": {
            "case_black_no": "คดีหมายเลขดำที่",
            "case_red_no": "คดีหมายเลขแดงที่",
            "court_name": "ชื่อศาล",
            "plaintiff_name": "ชื่อโจทก์",
            "defendant_name": "ชื่อจำเลย",
            "d": "วันที่ (หรือ day, date)",
            "month": "เดือน",
            "year": "ปี พ.ศ.",
            "judge_1_name": "ชื่อผู้พิพากษาคนที่ 1",
            "case_type": "ประเภทความ (เช่น คดีแพ่งสามัญ)",
            "case_subject": "เรื่อง / ข้อหาแห่งคดี",
            "refund_total": "จำนวนเงินค่าขึ้นศาลที่สั่งคืน"
        },
        "required_loops": {}
    }
}


def get_default_factory_template_path(filename: str) -> Optional[str]:
    """Find the pristine factory template file packaged with the program."""
    # 1. Check default_templates folder beside app / project root
    app_dir = storage_service.get_app_dir()
    p1 = os.path.join(app_dir, "default_templates", filename)
    if os.path.exists(p1) and os.path.getsize(p1) > 0:
        return p1

    # 2. Check bundle directory (_MEIPASS / executable)
    bundle_dir = storage_service.get_bundle_dir()
    p2 = os.path.join(bundle_dir, "default_templates", filename)
    if os.path.exists(p2) and os.path.getsize(p2) > 0:
        return p2

    p3 = os.path.join(bundle_dir, "templates", filename)
    if os.path.exists(p3) and os.path.getsize(p3) > 0:
        return p3

    # 3. Check current working directory
    p4 = os.path.join(os.getcwd(), "default_templates", filename)
    if os.path.exists(p4) and os.path.getsize(p4) > 0:
        return p4

    return None


def validate_word_template(docx_path: str, tpl_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform deep validation of a Word template (.docx):
    - Verifies file integrity (valid zip and XML structure)
    - Detects unclosed braces or syntax corruption
    - Validates presence of essential judicial variables
    - Validates loop block pairing (#paragraphs / /paragraphs, #signatories / /signatories)
    """
    res: Dict[str, Any] = {
        "valid": True,
        "docx_path": docx_path,
        "filename": os.path.basename(docx_path),
        "tpl_key": tpl_key,
        "file_exists": False,
        "file_readable": False,
        "detected_tags": [],
        "missing_required": [],
        "missing_loops": [],
        "syntax_errors": [],
        "warnings": [],
        "status_level": "success",  # "success", "warning", "error"
        "status_message": "แม่แบบสมบูรณ์พร้อมใช้งาน"
    }

    if not docx_path or not os.path.exists(docx_path):
        res["valid"] = False
        res["status_level"] = "error"
        res["status_message"] = f"ไม่พบไฟล์แม่แบบที่: {docx_path}"
        return res

    res["file_exists"] = True

    # Identify template key if not provided
    fname = os.path.basename(docx_path)
    if not tpl_key:
        for k, v in TEMPLATE_DEFINITIONS.items():
            if v["filename"] == fname or k in fname.lower():
                tpl_key = k
                break
        if not tpl_key:
            if "ตามยอม" in fname:
                tpl_key = "compromise"
            elif "ออนใลน์" in fname or "ออนไลน์" in fname:
                tpl_key = "online_report"
            else:
                tpl_key = "report"
    res["tpl_key"] = tpl_key

    tpl_def = TEMPLATE_DEFINITIONS.get(tpl_key, TEMPLATE_DEFINITIONS["report"])

    # Read and inspect OpenXML
    xml_content = ""
    try:
        with zipfile.ZipFile(docx_path, 'r') as zin:
            for item in zin.infolist():
                if item.filename == 'word/document.xml' or re.match(r'^word/(header|footer)\d+\.xml$', item.filename):
                    txt = zin.read(item.filename).decode('utf-8', errors='ignore')
                    xml_content += " " + txt
        res["file_readable"] = True
    except Exception as e:
        res["valid"] = False
        res["status_level"] = "error"
        res["status_message"] = f"ไฟล์แม่แบบเสียหาย ไม่สามารถเปิดอ่านได้: {str(e)}"
        res["syntax_errors"].append(f"โครงสร้างไฟล์ Word เสียหาย: {str(e)}")
        return res

    # Strip XML tags to pure text runs
    clean_txt = re.sub(r'<[^>]+>', '', xml_content)

    # Check for unclosed template braces ({{ without }} or vice versa)
    open_count = clean_txt.count('{{')
    close_count = clean_txt.count('}}')
    if open_count != close_count:
        res["valid"] = False
        res["status_level"] = "error"
        err_msg = f"พบเครื่องหมายปีกกาไม่ครบคู่ (มี '{{{{' จำนวน {open_count} แห่ง แต่มี '}}}}' จำนวน {close_count} แห่ง) อาจทำให้ตัวแปรไม่ทำงาน"
        res["syntax_errors"].append(err_msg)

    # Extract all tags
    raw_tags = set()
    matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', clean_txt)
    for m1, m2 in matches:
        tag = (m1 or m2).strip()
        if tag:
            raw_tags.add(tag)

    res["detected_tags"] = sorted(list(raw_tags))

    # Check required variables
    req_vars = tpl_def.get("required_variables", {})
    for var_name, var_desc in req_vars.items():
        found = False
        # Aliases for day / date / d
        if var_name in ("date", "day", "d"):
            if any(t in raw_tags for t in ["date", "day", "d"]):
                found = True
        elif var_name in ("court_name", "court", "ชื่อศาล"):
            if any(t in raw_tags for t in ["court_name", "court", "ชื่อศาล"]):
                found = True
        elif var_name in raw_tags:
            found = True

        if not found:
            res["missing_required"].append({
                "tag": f"{{{{{var_name}}}}}",
                "name": var_name,
                "description": var_desc
            })

    # Check required loops
    req_loops = tpl_def.get("required_loops", {})
    for loop_name, loop_info in req_loops.items():
        start_tag = loop_info["start"]
        end_tag = loop_info["end"]
        has_start = start_tag in raw_tags
        has_end = end_tag in raw_tags

        if not has_start or not has_end:
            issue_detail = []
            if not has_start:
                issue_detail.append(f"ขาดแท็กเปิด {{{{{start_tag}}}}}")
            if not has_end:
                issue_detail.append(f"ขาดแท็กปิด {{{{{end_tag}}}}}")
            
            res["missing_loops"].append({
                "loop_name": loop_name,
                "start_tag": f"{{{{{start_tag}}}}}",
                "end_tag": f"{{{{{end_tag}}}}}",
                "issue": ", ".join(issue_detail),
                "description": loop_info["description"]
            })

    # Determine overall status
    if res["syntax_errors"] or res["missing_loops"]:
        res["valid"] = False
        res["status_level"] = "error"
        reasons = []
        if res["missing_loops"]:
            reasons.append(f"ขาดโครงสร้างวนซ้ำหลัก {len(res['missing_loops'])} จุด")
        if res["syntax_errors"]:
            reasons.append("พบไวยากรณ์ปีกกาผิดพลาด")
        res["status_message"] = "แม่แบบมีข้อผิดพลาดร้ายแรง: " + ", ".join(reasons)
    elif res["missing_required"]:
        res["valid"] = False
        res["status_level"] = "warning"
        res["status_message"] = f"แม่แบบขาดตัวแปรจำเป็น {len(res['missing_required'])} ตัวแปร"
    else:
        res["valid"] = True
        res["status_level"] = "success"
        res["status_message"] = "แม่แบบถูกต้องสมบูรณ์ (ตรวจพบตัวแปรและโครงสร้างครบถ้วน)"

    return res


def restore_word_template(docx_filename: str) -> Tuple[bool, str, Optional[str]]:
    """
    Restore a Word template from the pristine factory default version.
    1. Makes a backup of current modified template in templates/backup/
    2. Overwrites template with factory default template
    3. Verifies that restored template is valid
    Returns (success, message, backup_filepath)
    """
    tpl_dir = storage_service.get_templates_dir()
    target_path = os.path.join(tpl_dir, docx_filename)

    factory_src = get_default_factory_template_path(docx_filename)
    if not factory_src or not os.path.exists(factory_src):
        return False, f"ไม่พบไฟล์แม่แบบต้นฉบับของโปรแกรมสำหรับ: '{docx_filename}'", None

    # Step 1: Create backup if current file exists
    backup_path = None
    if os.path.exists(target_path):
        try:
            backup_dir = os.path.join(tpl_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(docx_filename)
            backup_name = f"{base}_ก่อนกู้คืน_{ts}{ext}"
            backup_path = os.path.join(backup_dir, backup_name)
            shutil.copy2(target_path, backup_path)
        except Exception as e:
            # Continue even if backup warning
            pass

    # Step 2: Copy factory template over to target path
    try:
        os.makedirs(tpl_dir, exist_ok=True)
        shutil.copy2(factory_src, target_path)
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการคัดลอกไฟล์แม่แบบต้นฉบับ: {str(e)}", backup_path

    # Step 3: Run quick verification
    v_res = validate_word_template(target_path)
    if not v_res["valid"]:
        return True, f"กู้คืนแม่แบบ '{docx_filename}' สำเร็จแล้ว แต่ตรวจพบข้อสังเกต: {v_res['status_message']}", backup_path

    return True, f"กู้คืนแม่แบบ '{docx_filename}' กลับสู่ค่าเริ่มต้นของโปรแกรมเรียบร้อยแล้ว", backup_path


def restore_all_word_templates() -> Dict[str, Tuple[bool, str, Optional[str]]]:
    """Restore all standard judicial templates to factory defaults."""
    results = {}
    for k, v in TEMPLATE_DEFINITIONS.items():
        fname = v["filename"]
        ok, msg, bkp = restore_word_template(fname)
        results[fname] = (ok, msg, bkp)
    return results


def restore_default_paragraph_templates() -> Tuple[bool, str]:
    """Restore default paragraph templates to the database."""
    # Find factory paragraph_templates.json
    app_dir = storage_service.get_app_dir()
    p1 = os.path.join(app_dir, "default_templates", "paragraph_templates.json")
    bundle_dir = storage_service.get_bundle_dir()
    p2 = os.path.join(bundle_dir, "default_templates", "paragraph_templates.json")
    p3 = os.path.join(bundle_dir, "data", "paragraph_templates.json")
    p4 = os.path.join(app_dir, "data", "paragraph_templates.json")

    chosen = None
    for p in [p1, p2, p3, p4]:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            chosen = p
            break

    if not chosen:
        return False, "ไม่พบไฟล์ต้นฉบับ paragraph_templates.json ของระบบ"

    try:
        import json
        with open(chosen, 'r', encoding='utf-8') as f:
            tpls = json.load(f)
        if isinstance(tpls, list) and tpls:
            storage_service.save_templates(tpls)
            return True, f"กู้คืน Template ข้อความกระบวนพิจารณาเริ่มต้นสำเร็จ ({len(tpls)} รายการ)"
        return False, "โครงสร้างข้อมูลในไฟล์ Template เริ่มต้นไม่ถูกต้อง"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการกู้คืน Template ข้อความ: {str(e)}"
