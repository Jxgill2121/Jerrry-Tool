# VERSION: 2026-01-22 v5.0 - JERRY HITT Team Theme
# JERRY - HITT Team Analysis Tool (Surrey, BC)

from tkinter import ttk


# ============================================================
# EMBEDDED LOGO (BASE64)
# ============================================================

# PASTE YOUR BASE64 LOGO STRING BETWEEN THE TRIPLE QUOTES BELOW
POWERTECH_LOGO_BASE64 = """

"""


# ============================================================
# THEME CONFIGURATION
# ============================================================

class PowertechTheme:
    """JERRY HITT Team - Vibrant and bold color scheme"""

    # Main colors - vibrant orange and deep blue
    PRIMARY = "#004E89"          # Deep blue (HITT Team blue)
    PRIMARY_LIGHT = "#1A6BA8"    # Medium blue
    PRIMARY_DARK = "#002E54"     # Very dark blue

    ACCENT = "#FF6B35"           # Vibrant orange (JERRY orange)
    ACCENT_LIGHT = "#FF8C5A"     # Light orange

    SUCCESS = "#38a169"          # Green for success states
    WARNING = "#FFA500"          # Orange for warnings
    ERROR = "#e53e3e"            # Red for errors

    # Neutral colors
    BG_MAIN = "#f7fafc"          # Very light gray background
    BG_SECONDARY = "#edf2f7"     # Light gray
    BG_CARD = "#ffffff"          # White cards

    TEXT_PRIMARY = "#1a202c"     # Almost black
    TEXT_SECONDARY = "#4a5568"   # Medium gray
    TEXT_LIGHT = "#718096"       # Light gray

    BORDER = "#cbd5e0"           # Light border

    # Fonts - clean and modern
    FONT_FAMILY = "Arial"
    FONT_SIZE_TITLE = 16
    FONT_SIZE_HEADING = 12
    FONT_SIZE_BODY = 10
    FONT_SIZE_SMALL = 9


def apply_powertech_theme(root):
    """Apply custom Powertech styling to the application"""

    style = ttk.Style(root)

    # Use 'clam' as base theme for better customization
    style.theme_use('clam')

    # Configure main window
    root.configure(bg=PowertechTheme.BG_MAIN)

    # Notebook (tabs)
    style.configure('TNotebook',
                   background=PowertechTheme.BG_MAIN,
                   borderwidth=0)
    style.configure('TNotebook.Tab',
                   background=PowertechTheme.BG_SECONDARY,
                   foreground=PowertechTheme.TEXT_PRIMARY,
                   padding=[20, 10],
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY, 'bold'))
    style.map('TNotebook.Tab',
             background=[('selected', PowertechTheme.PRIMARY)],
             foreground=[('selected', 'white')],
             expand=[('selected', [1, 1, 1, 0])])

    # Frames
    style.configure('TFrame',
                   background=PowertechTheme.BG_MAIN)
    style.configure('Card.TFrame',
                   background=PowertechTheme.BG_CARD,
                   relief='flat',
                   borderwidth=1)

    # LabelFrames
    style.configure('TLabelframe',
                   background=PowertechTheme.BG_CARD,
                   foreground=PowertechTheme.PRIMARY,
                   borderwidth=2,
                   relief='solid')
    style.configure('TLabelframe.Label',
                   background=PowertechTheme.BG_CARD,
                   foreground=PowertechTheme.PRIMARY,
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_HEADING, 'bold'))

    # Buttons
    style.configure('TButton',
                   background=PowertechTheme.PRIMARY,
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none',
                   padding=[15, 8],
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY, 'bold'))
    style.map('TButton',
             background=[('active', PowertechTheme.PRIMARY_LIGHT),
                        ('pressed', PowertechTheme.PRIMARY_DARK)])

    # Action buttons (prominent)
    style.configure('Action.TButton',
                   background=PowertechTheme.ACCENT,
                   foreground='white',
                   padding=[20, 10],
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY, 'bold'))
    style.map('Action.TButton',
             background=[('active', PowertechTheme.ACCENT_LIGHT)])

    # Labels
    style.configure('TLabel',
                   background=PowertechTheme.BG_MAIN,
                   foreground=PowertechTheme.TEXT_PRIMARY,
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY))

    style.configure('Title.TLabel',
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_TITLE, 'bold'),
                   foreground=PowertechTheme.PRIMARY)

    style.configure('Subtitle.TLabel',
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY),
                   foreground=PowertechTheme.TEXT_SECONDARY)

    style.configure('Status.TLabel',
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY),
                   foreground=PowertechTheme.TEXT_SECONDARY,
                   padding=[5, 5])

    # Entry and Combobox
    style.configure('TEntry',
                   fieldbackground='white',
                   foreground=PowertechTheme.TEXT_PRIMARY,
                   borderwidth=1,
                   relief='solid')

    style.configure('TCombobox',
                   fieldbackground='white',
                   foreground=PowertechTheme.TEXT_PRIMARY,
                   arrowcolor=PowertechTheme.PRIMARY,
                   borderwidth=1)
    style.map('TCombobox',
             fieldbackground=[('readonly', 'white')],
             selectbackground=[('readonly', PowertechTheme.ACCENT_LIGHT)])

    # Spinbox
    style.configure('TSpinbox',
                   fieldbackground='white',
                   foreground=PowertechTheme.TEXT_PRIMARY,
                   arrowcolor=PowertechTheme.PRIMARY)

    # Checkbutton
    style.configure('TCheckbutton',
                   background=PowertechTheme.BG_CARD,
                   foreground=PowertechTheme.TEXT_PRIMARY,
                   font=(PowertechTheme.FONT_FAMILY, PowertechTheme.FONT_SIZE_BODY))
