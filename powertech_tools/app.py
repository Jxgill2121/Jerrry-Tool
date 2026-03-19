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
    build_validation_tab,
    build_asr_tab,
    build_fuel_systems_tab,
    build_cycle_viewer_tab
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
        self.tab_asr = ttk.Frame(self.nb)
        self.tab_fuel_systems = ttk.Frame(self.nb)
        self.tab_cycle_viewer = ttk.Frame(self.nb)

        # Add tabs to notebook
        self.nb.add(self.tab_merge, text="  1) TDMS CONVERSION  ")
        self.nb.add(self.tab_maxmin, text="  2) MAXMIN CONVERTER  ")
        self.nb.add(self.tab_plot, text="  3) PLOT DATA  ")
        self.nb.add(self.tab_avg, text="  4) CYCLE AVERAGES  ")
        self.nb.add(self.tab_val, text="  5) CYLINDERS VALIDATION  ")
        self.nb.add(self.tab_asr, text="  6) ASR VALIDATION  ")
        self.nb.add(self.tab_fuel_systems, text="  7) FUEL SYSTEMS  ")
        self.nb.add(self.tab_cycle_viewer, text="  8) CYCLE VIEWER  ")

        # Build each tab using modular functions
        build_merge_tab(self.tab_merge, self)
        build_maxmin_tab(self.tab_maxmin, self)
        build_plot_tab(self.tab_plot, self)
        build_avg_tab(self.tab_avg, self)
        build_validation_tab(self.tab_val, self)
        build_asr_tab(self.tab_asr, self)
        build_fuel_systems_tab(self.tab_fuel_systems, self)
        build_cycle_viewer_tab(self.tab_cycle_viewer, self)

    def _build_header(self):
        """Build professional header with company branding"""
        header = tk.Frame(self, bg="white", height=100)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Create a cute cat logo using Canvas
        cat_canvas = tk.Canvas(header, width=80, height=80, bg="white", highlightthickness=0)
        cat_canvas.pack(side="left", padx=(30, 5), pady=10)

        # Cat colors
        cat_color = "#0D9488"  # Teal
        cat_dark = "#0F766E"   # Dark teal

        # Draw cat face (circle)
        cat_canvas.create_oval(15, 20, 65, 70, fill=cat_color, outline=cat_dark, width=2)

        # Draw ears (triangles)
        cat_canvas.create_polygon(18, 28, 28, 8, 38, 28, fill=cat_color, outline=cat_dark, width=2)  # Left ear
        cat_canvas.create_polygon(42, 28, 52, 8, 62, 28, fill=cat_color, outline=cat_dark, width=2)  # Right ear

        # Inner ears (pink)
        cat_canvas.create_polygon(23, 26, 28, 14, 33, 26, fill="#FDA4AF", outline="")  # Left inner
        cat_canvas.create_polygon(47, 26, 52, 14, 57, 26, fill="#FDA4AF", outline="")  # Right inner

        # Eyes (white with dark pupils)
        cat_canvas.create_oval(25, 35, 35, 48, fill="white", outline=cat_dark, width=1)  # Left eye
        cat_canvas.create_oval(45, 35, 55, 48, fill="white", outline=cat_dark, width=1)  # Right eye

        # Pupils
        cat_canvas.create_oval(28, 38, 33, 46, fill=cat_dark, outline="")  # Left pupil
        cat_canvas.create_oval(48, 38, 53, 46, fill=cat_dark, outline="")  # Right pupil

        # Nose (small triangle)
        cat_canvas.create_polygon(40, 50, 36, 55, 44, 55, fill="#FDA4AF", outline="")

        # Mouth (simple smile)
        cat_canvas.create_arc(32, 52, 42, 62, start=200, extent=140, style="arc", outline=cat_dark, width=2)
        cat_canvas.create_arc(38, 52, 48, 62, start=200, extent=140, style="arc", outline=cat_dark, width=2)

        # Whiskers
        cat_canvas.create_line(15, 50, 28, 52, fill=cat_dark, width=1)
        cat_canvas.create_line(15, 55, 28, 55, fill=cat_dark, width=1)
        cat_canvas.create_line(15, 60, 28, 58, fill=cat_dark, width=1)
        cat_canvas.create_line(65, 50, 52, 52, fill=cat_dark, width=1)
        cat_canvas.create_line(65, 55, 52, 55, fill=cat_dark, width=1)
        cat_canvas.create_line(65, 60, 52, 58, fill=cat_dark, width=1)

        # JERRY text
        title = tk.Label(
            header,
            text="JERRY",
            font=("Arial", 36, "bold"),
            bg="white",
            fg="#0D9488"
        )
        title.pack(side="left", padx=(5, 15), pady=10)

        # Subtitle
        subtitle = tk.Label(
            header,
            text="HITT Team Analysis Tool",
            font=("Arial", 12),
            bg="white",
            fg="#5F7A78"
        )
        subtitle.pack(side="left", padx=(0, 30))
