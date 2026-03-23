# VERSION: 2026-03-19 v6.0 - Jerry HITT Team Theme (Green/Teal)
# Jerry - HITT Team Analysis Tool (Surrey, BC)

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
    """Jerry HITT Team - Green/Teal color scheme"""

    # Main colors - teal and green
    PRIMARY = "#0D9488"          # Teal
    PRIMARY_LIGHT = "#14B8A6"    # Light teal
    PRIMARY_DARK = "#0F766E"     # Dark teal

    ACCENT = "#10B981"           # Emerald green
    ACCENT_LIGHT = "#34D399"     # Light green

    SUCCESS = "#22C55E"          # Green for success states
    WARNING = "#F59E0B"          # Amber for warnings
    ERROR = "#EF4444"            # Red for errors

    # Neutral colors
    BG_MAIN = "#F0FDFA"          # Very light teal tint background
    BG_SECONDARY = "#CCFBF1"     # Light teal
    BG_CARD = "#ffffff"          # White cards

    TEXT_PRIMARY = "#134E4A"     # Dark teal text
    TEXT_SECONDARY = "#5F7A78"   # Medium gray-teal
    TEXT_LIGHT = "#7C9A97"       # Light gray-teal

    BORDER = "#99F6E4"           # Light teal border

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
             background=[('disabled', '#9CA3AF'), ('active', PowertechTheme.ACCENT_LIGHT)],
             foreground=[('disabled', 'white')])

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
