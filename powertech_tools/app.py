# Main Application Class for Powertech Tools
# VERSION: 2026-01-16 v4.6 - Dropdown Category Selector

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

        # Category selector bar
        selector_frame = ttk.Frame(self)
        selector_frame.pack(fill="x", padx=15, pady=(10, 5))

        ttk.Label(selector_frame, text="Category:", font=("Arial", 11, "bold")).pack(side="left", padx=(0, 10))

        self.category_var = tk.StringVar(value="File Conversion")
        self.category_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.category_var,
            values=["File Conversion", "Report Graphs", "Validation"],
            state="readonly",
            width=20,
            font=("Arial", 11)
        )
        self.category_dropdown.pack(side="left")
        self.category_dropdown.bind("<<ComboboxSelected>>", lambda e: self._switch_category())

        # Container for notebooks
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # Create all notebooks (hidden initially)
        self._create_all_notebooks()

        # Show initial category
        self._switch_category()

    def _create_all_notebooks(self):
        """Create all category notebooks"""

        # ========== FILE CONVERSION ==========
        self.nb_conversion = ttk.Notebook(self.content_frame)

        self.tab_merge = ttk.Frame(self.nb_conversion)
        self.tab_maxmin = ttk.Frame(self.nb_conversion)
        self.tab_avg = ttk.Frame(self.nb_conversion)

        self.nb_conversion.add(self.tab_merge, text="  TDMS Conversion  ")
        self.nb_conversion.add(self.tab_maxmin, text="  MaxMin Converter  ")
        self.nb_conversion.add(self.tab_avg, text="  Cycle Averages  ")

        build_merge_tab(self.tab_merge, self)
        build_maxmin_tab(self.tab_maxmin, self)
        build_avg_tab(self.tab_avg, self)

        # ========== REPORT GRAPHS ==========
        self.nb_graphs = ttk.Notebook(self.content_frame)

        self.tab_plot = ttk.Frame(self.nb_graphs)
        self.tab_cycle_viewer = ttk.Frame(self.nb_graphs)

        self.nb_graphs.add(self.tab_plot, text="  MaxMin Grapher  ")
        self.nb_graphs.add(self.tab_cycle_viewer, text="  Cycle Plotter  ")

        build_plot_tab(self.tab_plot, self)
        build_cycle_viewer_tab(self.tab_cycle_viewer, self)

        # ========== VALIDATION ==========
        self.nb_validation = ttk.Notebook(self.content_frame)

        self.tab_val = ttk.Frame(self.nb_validation)
        self.tab_asr = ttk.Frame(self.nb_validation)
        self.tab_fuel_systems = ttk.Frame(self.nb_validation)

        self.nb_validation.add(self.tab_val, text="  Cylinders  ")
        self.nb_validation.add(self.tab_asr, text="  ASR  ")
        self.nb_validation.add(self.tab_fuel_systems, text="  Fuel Systems  ")

        build_validation_tab(self.tab_val, self)
        build_asr_tab(self.tab_asr, self)
        build_fuel_systems_tab(self.tab_fuel_systems, self)

    def _switch_category(self):
        """Switch visible notebook based on dropdown selection"""
        # Hide all notebooks
        self.nb_conversion.pack_forget()
        self.nb_graphs.pack_forget()
        self.nb_validation.pack_forget()

        # Show selected category
        category = self.category_var.get()
        if category == "File Conversion":
            self.nb_conversion.pack(fill="both", expand=True)
        elif category == "Report Graphs":
            self.nb_graphs.pack(fill="both", expand=True)
        elif category == "Validation":
            self.nb_validation.pack(fill="both", expand=True)

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
