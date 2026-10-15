"""
CODS Icon Service - High Performance 100% Offline Vector SVG Icon Renderer
Renders crisp vector SVG icons into PySide6 QPixmap and QIcon instances.
Supports custom colors, sizes, and stroke widths with caching.
"""

import os
from typing import Dict, Tuple
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter, QPixmap, QIcon
from PySide6.QtCore import QByteArray, Qt

# Professional Vector SVG Icon Path Library (Enterprise Judicial Theme)
SVG_PATHS: Dict[str, str] = {
    "file-text": """
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
    """,
    "file-spreadsheet": """
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <rect x="8" y="12" width="8" height="6" rx="1"></rect>
        <line x1="12" y1="12" x2="12" y2="18"></line>
        <line x1="8" y1="15" x2="16" y2="15"></line>
    """,
    "clipboard-list": """
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
        <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
        <path d="M9 12h6"></path>
        <path d="M9 16h6"></path>
    """,
    "landmark": """
        <line x1="3" y1="21" x2="21" y2="21"></line>
        <line x1="4" y1="11" x2="20" y2="11"></line>
        <polyline points="12 3 20 8 4 8 12 3"></polyline>
        <line x1="6" y1="11" x2="6" y2="21"></line>
        <line x1="10" y1="11" x2="10" y2="21"></line>
        <line x1="14" y1="11" x2="14" y2="21"></line>
        <line x1="18" y1="11" x2="18" y2="21"></line>
    """,
    "scale": """
        <path d="M12 3v18"></path>
        <path d="M6 7l6-2 6 2"></path>
        <path d="M3 13a3 3 0 0 0 6 0l-3-6-3 6z"></path>
        <path d="M15 13a3 3 0 0 0 6 0l-3-6-3 6z"></path>
        <line x1="4" y1="21" x2="20" y2="21"></line>
    """,
    "folder-open": """
        <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2z"></path>
        <polygon points="2 10 22 10 20 20 4 20"></polygon>
    """,
    "save": """
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
    """,
    "settings": """
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    """,
    "plus": """
        <line x1="12" y1="5" x2="12" y2="19"></line>
        <line x1="5" y1="12" x2="19" y2="12"></line>
    """,
    "trash": """
        <polyline points="3 6 5 6 21 6"></polyline>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        <line x1="10" y1="11" x2="10" y2="17"></line>
        <line x1="14" y1="11" x2="14" y2="17"></line>
    """,
    "search": """
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    """,
    "grip-vertical": """
        <circle cx="9" cy="5" r="1.5" fill="currentColor"></circle>
        <circle cx="9" cy="12" r="1.5" fill="currentColor"></circle>
        <circle cx="9" cy="19" r="1.5" fill="currentColor"></circle>
        <circle cx="15" cy="5" r="1.5" fill="currentColor"></circle>
        <circle cx="15" cy="12" r="1.5" fill="currentColor"></circle>
        <circle cx="15" cy="19" r="1.5" fill="currentColor"></circle>
    """,
    "arrow-right": """
        <line x1="5" y1="12" x2="19" y2="12"></line>
        <polyline points="12 5 19 12 12 19"></polyline>
    """,
    "arrow-left": """
        <line x1="19" y1="12" x2="5" y2="12"></line>
        <polyline points="12 19 5 12 12 5"></polyline>
    """,
    "chevron-up": """
        <polyline points="18 15 12 9 6 15"></polyline>
    """,
    "chevron-down": """
        <polyline points="6 9 12 15 18 9"></polyline>
    """,
    "check": """
        <polyline points="20 6 9 17 4 12"></polyline>
    """,
    "users": """
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        <circle cx="9" cy="7" r="4"></circle>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
    """,
    "user": """
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
    """,
    "edit": """
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
    """,
    "link": """
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
    """,
    "filter": """
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
    """,
    "refresh": """
        <polyline points="23 4 23 10 17 10"></polyline>
        <polyline points="1 20 1 14 7 14"></polyline>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
    """,
    "calendar": """
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
        <line x1="16" y1="2" x2="16" y2="6"></line>
        <line x1="8" y1="2" x2="8" y2="6"></line>
        <line x1="3" y1="10" x2="21" y2="10"></line>
    """,
    "status-dot": """
        <circle cx="12" cy="12" r="8" fill="currentColor"></circle>
    """,
    "lightbulb": """
        <path d="M9 18h6"></path>
        <path d="M10 22h4"></path>
        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path>
    """,
    "help-circle": """
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
    """,
    "book-open": """
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
    """,
    "info": """
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
    """,
}

DEFAULT_ICON_COLOR = "#4c1d95"

_PIXMAP_CACHE: Dict[Tuple[str, str, int, float], QPixmap] = {}
_ICON_CACHE: Dict[Tuple[str, str, int, float], QIcon] = {}


def get_svg_code(icon_name: str, color: str = DEFAULT_ICON_COLOR, stroke_width: float = 2.0) -> str:
    """Generate SVG XML markup with both stroke and color attributes set to ensure currentColor renders properly."""
    path_content = SVG_PATHS.get(icon_name, SVG_PATHS["file-text"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" 
        color="{color}" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
        {path_content}
    </svg>"""


def get_pixmap(icon_name: str, color: str = DEFAULT_ICON_COLOR, size: int = 24, stroke_width: float = 2.0) -> QPixmap:
    """Render and return a cached QPixmap of the requested SVG icon."""
    cache_key = (icon_name, color, size, stroke_width)
    if cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    svg_code = get_svg_code(icon_name, color, stroke_width)
    renderer = QSvgRenderer(QByteArray(svg_code.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    _PIXMAP_CACHE[cache_key] = pixmap
    return pixmap


def get_icon(icon_name: str, color: str = DEFAULT_ICON_COLOR, size: int = 20, stroke_width: float = 2.0) -> QIcon:
    """Render and return a cached QIcon of the requested SVG icon."""
    cache_key = (icon_name, color, size, stroke_width)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    pixmap = get_pixmap(icon_name, color, size, stroke_width)
    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon


def get_app_logo_path() -> str:
    """Resolve absolute path to logo.png in project root, app dir, or frozen bundle."""
    from services.storage_service import get_logo_path
    logo = get_logo_path()
    if logo and os.path.exists(logo):
        return logo
    cwd_logo = os.path.join(os.getcwd(), "logo.png")
    if os.path.exists(cwd_logo):
        return cwd_logo
    return ""


def get_app_logo_pixmap(size: int = 48) -> QPixmap:
    """
    Return a smoothly scaled QPixmap of logo.png.
    Falls back gracefully to the judicial scale icon if not found.
    """
    cache_key = ("__app_logo__", size, 0.0, 0.0)
    if cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    logo_path = get_app_logo_path()
    if logo_path and os.path.exists(logo_path):
        orig = QPixmap(logo_path)
        if not orig.isNull():
            scaled = orig.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            _PIXMAP_CACHE[cache_key] = scaled
            return scaled

    fallback = get_pixmap("scale", color=DEFAULT_ICON_COLOR, size=size)
    _PIXMAP_CACHE[cache_key] = fallback
    return fallback


def get_app_logo_icon() -> QIcon:
    """
    Return QIcon of application logo for window and taskbar icons.
    """
    cache_key = ("__app_logo_icon__", "", 0, 0.0)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    logo_path = get_app_logo_path()
    if logo_path and os.path.exists(logo_path):
        icon = QIcon(logo_path)
        _ICON_CACHE[cache_key] = icon
        return icon

    icon = get_icon("scale", color=DEFAULT_ICON_COLOR, size=64)
    _ICON_CACHE[cache_key] = icon
    return icon

