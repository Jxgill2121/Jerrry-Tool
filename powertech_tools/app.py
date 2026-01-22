# Main Application Class for Powertech Tools
# VERSION: 2026-01-16 v4.4 - Modular Architecture

import base64
import tkinter as tk
from io import BytesIO
from tkinter import ttk

from powertech_tools.config.theme import PowertechTheme, apply_powertech_theme, POWERTECH_LOGO_BASE64
from powertech_tools.tabs import (
    build_merge_tab,
    build_maxmin_tab,
    build_plot_tab,
    build_avg_tab,
    build_validation_tab
)


class PowertechToolsApp(tk.Tk):
    """Main application window for Powertech Analysis Tools"""

    def __init__(self):
        super().__init__()

        self.title("JERRY - HITT Team Analysis Tool")
        self.geometry("1500x950")

        # Apply theme
        apply_powertech_theme(self)

        # Add company header
        self._build_header()

        # Create notebook (tabbed interface)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Create tab frames
        self.tab_merge = ttk.Frame(self.nb)
        self.tab_maxmin = ttk.Frame(self.nb)
        self.tab_plot = ttk.Frame(self.nb)
        self.tab_avg = ttk.Frame(self.nb)
        self.tab_val = ttk.Frame(self.nb)

        # Add tabs to notebook
        self.nb.add(self.tab_merge, text="  1) TDMS CONVERSION  ")
        self.nb.add(self.tab_maxmin, text="  2) MAX/MIN ANALYSIS  ")
        self.nb.add(self.tab_plot, text="  3) PLOT DATA  ")
        self.nb.add(self.tab_avg, text="  4) CYCLE AVERAGES  ")
        self.nb.add(self.tab_val, text="  5) VALIDATION  ")

        # Build each tab using modular functions
        build_merge_tab(self.tab_merge, self)
        build_maxmin_tab(self.tab_maxmin, self)
        build_plot_tab(self.tab_plot, self)
        build_avg_tab(self.tab_avg, self)
        build_validation_tab(self.tab_val, self)

    def _build_header(self):
        """Build professional header with company branding"""
        header = tk.Frame(self, bg="white", height=120)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Try to load embedded logo
        logo_label = None

        try:
            if POWERTECH_LOGO_BASE64.strip():
                from PIL import Image, ImageTk

                # Decode base64 to image
                logo_data = base64.b64decode(POWERTECH_LOGO_BASE64.strip())
                logo_img = Image.open(BytesIO(logo_data))

                # Resize to fit header (maintain aspect ratio)
                logo_img.thumbnail((450, 100), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)

                logo_label = tk.Label(header, image=logo_photo, bg="white")
                logo_label.image = logo_photo  # Keep a reference
                logo_label.pack(side="left", padx=30, pady=10)
        except Exception as e:
            # If logo fails to load, fall back to text
            print(f"Logo not loaded: {e}")

        # If no logo loaded, use text with bold, fun font
        if logo_label is None:
            title = tk.Label(
                header,
                text="JERRY",
                font=("Impact", 38, "bold"),  # Bold, impactful font
                bg="white",
                fg="#FF6B35"  # Vibrant orange
            )
            title.pack(side="left", padx=30, pady=10)

        # Subtitle with team branding
        subtitle = tk.Label(
            header,
            text="HITT Team Analysis Tool",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#004E89"  # Deep blue
        )
        subtitle.pack(side="left", padx=(0, 30))

        # Tagline
        tagline = tk.Label(
            header,
            text="High Impact Test Team",
            font=("Arial", 9, "italic"),
            bg="white",
            fg="#666666"
        )
        tagline.pack(side="left", padx=(0, 20))

        # Location
        location = tk.Label(
            header,
            text="📍 Surrey, BC • HITT Squad",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#FF6B35"
        )
        location.pack(side="right", padx=30)
