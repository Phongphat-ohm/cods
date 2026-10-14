"""
Root forwarder for icon_service ensuring 100% backward compatibility.
"""
from services.icon_service import (
    SVG_PATHS,
    get_svg_code,
    get_pixmap,
    get_icon,
    get_app_logo_path,
    get_app_logo_pixmap,
    get_app_logo_icon
)

__all__ = [
    "SVG_PATHS",
    "get_svg_code",
    "get_pixmap",
    "get_icon",
    "get_app_logo_path",
    "get_app_logo_pixmap",
    "get_app_logo_icon"
]
