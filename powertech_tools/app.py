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

        self.title("Jerry - HITT Team Analysis Tool")
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

        # Create Jerry the mouse logo using Canvas
        mouse_canvas = tk.Canvas(header, width=85, height=80, bg="white", highlightthickness=0)
        mouse_canvas.pack(side="left", padx=(30, 5), pady=10)

        # Mouse colors (brown like Jerry)
        mouse_color = "#C4A484"  # Light brown/tan
        mouse_dark = "#8B7355"   # Darker brown
        mouse_inner = "#F5DEB3"  # Cream/beige for inner areas
        pink = "#FFB6C1"         # Light pink

        # Draw big round ears (behind head)
        mouse_canvas.create_oval(5, 10, 35, 40, fill=mouse_color, outline=mouse_dark, width=2)   # Left ear
        mouse_canvas.create_oval(50, 10, 80, 40, fill=mouse_color, outline=mouse_dark, width=2)  # Right ear

        # Inner ears (pink)
        mouse_canvas.create_oval(12, 17, 28, 33, fill=pink, outline="")   # Left inner
        mouse_canvas.create_oval(57, 17, 73, 33, fill=pink, outline="")   # Right inner

        # Draw mouse face (oval, slightly wider)
        mouse_canvas.create_oval(18, 25, 67, 75, fill=mouse_color, outline=mouse_dark, width=2)

        # Cream colored face/belly area
        mouse_canvas.create_oval(25, 40, 60, 72, fill=mouse_inner, outline="")

        # Eyes (big and expressive like Jerry)
        mouse_canvas.create_oval(26, 35, 40, 52, fill="white", outline=mouse_dark, width=1)  # Left eye
        mouse_canvas.create_oval(45, 35, 59, 52, fill="white", outline=mouse_dark, width=1)  # Right eye

        # Pupils (looking slightly to the side)
        mouse_canvas.create_oval(31, 40, 38, 49, fill="black", outline="")  # Left pupil
        mouse_canvas.create_oval(50, 40, 57, 49, fill="black", outline="")  # Right pupil

        # Eye shine
        mouse_canvas.create_oval(33, 41, 36, 44, fill="white", outline="")  # Left shine
        mouse_canvas.create_oval(52, 41, 55, 44, fill="white", outline="")  # Right shine

        # Nose (round pink nose)
        mouse_canvas.create_oval(38, 52, 47, 60, fill=pink, outline=mouse_dark, width=1)

        # Smile
        mouse_canvas.create_arc(32, 58, 53, 72, start=200, extent=140, style="arc", outline=mouse_dark, width=2)

        # Whiskers
        mouse_canvas.create_line(10, 55, 28, 58, fill=mouse_dark, width=1)
        mouse_canvas.create_line(10, 62, 28, 62, fill=mouse_dark, width=1)
        mouse_canvas.create_line(10, 69, 28, 66, fill=mouse_dark, width=1)
        mouse_canvas.create_line(75, 55, 57, 58, fill=mouse_dark, width=1)
        mouse_canvas.create_line(75, 62, 57, 62, fill=mouse_dark, width=1)
        mouse_canvas.create_line(75, 69, 57, 66, fill=mouse_dark, width=1)

        # Jerry text
        title = tk.Label(
            header,
            text="Jerry",
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
