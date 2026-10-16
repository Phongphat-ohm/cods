"""
CODS Docx Service - High Performance 100% Offline Word Document Generation
Performs OpenXML manipulation on template Word files (.docx) using lxml and zipfile.
Handles placeholder tags, loop blocks, attendee formatting, and XML sanitization.
100% Offline (Air-Gapped) - Zero external network interactions.
"""

import os
import re
import io
import copy
import zipfile
import uuid
from typing import Dict, Any, List, Tuple, Set
from lxml import etree
from services import storage_service

W_NS = 'http://purl.oclc.org/ooxml/wordprocessingml/main'

# Reserved control keywords for OpenXML template loops
FORBIDDEN_CONTROL_KEYWORDS: Set[str] = {
    'paragraphs', '#paragraphs', '/paragraphs',
    'signatories', '#signatories', '/signatories',
    '.', 'position'
}

# Standard system variables bound directly to court case metadata
SYSTEM_RESERVED_VARIABLES: Set[str] = {
    'case_black_no', 'case_red_no', 'court_name', 'court', 'ชื่อศาล',
    'case_type', 'hearing_purpose', 'appointment_date', 'appointment_reason', 'appointment_purpose', 'นัดมาทำไม',
    'day', 'd', 'date', 'month', 'year', 'hearing_time',
    'plaintiff_name', 'defendant_name',
    'judge_1_name', 'judge_2_name', 'judge_๑_name', 'judge_๒_name',
    'attendees_summary', 'full_date', 'case_subject', 'refund_total'
}


def validate_template_variable(var_name: str) -> Tuple[bool, str]:
    """
    Validate variable syntax and check against forbidden keywords.
    Returns (is_valid, error_message).
    """
    if not var_name or not var_name.strip():
        return False, "ชื่อตัวแปรว่างเปล่า (เช่น {{}})"
    name = var_name.strip()

    # Check loop control keywords (forbidden as custom input variable)
    clean_tag = name.lstrip('#/').strip()
    if clean_tag.lower() in {k.lower() for k in FORBIDDEN_CONTROL_KEYWORDS}:
        return False, f"คำว่า '{name}' เป็นคำสั่งสงวนโครงสร้างเอกสารของระบบ ห้ามใช้เป็นตัวแปร"

    # Check invalid characters
    invalid_chars = ['<', '>', '&', '"', "'", '/', '\\', '?', '*', ':', '|']
    for ch in invalid_chars:
        if ch in name:
            return False, f"ชื่อตัวแปร '{name}' มีอักขระต้องห้าม '{ch}' ที่อาจทำให้ไฟล์ Word เสียหาย"

    # Check spaces inside variable name
    if ' ' in name or '\t' in name or '\n' in name:
        return False, f"ชื่อตัวแปร '{name}' ห้ามมีเว้นวรรค (ควรใช้ขีดล่าง '_' เช่น '{{ข้อหา_แห่งคดี}}')"

    # Check basic character validity (Thai, English, numbers, underscore)
    if not re.match(r'^[a-zA-Z0-9_\u0E00-\u0E7F]+$', name):
        return False, f"ชื่อตัวแปร '{name}' มีรูปแบบอักขระที่ไม่ถูกต้อง"

    return True, ""


def extract_and_categorize_template_variables(docx_path: str) -> Dict[str, Any]:
    """
    Scan an OpenXML .docx template and categorize all detected variables:
    - custom_variables: variables requiring dynamic user inputs
    - system_variables: built-in variables automatically filled from case data
    - errors: validation errors for forbidden keywords or invalid syntax
    """
    result: Dict[str, Any] = {
        'custom_variables': [],
        'system_variables': [],
        'errors': []
    }
    if not os.path.exists(docx_path):
        return result

    raw_tags = set()
    try:
        with zipfile.ZipFile(docx_path, 'r') as zin:
            for item in zin.infolist():
                if item.filename == 'word/document.xml' or re.match(r'^word/(header|footer)\d+\.xml$', item.filename):
                    txt = zin.read(item.filename).decode('utf-8', errors='ignore')
                    # Strip XML tags to get pure text runs
                    clean_txt = re.sub(r'<[^>]+>', '', txt)
                    # Search for {{...}} and {...}
                    matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', clean_txt)
                    for m1, m2 in matches:
                        tag = (m1 or m2).strip()
                        if tag:
                            raw_tags.add(tag)
    except Exception as e:
        result['errors'].append(f"ไม่สามารถอ่านไฟล์แม่แบบได้: {str(e)}")
        return result

    for tag in sorted(list(raw_tags)):
        # Skip loop control tags
        clean_tag = tag.lstrip('#/').strip()
        if clean_tag in FORBIDDEN_CONTROL_KEYWORDS:
            continue

        # Check if it's a known system variable
        if clean_tag in SYSTEM_RESERVED_VARIABLES:
            if clean_tag not in result['system_variables']:
                result['system_variables'].append(clean_tag)
            continue

        # Validate custom variable
        is_valid, err_msg = validate_template_variable(clean_tag)
        if is_valid:
            if clean_tag not in result['custom_variables']:
                result['custom_variables'].append(clean_tag)
        else:
            result['errors'].append(err_msg)

    return result


def sanitize_xml_string(val: Any) -> str:
    """
    Remove illegal XML 1.0 control characters and convert None to empty string.
    Prevents lxml ValueError on invalid characters.
    """
    if val is None:
        return ""
    s = str(val)
    # Strip illegal XML 1.0 control characters: \x00-\x08, \x0b, \x0c, \x0e-\x1f
    clean_s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)
    return clean_s


def parse_attendees_list(input_val: Any) -> List[str]:
    """Parse various attendee inputs into a clean list of position titles."""
    if isinstance(input_val, list):
        res = []
        for x in input_val:
            if isinstance(x, dict) and 'position' in x:
                val = str(x['position']).strip()
            else:
                val = str(x).strip()
            val = re.sub(r'^และ\s*', '', val).strip()
            if val:
                res.append(val)
        return res
    if isinstance(input_val, str) and input_val.strip():
        txt = input_val.strip()
        parts = re.split(r'[,+\n]+', txt) if (',' in txt or '\n' in txt) else txt.split()
        return [re.sub(r'^และ\s*', '', p).strip() for p in parts if p.strip()]
    return []


def format_attendees_summary(positions: List[str]) -> str:
    """
    Format a list of attendee roles into official Thai court grammatical summary.
    Examples:
      ['โจทก์'] -> 'โจทก์'
      ['โจทก์', 'จำเลย'] -> 'โจทก์ และจำเลย'
      ['โจทก์', 'ทนายโจทก์', 'จำเลย'] -> 'โจทก์ ทนายโจทก์ และจำเลย'
    """
    cleaned = [p.strip() for p in positions if p.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return f"{' '.join(cleaned[:-1])} และ{cleaned[-1]}"


def replace_in_nodes(t_nodes: List[Any], replacements: Dict[str, Any]):
    """
    Safely replace placeholder tags ({tag} or {{tag}} or {{ tag }}) across text runs (w:t elements)
    without corrupting XML tags or document structure, resolving run-splitting in Word.
    """
    full_text = ''.join(t.text or '' for t in t_nodes)
    if not full_text:
        return

    char_map = []
    for node_idx, t in enumerate(t_nodes):
        txt = t.text or ''
        for char_idx in range(len(txt)):
            char_map.append((node_idx, char_idx))

    matches = list(re.finditer(r'\{{1,2}\s*([a-zA-Z0-9_\u0E00-\u0E7F.]+)\s*\}{1,2}', full_text))
    if not matches:
        return

    # Process matches in reverse to maintain indexing
    for m in reversed(matches):
        tag = m.group(1).strip()
        if tag in replacements:
            val = sanitize_xml_string(replacements[tag])
            start, end = m.start(), m.end()
            start_node_idx, start_char_idx = char_map[start]
            end_node_idx, end_char_idx = char_map[end - 1]

            if start_node_idx == end_node_idx:
                node = t_nodes[start_node_idx]
                curr_text = node.text or ''
                node.text = curr_text[:start_char_idx] + val + curr_text[end_char_idx + 1:]
            else:
                s_node = t_nodes[start_node_idx]
                s_text = s_node.text or ''
                s_node.text = s_text[:start_char_idx] + val

                for mid_idx in range(start_node_idx + 1, end_node_idx):
                    t_nodes[mid_idx].text = ''

                e_node = t_nodes[end_node_idx]
                e_text = e_node.text or ''
                e_node.text = e_text[end_char_idx + 1:]


def generate_report_docx(template_path: str, output_path: str, data: Dict[str, Any]) -> str:
    """
    Generate a complete judicial report Word document (.docx) from a template.
    Replaces tags, dynamic paragraphs loop, signatories loop, and bench judge markers.
    Performs atomic file writing and raises clear error messages if target file is locked.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Build context dictionary with both Arabic and Thai numeral aliases
    context: Dict[str, Any] = {}
    for k, v in data.items():
        val_clean = sanitize_xml_string(v)
        context[k] = val_clean

        # Add Thai numeral tag aliases
        k_thai = k.replace('1', '๑').replace('2', '๒')
        context[k_thai] = val_clean

    # Court name fallback and normalization to prevent duplicate 'ศาลศาล...'
    court_raw = sanitize_xml_string(data.get('court_name') or storage_service.get_default_court_name() or '').strip()
    clean_court = re.sub(r'^ศาล\s*', '', court_raw) if court_raw.startswith('ศาล') else court_raw
    context['court_name'] = clean_court
    context['court'] = clean_court
    context['ชื่อศาล'] = clean_court

    j1 = sanitize_xml_string(data.get('judge_1_name', ''))
    j2 = sanitize_xml_string(data.get('judge_2_name', ''))

    paras = data.get('paragraphs', [])
    if not isinstance(paras, list):
        paras = [str(paras)] if paras else []
    paras = [sanitize_xml_string(p) for p in paras if sanitize_xml_string(p).strip()]

    sigs = parse_attendees_list(data.get('signatories', []))
    formatted_sigs = [re.sub(r'^และ\s*', '', s).strip() for s in sigs if s.strip()]

    # Process docx package in memory
    zout_buf = io.BytesIO()

    with zipfile.ZipFile(template_path, 'r') as zin, zipfile.ZipFile(zout_buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            buf = zin.read(item.filename)

            # Target main document and any headers/footers
            if item.filename == 'word/document.xml' or re.match(r'^word/(header|footer)\d+\.xml$', item.filename):
                root = etree.fromstring(buf)
                w_ns = root.nsmap.get('w', W_NS)
                body = root.find(f'{{{w_ns}}}body')
                if body is None:
                    for child in root:
                        if child.tag.endswith('}body'):
                            body = child
                            break

                if body is not None and item.filename == 'word/document.xml':
                    # 1. Handle paragraphs loop: {#paragraphs} ... {{.}} ... {/paragraphs}
                    cur_body = list(body)
                    p_loop_start = None
                    p_loop_end = None
                    for idx, ch in enumerate(cur_body):
                        txt = ''.join(ch.itertext())
                        if '{#paragraphs}' in txt or '{{#paragraphs}}' in txt:
                            p_loop_start = idx
                        elif '{/paragraphs}' in txt or '{{/paragraphs}}' in txt:
                            p_loop_end = idx
                            break

                    if p_loop_start is not None and p_loop_end is not None and p_loop_end >= p_loop_start:
                        loop_elems = cur_body[p_loop_start : p_loop_end + 1]
                        insert_idx = list(body).index(loop_elems[0])

                        # Template paragraph is between loop markers (if any)
                        template_p = loop_elems[1] if len(loop_elems) >= 3 else None

                        for elem in loop_elems:
                            body.remove(elem)

                        if paras and template_p is not None:
                            for p_text in paras:
                                new_p = copy.deepcopy(template_p)
                                t_nodes = [t for t in new_p.iter() if t.tag.endswith('}t')]
                                replace_in_nodes(t_nodes, {'.': p_text})
                                body.insert(insert_idx, new_p)
                                insert_idx += 1

                    # 2. Handle signatories loop: {#signatories} ... {position} ... {/signatories}
                    cur_body = list(body)
                    sig_loop_start = None
                    sig_loop_end = None
                    for idx, ch in enumerate(cur_body):
                        txt = ''.join(ch.itertext())
                        if '{#signatories}' in txt or '{{#signatories}}' in txt:
                            sig_loop_start = idx
                        elif '{/signatories}' in txt or '{{/signatories}}' in txt:
                            sig_loop_end = idx
                            break

                    if sig_loop_start is not None and sig_loop_end is not None and sig_loop_end >= sig_loop_start:
                        loop_elems = cur_body[sig_loop_start : sig_loop_end + 1]
                        template_sig_p = loop_elems[1] if len(loop_elems) >= 3 else None
                        insert_idx = list(body).index(loop_elems[0])

                        # Remove blank paragraph preceding signatories loop if present
                        if insert_idx > 0:
                            prev_elem = body[insert_idx - 1]
                            if prev_elem.tag.endswith('}p') and not ''.join(prev_elem.itertext()).strip():
                                body.remove(prev_elem)
                                insert_idx -= 1

                        for elem in loop_elems:
                            body.remove(elem)

                        if formatted_sigs and template_sig_p is not None:
                            for pos in formatted_sigs:
                                new_sig_p = copy.deepcopy(template_sig_p)
                                t_nodes = [t for t in new_sig_p.iter() if t.tag.endswith('}t')]
                                replace_in_nodes(t_nodes, {'position': pos})
                                body.insert(insert_idx, new_sig_p)
                                insert_idx += 1

                    # 3. Handle judge 2 removal / replacement (Bookmark id="2" or tag)
                    for p in [p for p in root.iter() if p.tag.endswith('}p')]:
                        txt = ''.join(p.itertext())
                        if 'judge_2_name' in txt or 'judge_๒_name' in txt:
                            if not j2:
                                children = list(p)
                                bm_start_idx = None
                                bm_end_idx = None
                                for c_idx, c in enumerate(children):
                                    if c.tag.endswith('}bookmarkStart') and any(k.endswith('}id') and v == '2' for k, v in c.attrib.items()):
                                        bm_start_idx = c_idx
                                    elif c.tag.endswith('}bookmarkEnd') and any(k.endswith('}id') and v == '2' for k, v in c.attrib.items()):
                                        bm_end_idx = c_idx
                                if bm_start_idx is not None and bm_end_idx is not None:
                                    for c in children[bm_start_idx + 1 : bm_end_idx]:
                                        p.remove(c)
                                else:
                                    t_nodes = [t for t in p.iter() if t.tag.endswith('}t')]
                                    replace_in_nodes(t_nodes, {'judge_2_name': '', 'judge_๒_name': ''})
                            else:
                                t_nodes = [t for t in p.iter() if t.tag.endswith('}t')]
                                replace_in_nodes(t_nodes, {'judge_2_name': j2, 'judge_๒_name': j2})

                        # Ensure no tab immediately precedes บันทึก/อ่าน to keep "(ชื่อผู้พิพากษา) บันทึก/อ่าน" close together
                        if 'บันทึก' in txt:
                            runs = [r for r in p if r.tag.endswith('}r')]
                            for r_idx, r in enumerate(runs):
                                if any(ch.tag.endswith('}tab') for ch in r):
                                    next_txt = ''.join([''.join(sub_r.itertext()) for sub_r in runs[r_idx+1:]]).strip()
                                    if next_txt.startswith('บันทึก'):
                                        p.remove(r)

                # 4. Replace simple tags across all paragraphs in document or header/footer
                for p in [p for p in root.iter() if p.tag.endswith('}p')]:
                    txt = ''.join(p.itertext())
                    if '{' in txt:
                        t_nodes = [t for t in p.iter() if t.tag.endswith('}t')]
                        replace_in_nodes(t_nodes, context)

                buf = etree.tostring(root, xml_declaration=True, encoding='utf-8', standalone=True)

            zout.writestr(item.filename, buf)

    # Atomic write to target file with PermissionError handling
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    temp_out = f"{output_path}.tmp_{uuid.uuid4().hex[:6]}"
    try:
        with open(temp_out, 'wb') as f:
            f.write(zout_buf.getvalue())
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_out, output_path)
    except PermissionError:
        if os.path.exists(temp_out):
            try:
                os.remove(temp_out)
            except OSError:
                pass
        raise PermissionError(
            f"ไม่สามารถบันทึกไฟล์ได้เนื่องจากไฟล์ปลายทางกำลังถูกเปิดใช้งานอยู่:\n{output_path}\n\n"
            f"กรุณาปิดโปรแกรม Microsoft Word ที่เปิดไฟล์นี้อยู่ แล้วลองกดบันทึกใหม่อีกครั้ง"
        )
    except Exception as e:
        if os.path.exists(temp_out):
            try:
                os.remove(temp_out)
            except OSError:
                pass
        raise e

    return output_path


def generate_compromise_docx(template_path: str, output_path: str, data: Dict[str, Any]) -> str:
    """
    Generate a complete judicial compromise judgment document (.docx) from template (e.g. คำพิพากษาตามยอม.docx).
    Replaces all variables: case_black_no, case_red_no, court_name, case_type, case_subject,
    plaintiff_name, defendant_name, d, month, year, full_date, refund_total, judge_1_name, judge_2_name.
    Cleans up any leftover artifacts from the template.
    Removes judge 2 row if judge_2_name is empty.
    Atomic file writing with lock checking.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Build context dictionary
    context: Dict[str, Any] = {}
    for k, v in data.items():
        val_clean = sanitize_xml_string(v)
        context[k] = val_clean
        # Add Thai numeral tag aliases
        k_thai = k.replace('1', '๑').replace('2', '๒')
        context[k_thai] = val_clean

    # Court name fallback and normalization to prevent duplicate 'ศาลศาล...'
    court_raw = sanitize_xml_string(data.get('court_name') or storage_service.get_default_court_name() or '').strip()
    clean_court = re.sub(r'^ศาล\s*', '', court_raw) if court_raw.startswith('ศาล') else court_raw
    context['court_name'] = clean_court
    context['court'] = clean_court
    context['ชื่อศาล'] = clean_court

    # Aliases for day / date
    d_val = sanitize_xml_string(data.get('d') or data.get('day') or data.get('date') or '')
    context['d'] = d_val
    context['day'] = d_val
    context['date'] = d_val

    # Format full_date: e.g. "17 กันยายน 2569"
    full_d = sanitize_xml_string(data.get('full_date', '')).strip()
    if not full_d:
        d_p = d_val
        m_p = sanitize_xml_string(data.get('month', '')).strip()
        y_p = sanitize_xml_string(data.get('year', '')).strip()
        parts = [p for p in [d_p, m_p, y_p] if p]
        full_d = " ".join(parts)
    clean_full_d = re.sub(r'^วันที่\s*', '', full_d).strip() if full_d.startswith('วันที่') else full_d
    context['full_date'] = clean_full_d

    j1 = sanitize_xml_string(data.get('judge_1_name', ''))
    j2 = sanitize_xml_string(data.get('judge_2_name', ''))

    zout_buf = io.BytesIO()

    with zipfile.ZipFile(template_path, 'r') as zin, zipfile.ZipFile(zout_buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            buf = zin.read(item.filename)

            if item.filename == 'word/document.xml' or re.match(r'^word/(header|footer)\d+\.xml$', item.filename):
                root = etree.fromstring(buf)

                # Pre-replacement: Handle judge 2 signature line removal if no judge 2
                if item.filename == 'word/document.xml' and not j2:
                    for tbl in root.iter():
                        if tbl.tag.endswith('}tbl'):
                            trs = [r for r in tbl.iter() if r.tag.endswith('}tr')]
                            for r in trs:
                                r_txt = ''.join(r.itertext())
                                if 'judge_2_name' in r_txt or 'judge_๒_name' in r_txt or ('ผู้พิพากษา' in r_txt and j1 and j1 not in r_txt):
                                    parent = r.getparent()
                                    if parent is not None:
                                        parent.remove(r)

                # Process paragraphs and text elements
                for p in root.iter():
                    if p.tag.endswith('}p'):
                        t_nodes = [t for t in p.iter() if t.tag.endswith('}t')]
                        if t_nodes:
                            replace_in_nodes(t_nodes, context)

                # Post-replacement cleanup for leftover template artifacts in document.xml
                if item.filename == 'word/document.xml':
                    for p in root.iter():
                        if p.tag.endswith('}p'):
                            t_nodes = [t for t in p.iter() if t.tag.endswith('}t')]
                            for t in t_nodes:
                                if t.text:
                                    # Clean up trailing ' ย' after month if any
                                    if ' ย' in t.text and data.get('month'):
                                        t.text = t.text.replace(' ย', '')
                                    # Clean up FORMTEXT if present
                                    if 'FORMTEXT' in t.text:
                                        t.text = t.text.replace('FORMTEXT', '')

                buf = etree.tostring(root, xml_declaration=True, encoding='utf-8', standalone=True)

            zout.writestr(item.filename, buf)

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    temp_out = f"{output_path}.tmp_{uuid.uuid4().hex[:6]}"
    try:
        with open(temp_out, 'wb') as f:
            f.write(zout_buf.getvalue())
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_out, output_path)
    except PermissionError:
        if os.path.exists(temp_out):
            try:
                os.remove(temp_out)
            except OSError:
                pass
        raise PermissionError(
            f"ไม่สามารถบันทึกไฟล์ได้เนื่องจากไฟล์ปลายทางกำลังถูกเปิดใช้งานอยู่:\n{output_path}\n\n"
            f"กรุณาปิดโปรแกรม Microsoft Word ที่เปิดไฟล์นี้อยู่ แล้วลองกดบันทึกใหม่อีกครั้ง"
        )
    except Exception as e:
        if os.path.exists(temp_out):
            try:
                os.remove(temp_out)
            except OSError:
                pass
        raise e

    return output_path

