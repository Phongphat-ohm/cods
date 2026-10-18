"""
CODS Template Variable Service
Handles typed template variables, input types (date, time, number, select, text),
and rich Thai date formatting (full, short, numeric, court official, day-month, weekday).
100% Offline, no external dependencies beyond standard library & PySide6.
"""

import re
import datetime
from typing import Dict, Any, List, Tuple, Optional, Set

# Standard Thai Months
THAI_MONTHS = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
]

THAI_SHORT_MONTHS = [
    'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
    'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
]

THAI_DAYS_OF_WEEK = [
    'วันจันทร์', 'วันอังคาร', 'วันพุธ', 'วันพฤหัสบดี', 'วันศุกร์', 'วันเสาร์', 'วันอาทิตย์'
]

# Mapping short month string to month index (1-12)
MONTH_MAPPING = {
    'มกราคม': 1, 'ม.ค.': 1, 'ม.ค': 1, 'มค': 1,
    'กุมภาพันธ์': 2, 'ก.พ.': 2, 'ก.พ': 2, 'กพ': 2,
    'มีนาคม': 3, 'มี.ค.': 3, 'มี.ค': 3, 'มีค': 3,
    'เมษายน': 4, 'เม.ย.': 4, 'เม.ย': 4, 'เมย': 4,
    'พฤษภาคม': 5, 'พ.ค.': 5, 'พ.ค': 5, 'พค': 5,
    'มิถุนายน': 6, 'มิ.ย.': 6, 'มิ.ย': 6, 'มิย': 6,
    'กรกฎาคม': 7, 'ก.ค.': 7, 'ก.ค': 7, 'กค': 7,
    'สิงหาคม': 8, 'ส.ค.': 8, 'ส.ค': 8, 'สค': 8,
    'กันยายน': 9, 'ก.ย.': 9, 'ก.ย': 9, 'กย': 9,
    'ตุลาคม': 10, 'ต.ค.': 10, 'ต.ค': 10, 'ตค': 10,
    'พฤศจิกายน': 11, 'พ.ย.': 11, 'พ.ย': 11, 'พย': 11,
    'ธันวาคม': 12, 'ธ.ค.': 12, 'ธ.ค': 12, 'ธค': 12
}

# Supported Date Format Styles with descriptions & sample previews
DATE_FORMAT_STYLES = {
    'full': {
        'id': 'full',
        'label': 'แบบเต็ม',
        'aliases': ['full', 'เต็ม', 'แบบเต็ม', 'date_full'],
        'example': '18 ตุลาคม 2569',
        'desc': 'วัน เดือนปีภาษาไทยแบบเต็ม (เช่น 18 ตุลาคม 2569)'
    },
    'short': {
        'id': 'short',
        'label': 'แบบย่อ',
        'aliases': ['short', 'ย่อ', 'แบบย่อ', 'date_short'],
        'example': '18 ต.ค. 2569',
        'desc': 'วัน เดือนย่อ ปี พ.ศ. เต็ม (เช่น 18 ต.ค. 2569)'
    },
    'numeric': {
        'id': 'numeric',
        'label': 'แบบตัวเลข',
        'aliases': ['numeric', 'number', 'ตัวเลข', 'แบบตัวเลข', 'date_num'],
        'example': '18/10/2569',
        'desc': 'ตัวเลข วัน/เดือน/ปี พ.ศ. (เช่น 18/10/2569)'
    },
    'court': {
        'id': 'court',
        'label': 'แบบทางการศาล',
        'aliases': ['court', 'ทางการ', 'แบบทางการ', 'ราชการ', 'date_court'],
        'example': 'วันที่ 18 เดือน ตุลาคม พ.ศ. 2569',
        'desc': 'รูปแบบทางการสำนวนศาล (เช่น วันที่ 18 เดือน ตุลาคม พ.ศ. 2569)'
    },
    'court_short': {
        'id': 'court_short',
        'label': 'แบบทางการย่อ',
        'aliases': ['court_short', 'ทางการย่อ'],
        'example': 'วันที่ 18 ต.ค. 2569',
        'desc': 'มีคำว่า วันที่ นำหน้า พร้อมเดือนย่อ (เช่น วันที่ 18 ต.ค. 2569)'
    },
    'day_month': {
        'id': 'day_month',
        'label': 'วันและเดือน',
        'aliases': ['day_month', 'วันเดือน', 'วันและเดือน'],
        'example': '18 ตุลาคม',
        'desc': 'เฉพาะวันและเดือนเต็ม (เช่น 18 ตุลาคม)'
    },
    'day_month_short': {
        'id': 'day_month_short',
        'label': 'วันและเดือนย่อ',
        'aliases': ['day_month_short', 'วันเดือนย่อ'],
        'example': '18 ต.ค.',
        'desc': 'เฉพาะวันและเดือนย่อ (เช่น 18 ต.ค.)'
    },
    'weekday_full': {
        'id': 'weekday_full',
        'label': 'มีชื่อวันในสัปดาห์',
        'aliases': ['weekday', 'weekday_full', 'วันในสัปดาห์'],
        'example': 'วันอาทิตย์ที่ 18 ตุลาคม 2569',
        'desc': 'ระบุชื่อวันในสัปดาห์ด้วย (เช่น วันอาทิตย์ที่ 18 ตุลาคม 2569)'
    },
    'short_year': {
        'id': 'short_year',
        'label': 'แบบย่อ 2 หลัก',
        'aliases': ['short_year', 'ย่อสองหลัก', 'พศย่อ'],
        'example': '18 ต.ค. 69',
        'desc': 'เดือนย่อ ปี พ.ศ. 2 หลัก (เช่น 18 ต.ค. 69)'
    }
}

# Canonical Type Definitions
INPUT_TYPES = {
    'date': {
        'id': 'date',
        'label': 'วันที่',
        'icon': 'calendar',
        'aliases': ['date', 'วันที่', 'วันนัด', 'วัน', 'appointment_date']
    },
    'time': {
        'id': 'time',
        'label': 'เวลา',
        'icon': 'clock',
        'aliases': ['time', 'เวลา', 'เวลานัด', 'นาฬิกา']
    },
    'number': {
        'id': 'number',
        'label': 'ตัวเลข / จำนวนเงิน',
        'icon': 'hash',
        'aliases': ['number', 'currency', 'money', 'ตัวเลข', 'จำนวนเงิน', 'เงิน', 'บาท', 'ยอดเงิน', 'ราคา']
    },
    'select': {
        'id': 'select',
        'label': 'ตัวเลือกรายการ',
        'icon': 'list',
        'aliases': ['select', 'dropdown', 'choice', 'ตัวเลือก', 'เลือก', 'รายการ']
    },
    'textarea': {
        'id': 'textarea',
        'label': 'ข้อความยาว',
        'icon': 'file-text',
        'aliases': ['textarea', 'ข้อความยาว', 'หลายบรรทัด']
    },
    'text': {
        'id': 'text',
        'label': 'ข้อความทั่วไป',
        'icon': 'type',
        'aliases': ['text', 'string', 'ข้อความ', 'ทั่วไป']
    }
}


def normalize_input_type(raw_type: str) -> str:
    """Normalize input type string (Thai or English) to standard key."""
    if not raw_type:
        return 'text'
    clean = raw_type.strip().lower()
    for type_id, meta in INPUT_TYPES.items():
        if clean == type_id or clean in [a.lower() for a in meta['aliases']]:
            return type_id
    return 'text'


def normalize_date_format_style(raw_style: str) -> str:
    """Normalize date format style string (Thai or English) to standard key."""
    if not raw_style:
        return 'full'
    clean = raw_style.strip().lower()
    for style_id, meta in DATE_FORMAT_STYLES.items():
        if clean == style_id or clean in [a.lower() for a in meta['aliases']]:
            return style_id
    return 'full'


def infer_variable_type(var_name: str) -> Tuple[str, str]:
    """
    Intelligently infer input type and default format style from variable name.
    Returns (var_type, format_style).
    """
    if not var_name:
        return 'text', ''

    name_lower = var_name.lower().strip()

    # Date heuristics
    date_keywords = ['วัน', 'วันที่', 'date', 'นัด']
    # Exclude if it's purely time (e.g. เวลานัด)
    if 'เวลา' in name_lower or 'time' in name_lower or 'นาฬิกา' in name_lower:
        return 'time', 'court'

    if any(k in name_lower for k in date_keywords):
        return 'date', 'full'

    # Number / Currency heuristics
    number_keywords = ['เงิน', 'บาท', 'จำนวน', 'ยอด', 'ราคา', 'ทุนทรัพย์', 'amount', 'price', 'fee', 'cost', 'ดอกเบี้ย']
    if any(k in name_lower for k in number_keywords):
        return 'number', 'currency'

    return 'text', ''


def parse_variable_tag(raw_tag: str) -> Dict[str, Any]:
    """
    Parse a template variable tag which may contain type & format annotations.
    Formats supported:
      - "วันนัด" -> {name: "วันนัด", type: "date", format_style: "full", ...}
      - "วันนัด:date" -> {name: "วันนัด", type: "date", format_style: "full", ...}
      - "วันนัด:date:short" -> {name: "วันนัด", type: "date", format_style: "short", ...}
      - "วันนัด:วันที่:ย่อ" -> {name: "วันนัด", type: "date", format_style: "short", ...}
      - "ผลการเจรจา:select:เลื่อนนัด,ไกล่เกลี่ยสำเร็จ,สืบพยาน" -> {name: "ผลการเจรจา", type: "select", options: [...], ...}
      - "จำนวนเงิน:number" -> {name: "จำนวนเงิน", type: "number", ...}
    """
    clean_tag = raw_tag.strip().lstrip('#/').strip()
    clean_tag = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', clean_tag).strip()

    parts = [p.strip() for p in clean_tag.split(':') if p.strip()]
    if not parts:
        return {
            'raw_tag': raw_tag,
            'name': '',
            'type': 'text',
            'format_style': '',
            'options': [],
            'display_label': '',
            'display_type_label': 'ข้อความ'
        }

    var_name = parts[0]

    # Explicit type given or inferred
    if len(parts) >= 2:
        explicit_type = normalize_input_type(parts[1])
        format_or_options = ':'.join(parts[2:]) if len(parts) >= 3 else ''
    else:
        explicit_type, format_or_options = infer_variable_type(var_name)

    options = []
    format_style = ''

    if explicit_type == 'date':
        format_style = normalize_date_format_style(format_or_options)
        style_meta = DATE_FORMAT_STYLES.get(format_style, DATE_FORMAT_STYLES['full'])
        display_type_label = f"วันที่ ({style_meta['label']})"
    elif explicit_type == 'time':
        format_style = format_or_options if format_or_options else 'court'
        display_type_label = "เวลา"
    elif explicit_type == 'number':
        format_style = format_or_options if format_or_options else 'currency'
        display_type_label = "ตัวเลข / จำนวนเงิน"
    elif explicit_type == 'select':
        if format_or_options:
            options = [opt.strip() for opt in re.split(r'[,|]+', format_or_options) if opt.strip()]
        display_type_label = f"ตัวเลือก ({len(options)} รายการ)" if options else "ตัวเลือก"
    elif explicit_type == 'textarea':
        display_type_label = "ข้อความยาว"
    else:
        display_type_label = "ข้อความ"

    return {
        'raw_tag': raw_tag,
        'name': var_name,
        'type': explicit_type,
        'format_style': format_style,
        'options': options,
        'display_label': var_name,
        'display_type_label': display_type_label
    }


def parse_date_to_dmy(val: Any) -> Optional[Tuple[int, int, int, int]]:
    """
    Parse any date value into (day, month, be_year, weekday_index_0_to_6).
    be_year is Buddhist Era year (e.g. 2569).
    Returns None if parsing fails.
    """
    if val is None:
        return None

    # 1. datetime / date object or QDate
    if hasattr(val, 'day') and hasattr(val, 'month') and hasattr(val, 'year'):
        d = val.day() if callable(val.day) else val.day
        m = val.month() if callable(val.month) else val.month
        y = val.year() if callable(val.year) else val.year
        # Handle QDate / Python date
        if hasattr(val, 'weekday'):
            w = val.weekday() if callable(val.weekday) else val.weekday
        elif hasattr(val, 'dayOfWeek'):
            dow = val.dayOfWeek() if callable(val.dayOfWeek) else val.dayOfWeek
            w = (dow - 1) % 7
        else:
            try:
                w = datetime.date(y, m, d).weekday()
            except Exception:
                w = 0
        be_y = y + 543 if y < 2400 else y
        return d, m, be_y, w

    s = str(val).strip()
    if not s or s in ['-', 'N/A', 'None']:
        return None

    # Clean prefixes like "วันที่", "วัน"
    s_clean = re.sub(r'^(วัน\w+ที่|วันที่|วัน)\s*', '', s).strip()
    s_clean = re.sub(r'(เวลา)?\s*\d{1,2}[:.]\d{2}.*$', '', s_clean).strip()

    # Check for Thai month name in string
    found_m = None
    for m_name, m_idx in MONTH_MAPPING.items():
        if m_name in s_clean:
            found_m = m_idx
            # Remove the month name so digits are clean
            s_clean = s_clean.replace(m_name, ' ').strip()
            break

    # Extract all numbers from remainder
    numbers = [int(n) for n in re.findall(r'\d+', s_clean)]

    if found_m is not None:
        m = found_m
        d = 1
        be_y = datetime.datetime.now().year + 543
        for n in numbers:
            if n > 1000:
                be_y = n if n >= 2400 else n + 543
            elif n > 31 and n < 100:
                # 2-digit BE year (e.g. 69 -> 2569)
                be_y = 2500 + n
            elif 1 <= n <= 31:
                d = n
            elif not d:
                d = n
        try:
            ce_y = be_y - 543 if be_y >= 2400 else be_y
            w = datetime.date(ce_y, m, d).weekday()
        except Exception:
            w = 0
        return d, m, be_y, w

    # Pure numeric formats: YYYY-MM-DD or DD/MM/YYYY
    if len(numbers) >= 3:
        n0, n1, n2 = numbers[0], numbers[1], numbers[2]
        if n0 > 1000:
            # YYYY-MM-DD
            ce_y = n0 if n0 < 2400 else n0 - 543
            be_y = n0 if n0 >= 2400 else n0 + 543
            m = max(1, min(12, n1))
            d = max(1, min(31, n2))
        else:
            # DD/MM/YYYY
            d = max(1, min(31, n0))
            m = max(1, min(12, n1))
            if n2 > 1000:
                be_y = n2 if n2 >= 2400 else n2 + 543
                ce_y = n2 if n2 < 2400 else n2 - 543
            elif n2 < 100:
                be_y = 2500 + n2
                ce_y = be_y - 543
            else:
                be_y = n2
                ce_y = n2
        try:
            w = datetime.date(ce_y, m, d).weekday()
        except Exception:
            w = 0
        return d, m, be_y, w

    return None


def format_thai_date_by_style(date_val: Any, format_style: str = 'full') -> str:
    """
    Format a date value into the specified Thai date format style.
    Styles supported:
      - 'full': 18 ตุลาคม 2569
      - 'short': 18 ต.ค. 2569
      - 'numeric': 18/10/2569
      - 'court': วันที่ 18 เดือน ตุลาคม พ.ศ. 2569
      - 'court_short': วันที่ 18 ต.ค. 2569
      - 'day_month': 18 ตุลาคม
      - 'day_month_short': 18 ต.ค.
      - 'weekday_full': วันอาทิตย์ที่ 18 ตุลาคม 2569
      - 'short_year': 18 ต.ค. 69
    """
    parsed = parse_date_to_dmy(date_val)
    if not parsed:
        return str(date_val) if date_val is not None else ""

    d, m, be_y, w = parsed
    style_key = normalize_date_format_style(format_style)

    full_m = THAI_MONTHS[m - 1]
    short_m = THAI_SHORT_MONTHS[m - 1]
    short_y = str(be_y)[-2:] if len(str(be_y)) >= 2 else str(be_y)
    weekday_name = THAI_DAYS_OF_WEEK[w] if 0 <= w < len(THAI_DAYS_OF_WEEK) else ""

    if style_key == 'full':
        return f"{d} {full_m} {be_y}"
    elif style_key == 'short':
        return f"{d} {short_m} {be_y}"
    elif style_key == 'numeric':
        return f"{d:02d}/{m:02d}/{be_y}"
    elif style_key == 'court':
        return f"วันที่ {d} เดือน {full_m} พ.ศ. {be_y}"
    elif style_key == 'court_short':
        return f"วันที่ {d} {short_m} {be_y}"
    elif style_key == 'day_month':
        return f"{d} {full_m}"
    elif style_key == 'day_month_short':
        return f"{d} {short_m}"
    elif style_key == 'weekday_full':
        return f"{weekday_name}ที่ {d} {full_m} {be_y}"
    elif style_key == 'short_year':
        return f"{d} {short_m} {short_y}"
    else:
        return f"{d} {full_m} {be_y}"


def format_number_comma(val: Any) -> str:
    """
    Format numeric values or currency amounts with comma thousands separators (e.g. 1000000 -> 1,000,000).
    Handles integers, floats, existing commas, negative numbers, and Thai suffixes (e.g. '50000 บาท' -> '50,000 บาท').
    """
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    m = re.match(r'^([+-]?)([\d,]+)(\.\d+)?(\s*.*)$', s)
    if not m:
        return s
    sign, int_part, dec_part, suffix = m.groups()
    clean_int = int_part.replace(',', '')
    if not clean_int.isdigit():
        return s
    formatted_int = f"{int(clean_int):,}"
    formatted_dec = dec_part if dec_part else ""
    return f"{sign}{formatted_int}{formatted_dec}{suffix}"


def get_variable_replace_pattern(var_name: str) -> re.Pattern:
    """
    Build a regex pattern to match a template variable token in all its bracket/type variants.
    e.g. matching [วันนัด], [วันนัด:date:full], {{วันนัด}}, {{วันนัด:วันที่:ย่อ}}, {วันนัด}.
    """
    esc = re.escape(var_name)
    return re.compile(
        rf'\[\s*(?:\U0001f3f7\ufe0f)?\s*{esc}(?::[^\]\n]+)?\s*\]|'
        rf'\{{\{{\s*{esc}(?::[^}}\n]+)?\s*\}}\}}|'
        rf'\{{\s*{esc}(?::[^{{\}}\n]+)?\s*\}}'
    )


def extract_variables_with_meta(text: str) -> List[Dict[str, Any]]:
    """
    Extract all template variables found in text along with their parsed metadata.
    """
    if not text:
        return []

    matches = re.findall(
        r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]\n]+?)\s*\]|\{\{\s*([^}\n]+?)\s*\}\}|\{([^{}\n]+?)\}',
        text
    )
    result = []
    seen = set()

    for m1, m2, m3 in matches:
        raw_tag = (m1 or m2 or m3).strip()
        raw_tag = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', raw_tag).strip()
        if not raw_tag or raw_tag.startswith(('#', '/')):
            continue

        meta = parse_variable_tag(raw_tag)
        if meta['name'] and meta['name'] not in seen:
            seen.add(meta['name'])
            result.append(meta)

    return result
