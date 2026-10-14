"""
Root forwarder for docx_service ensuring 100% backward compatibility.
"""
from services.docx_service import (
    W_NS,
    FORBIDDEN_CONTROL_KEYWORDS,
    SYSTEM_RESERVED_VARIABLES,
    validate_template_variable,
    extract_and_categorize_template_variables,
    sanitize_xml_string,
    parse_attendees_list,
    format_attendees_summary,
    replace_in_nodes,
    generate_report_docx,
    generate_compromise_docx
)

__all__ = [
    "W_NS",
    "FORBIDDEN_CONTROL_KEYWORDS",
    "SYSTEM_RESERVED_VARIABLES",
    "validate_template_variable",
    "extract_and_categorize_template_variables",
    "sanitize_xml_string",
    "parse_attendees_list",
    "format_attendees_summary",
    "replace_in_nodes",
    "generate_report_docx",
    "generate_compromise_docx"
]
