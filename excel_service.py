"""
Root forwarder for excel_service ensuring 100% backward compatibility.
"""
from services.excel_service import (
    COMMON_HEADERS,
    SEQUENCE_NAMES,
    HEADER_KEYWORDS,
    THAI_MONTHS,
    THAI_SHORT_MONTHS,
    guess_column_mapping,
    read_excel_data,
    to_full_buddhist_year,
    format_thai_date
)

__all__ = [
    "COMMON_HEADERS",
    "SEQUENCE_NAMES",
    "HEADER_KEYWORDS",
    "THAI_MONTHS",
    "THAI_SHORT_MONTHS",
    "guess_column_mapping",
    "read_excel_data",
    "to_full_buddhist_year",
    "format_thai_date"
]
