APP_NAME = "PDF eSign"

ZOOM_MIN = 0.25
ZOOM_MAX = 4.0
ZOOM_STEP = 0.25
ZOOM_DEFAULT = 1.0

SUPPORTED_COLORS = ["black", "blue"]

DEFAULT_DATE_FORMAT = "%m/%d/%Y"

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

SIGNATURE_FONTS = [
    {"name": "Alex Brush",     "file": "AlexBrush-Regular.ttf"},
    {"name": "Allura",         "file": "Allura-Regular.ttf"},
    {"name": "Great Vibes",    "file": "GreatVibes-Regular.ttf"},
    {"name": "Parisienne",     "file": "Parisienne-Regular.ttf"},
    {"name": "Sacramento",     "file": "Sacramento-Regular.ttf"},
]

from app.theme import (
    ThemeColors,
    ThemeRadii,
    ThemeSizes,
    ThemeSpacing,
    ThemeTokens,
    ThemeTypography,
)


THEME = ThemeTokens(
    colors=ThemeColors(
        app_bg="#F3F1EE",
        panel_bg="#ECE8E3",
        toolbar_bg="#F6F4F1",
        surface_bg="#FBFAF8",
        workspace_bg="#EEEAE5",
        text="#2C2A28",
        text_muted="#6C6761",
        border="#D7D1CA",
        active_fill="#E1DBD4",
        active_border="#8D857C",
        primary_bg="#5B5752",
        primary_text="#F8F7F5",
        quiet_bg="#F4F1ED",
        danger_bg="#EFEAE4",
        danger_text="#4E4944",
    ),
    spacing=ThemeSpacing(
        outer=10,
        panel_padding=10,
        section_gap=10,
        field_gap=6,
        compact_gap=6,
    ),
    radii=ThemeRadii(
        control=5,
        surface=6,
    ),
    sizes=ThemeSizes(
        toolbar_height=38,
        control_height=30,
        compact_control_height=28,
        left_panel_width=268,
        right_panel_width=182,
    ),
    typography=ThemeTypography(
        family="Segoe UI",
        section_title_px=15,
        body_px=13,
        helper_px=12,
    ),
)
