# Fuel Systems Validation tab - Advanced cycle validation with time-based checks

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from powertech_tools.utils.helpers import ScrollableFrame, natural_sort_key
from powertech_tools.utils.fuel_systems_presets import (
    save_preset, delete_preset, get_preset_names, get_preset
)
from powertech_tools.data.fuel_systems_validator import validate_fuel_system_file
from powertech_tools.utils.file_parser import read_headers_only


def build_tab(parent, app):
    """
    Build the Fuel Systems Validation tab UI.

    Args:
        parent: Parent frame for this tab
        app: Main application instance (for storing state)
    """
    scrollable = ScrollableFrame(parent)
    scrollable.pack(fill="both", expand=True)
    f = ttk.Frame(scrollable.content)
    f.pack(fill="both", expand=True, padx=15, pady=15)

    # Import theme for styling
    from powertech_tools.config.theme import PowertechTheme

    # Title
    title_label = ttk.Label(f, text="Fuel Systems Validation", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Advanced cycle validation with Ptank-based cycle detection and time-based tfuel checks",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection card
    card1 = ttk.LabelFrame(f, text="Cycle Files Selection", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    # Store state in app instance
    app.fs_files = []
    app.fs_column_headers = []
    app.fs_param_vars = {}  # CheckButton variables for parameter selection
    app.fs_param_min_vars = {}  # Min bound entries
    app.fs_param_max_vars = {}  # Max bound entries
    app.fs_results = []

    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x", pady=(0, 10))

    ttk.Button(
        btn_frame,
        text="📁 Choose Cycle Files",
        command=lambda: _fs_choose_files(app),
        style='Action.TButton'
    ).pack(side="left")

    app.fs_files_label = tk.StringVar(value="No files selected")
    ttk.Label(
        btn_frame,
        textvariable=app.fs_files_label,
        style='Status.TLabel'
    ).pack(side="left", padx=15)

    # Configuration card
    card2 = ttk.LabelFrame(f, text="Validation Configuration", padding=20)
    card2.pack(fill="x", pady=(0, 15))

    config_frame = ttk.Frame(card2)
    config_frame.pack(fill="x")

    # Column selections
    col_frame = ttk.Frame(config_frame)
    col_frame.pack(fill="x", pady=5)

    ttk.Label(col_frame, text="Time Column:", width=20).pack(side="left")
    app.fs_time_col = tk.StringVar(value="")
    app.cb_fs_time = ttk.Combobox(col_frame, state="disabled", width=20, textvariable=app.fs_time_col, values=[])
    app.cb_fs_time.pack(side="left", padx=5)

    ttk.Label(col_frame, text="Ptank Column:", width=15).pack(side="left", padx=(20, 0))
    app.fs_ptank_col = tk.StringVar(value="")
    app.cb_fs_ptank = ttk.Combobox(col_frame, state="disabled", width=20, textvariable=app.fs_ptank_col, values=[])
    app.cb_fs_ptank.pack(side="left", padx=5)

    ttk.Label(col_frame, text="tfuel Column:", width=15).pack(side="left", padx=(20, 0))
    app.fs_tfuel_col = tk.StringVar(value="")
    app.cb_fs_tfuel = ttk.Combobox(col_frame, state="disabled", width=20, textvariable=app.fs_tfuel_col, values=[])
    app.cb_fs_tfuel.pack(side="left", padx=5)

    # Fill detection settings
    cycle_frame = ttk.LabelFrame(config_frame, text="Fill Detection", padding=10)
    cycle_frame.pack(fill="x", pady=(10, 5))

    ptank_row = ttk.Frame(cycle_frame)
    ptank_row.pack(fill="x", pady=2)
    ttk.Label(ptank_row, text="Ptank Threshold (MPa):").pack(side="left")
    app.fs_ptank_threshold = tk.StringVar(value="2.0")
    ttk.Entry(ptank_row, textvariable=app.fs_ptank_threshold, width=10).pack(side="left", padx=10)
    ttk.Label(ptank_row, text="(Fill start detected from Ptank)", font=(PowertechTheme.FONT_FAMILY, 8), foreground="#666").pack(side="left", padx=5)

    end_row = ttk.Frame(cycle_frame)
    end_row.pack(fill="x", pady=5)
    ttk.Label(end_row, text="End of Fill Based On:").pack(side="left")
    app.fs_end_mode = tk.StringVar(value="Ptank")
    ttk.Radiobutton(end_row, text="Ptank", variable=app.fs_end_mode, value="Ptank").pack(side="left", padx=(10, 5))
    ttk.Radiobutton(end_row, text="SOC", variable=app.fs_end_mode, value="SOC").pack(side="left", padx=5)

    soc_row = ttk.Frame(cycle_frame)
    soc_row.pack(fill="x", pady=2)
    ttk.Label(soc_row, text="SOC Column:").pack(side="left")
    app.fs_soc_col = tk.StringVar(value="")
    app.cb_fs_soc = ttk.Combobox(soc_row, state="disabled", width=20, textvariable=app.fs_soc_col, values=[])
    app.cb_fs_soc.pack(side="left", padx=10)
    ttk.Label(soc_row, text="SOC Threshold (%):").pack(side="left", padx=(10, 0))
    app.fs_soc_threshold = tk.StringVar(value="100")
    ttk.Entry(soc_row, textvariable=app.fs_soc_threshold, width=10).pack(side="left", padx=10)
    ttk.Label(soc_row, text="(only used in SOC mode)", font=(PowertechTheme.FONT_FAMILY, 8), foreground="#666").pack(side="left", padx=5)

    # tfuel timing check settings (optional)
    tfuel_frame = ttk.LabelFrame(config_frame, text="tfuel Timing Check (Optional)", padding=10)
    tfuel_frame.pack(fill="x", pady=(10, 5))

    tfuel_enable_row = ttk.Frame(tfuel_frame)
    tfuel_enable_row.pack(fill="x", pady=2)
    app.fs_enable_tfuel_check = tk.BooleanVar(value=True)
    ttk.Checkbutton(tfuel_enable_row, text="Enable tfuel timing check", variable=app.fs_enable_tfuel_check).pack(side="left")

    tfuel_row1 = ttk.Frame(tfuel_frame)
    tfuel_row1.pack(fill="x", pady=2)
    ttk.Label(tfuel_row1, text="Target Temperature (°C):").pack(side="left")
    app.fs_tfuel_target = tk.StringVar(value="-30")
    ttk.Entry(tfuel_row1, textvariable=app.fs_tfuel_target, width=10).pack(side="left", padx=10)

    ttk.Label(tfuel_row1, text="Time Window (seconds):").pack(side="left", padx=(20, 0))
    app.fs_tfuel_window = tk.StringVar(value="30")
    ttk.Entry(tfuel_row1, textvariable=app.fs_tfuel_window, width=10).pack(side="left", padx=10)

    tfuel_desc = ttk.Label(
        tfuel_frame,
        text="tfuel must reach and hold target temperature within time window from fill start",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    tfuel_desc.pack(anchor="w", pady=(5, 0))

    # Average pressure ramp rate check (optional)
    ramp_frame = ttk.LabelFrame(config_frame, text="Average Pressure Ramp Rate Check (Optional)", padding=10)
    ramp_frame.pack(fill="x", pady=(10, 5))

    ramp_enable_row = ttk.Frame(ramp_frame)
    ramp_enable_row.pack(fill="x", pady=2)
    app.fs_enable_ramp_check = tk.BooleanVar(value=False)
    ttk.Checkbutton(ramp_enable_row, text="Enable average ramp rate check", variable=app.fs_enable_ramp_check).pack(side="left")

    ramp_row = ttk.Frame(ramp_frame)
    ramp_row.pack(fill="x", pady=2)
    ttk.Label(ramp_row, text="Max Ramp Rate (MPa/min):").pack(side="left")
    app.fs_ramp_limit = tk.StringVar(value="")
    ttk.Entry(ramp_row, textvariable=app.fs_ramp_limit, width=10).pack(side="left", padx=10)
    ttk.Label(ramp_row, text="(leave blank to report only, no pass/fail)", font=(PowertechTheme.FONT_FAMILY, 8), foreground="#666").pack(side="left", padx=5)

    # Preset management section
    preset_frame = ttk.LabelFrame(config_frame, text="Configuration Presets", padding=15)
    preset_frame.pack(fill="x", pady=(15, 0))

    preset_desc = ttk.Label(
        preset_frame,
        text="Save/load validation configurations for different test types",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    preset_desc.pack(anchor="w", pady=(0, 10))

    preset_row1 = ttk.Frame(preset_frame)
    preset_row1.pack(fill="x", pady=5)

    ttk.Label(preset_row1, text="Select Preset:", width=15).pack(side="left")
    app.fs_preset_var = tk.StringVar(value="")
    app.fs_preset_combo = ttk.Combobox(preset_row1, state="readonly", width=30, textvariable=app.fs_preset_var)
    app.fs_preset_combo.pack(side="left", padx=10)

    ttk.Button(
        preset_row1,
        text="⬇ Load Preset",
        command=lambda: _fs_load_preset(app)
    ).pack(side="left", padx=5)

    ttk.Button(
        preset_row1,
        text="🗑 Delete",
        command=lambda: _fs_delete_preset(app)
    ).pack(side="left", padx=5)

    preset_row2 = ttk.Frame(preset_frame)
    preset_row2.pack(fill="x", pady=5)

    ttk.Label(preset_row2, text="Save As:", width=15).pack(side="left")
    app.fs_preset_name_var = tk.StringVar(value="")
    ttk.Entry(preset_row2, textvariable=app.fs_preset_name_var, width=30).pack(side="left", padx=10)

    ttk.Button(
        preset_row2,
        text="💾 Save Current Settings",
        command=lambda: _fs_save_preset(app)
    ).pack(side="left", padx=5)

    app.fs_preset_status = tk.StringVar(value="")
    ttk.Label(preset_row2, textvariable=app.fs_preset_status, foreground=PowertechTheme.ACCENT).pack(side="left", padx=10)

    # Refresh preset list
    _fs_refresh_preset_list(app)

    # Parameters bounds card
    card3 = ttk.LabelFrame(f, text="Parameter Bounds (Min/Max Validation)", padding=15)
    card3.pack(fill="both", expand=True, pady=(0, 15))

    params_desc = ttk.Label(
        card3,
        text="Select parameters to validate and set their min/max bounds. NOTE: tfuel bounds apply AFTER the time window.",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    params_desc.pack(anchor="w", pady=(0, 10))

    # Scrollable frame for parameter checkboxes
    app.fs_param_frame = ttk.Frame(card3)
    app.fs_param_frame.pack(fill="both", expand=True)

    # Selection buttons
    btn_row = ttk.Frame(card3)
    btn_row.pack(fill="x", pady=(10, 0))
    ttk.Button(btn_row, text="Select All", command=lambda: _fs_select_all_params(app, True)).pack(side="left", padx=5)
    ttk.Button(btn_row, text="Deselect All", command=lambda: _fs_select_all_params(app, False)).pack(side="left")

    app.fs_param_status = tk.StringVar(value="No parameters available")
    ttk.Label(btn_row, textvariable=app.fs_param_status, foreground="#666").pack(side="left", padx=15)

    # Action card
    action_card = ttk.LabelFrame(f, text="Run Validation", padding=20)
    action_card.pack(fill="x", pady=(0, 15))

    action_row = ttk.Frame(action_card)
    action_row.pack(fill="x")

    ttk.Button(
        action_row,
        text="▶ VALIDATE FILES",
        command=lambda: _fs_validate(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Button(
        action_row,
        text="📊 Export Results",
        command=lambda: _fs_export_results(app)
    ).pack(side="left", padx=10)

    app.fs_status = tk.StringVar(value="")
    status_label = ttk.Label(action_row, textvariable=app.fs_status, style='Status.TLabel')
    status_label.pack(side="left", padx=15)

    # Results card
    results_card = ttk.LabelFrame(f, text="Validation Results", padding=15)
    results_card.pack(fill="x", pady=(0, 15))

    app.fs_results_text = scrolledtext.ScrolledText(
        results_card,
        height=10,
        font=("Courier New", 9),
        wrap=tk.WORD
    )
    app.fs_results_text.pack(fill="both", expand=True)

    # Cycle Visualization card
    viz_card = ttk.LabelFrame(f, text="Cycle Visualization (Clean Data Only)", padding=15)
    viz_card.pack(fill="both", expand=True, pady=(0, 0))

    # Navigation controls
    nav_frame = ttk.Frame(viz_card)
    nav_frame.pack(fill="x", pady=(0, 10))

    ttk.Button(
        nav_frame,
        text="◀ Previous",
        command=lambda: _fs_show_cycle(app, -1)
    ).pack(side="left", padx=5)

    ttk.Button(
        nav_frame,
        text="Next ▶",
        command=lambda: _fs_show_cycle(app, 1)
    ).pack(side="left", padx=5)

    ttk.Label(nav_frame, text="Cycle:", width=10).pack(side="left", padx=(20, 5))
    app.fs_cycle_var = tk.StringVar(value="")
    app.fs_cycle_combo = ttk.Combobox(nav_frame, state="disabled", width=30, textvariable=app.fs_cycle_var)
    app.fs_cycle_combo.pack(side="left", padx=5)
    app.fs_cycle_combo.bind("<<ComboboxSelected>>", lambda e: _fs_show_selected_cycle(app))

    app.fs_viz_status = tk.StringVar(value="No data to visualize")
    ttk.Label(nav_frame, textvariable=app.fs_viz_status, foreground="#666").pack(side="left", padx=15)

    # Plot area
    from powertech_tools.config.theme import PowertechTheme
    app.fs_fig = plt.Figure(figsize=(14, 8), dpi=100)
    app.fs_fig.patch.set_facecolor('#1a1a2e')
    app.fs_canvas = FigureCanvasTkAgg(app.fs_fig, master=viz_card)
    app.fs_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    toolbar = NavigationToolbar2Tk(app.fs_canvas, viz_card)
    toolbar.update()

    # Store cycle data for visualization
    app.fs_cycle_data = []
    app.fs_current_cycle_idx = 0

    # Bind arrow keys for navigation
    app.bind("<Left>", lambda e: _fs_show_cycle(app, -1))
    app.bind("<Right>", lambda e: _fs_show_cycle(app, 1))


def _fs_choose_files(app):
    """Handle file selection for fuel systems validation"""
    paths = filedialog.askopenfilenames(
        title="Select cycle TXT files",
        filetypes=[("Text/Log", "*.txt *.log *.dat"), ("All", "*.*")]
    )
    if not paths:
        return

    try:
        app.fs_files = sorted(list(paths), key=lambda p: natural_sort_key(os.path.basename(p)))
        app.fs_files_label.set(f"✓ {len(app.fs_files)} files selected")

        # Read headers from first file
        headers, _, _, _ = read_headers_only(app.fs_files[0])
        app.fs_column_headers = headers

        # Update column dropdowns
        app.cb_fs_time["values"] = headers
        app.cb_fs_ptank["values"] = headers
        app.cb_fs_tfuel["values"] = headers
        app.cb_fs_soc["values"] = headers
        app.cb_fs_time["state"] = "readonly"
        app.cb_fs_ptank["state"] = "readonly"
        app.cb_fs_tfuel["state"] = "readonly"
        app.cb_fs_soc["state"] = "readonly"

        # Auto-select common columns
        headers_lower = [h.lower() for h in headers]

        if "time" in headers_lower:
            app.fs_time_col.set(headers[headers_lower.index("time")])
        elif "elapsed" in headers_lower:
            app.fs_time_col.set(headers[headers_lower.index("elapsed")])

        if "ptank" in headers_lower:
            app.fs_ptank_col.set(headers[headers_lower.index("ptank")])

        if "tfuel" in headers_lower:
            app.fs_tfuel_col.set(headers[headers_lower.index("tfuel")])

        if "soc" in headers_lower:
            app.fs_soc_col.set(headers[headers_lower.index("soc")])

        # Build parameter selection UI
        _fs_build_param_checkboxes(app, headers)

        app.fs_status.set("Ready to configure validation")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read files: {e}")
        app.fs_files = []
        app.fs_files_label.set("No files selected")


def _fs_build_param_checkboxes(app, headers: List[str]):
    """Build parameter selection checkboxes with min/max bounds"""
    # Clear existing widgets
    for widget in app.fs_param_frame.winfo_children():
        widget.destroy()

    app.fs_param_vars = {}
    app.fs_param_min_vars = {}
    app.fs_param_max_vars = {}

    # Create scrollable canvas
    canvas = tk.Canvas(app.fs_param_frame, height=250, bg="white")
    scrollbar = ttk.Scrollbar(app.fs_param_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Header
    header_frame = ttk.Frame(scrollable_frame)
    header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=(0, 5))
    ttk.Label(header_frame, text="Parameter", width=25, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
    ttk.Label(header_frame, text="Min", width=12, font=("Arial", 9, "bold")).grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(header_frame, text="Max", width=12, font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="w", padx=5)

    # Skip time, ptank columns (handled separately)
    # Include tfuel - it has both timing check AND bounds check
    exclude_cols = {"time", "elapsed", "ptank"}
    param_headers = [h for h in headers if h.lower() not in exclude_cols]

    # Create rows
    for idx, param in enumerate(param_headers, start=1):
        var = tk.BooleanVar(value=True)
        min_var = tk.StringVar(value="")
        max_var = tk.StringVar(value="")

        app.fs_param_vars[param] = var
        app.fs_param_min_vars[param] = min_var
        app.fs_param_max_vars[param] = max_var

        # Add special indicator for tfuel
        param_display = param
        if param.lower() == "tfuel":
            param_display = f"{param} (bounds after window)"

        cb = ttk.Checkbutton(scrollable_frame, text=param_display, variable=var)
        cb.grid(row=idx, column=0, sticky="w", padx=5, pady=2)

        ttk.Entry(scrollable_frame, textvariable=min_var, width=12).grid(row=idx, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(scrollable_frame, textvariable=max_var, width=12).grid(row=idx, column=2, sticky="w", padx=5, pady=2)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    app.fs_param_status.set(f"{len(param_headers)} parameters available")


def _fs_select_all_params(app, select: bool):
    """Select or deselect all parameters"""
    for var in app.fs_param_vars.values():
        var.set(select)


def _fs_refresh_preset_list(app):
    """Refresh the preset dropdown list"""
    preset_names = get_preset_names()
    app.fs_preset_combo["values"] = preset_names
    if preset_names:
        app.fs_preset_var.set(preset_names[0])
    else:
        app.fs_preset_var.set("")


def _fs_save_preset(app):
    """Save current validation settings as a preset"""
    try:
        preset_name = app.fs_preset_name_var.get().strip()
        if not preset_name:
            messagebox.showerror("Error", "Please enter a preset name")
            return

        # Collect settings
        param_limits = {}
        for param, var in app.fs_param_vars.items():
            if var.get():
                min_val = app.fs_param_min_vars[param].get().strip()
                max_val = app.fs_param_max_vars[param].get().strip()

                limits = {}
                if min_val:
                    try:
                        limits['min'] = float(min_val)
                    except ValueError:
                        pass
                if max_val:
                    try:
                        limits['max'] = float(max_val)
                    except ValueError:
                        pass

                if limits:
                    param_limits[param] = limits

        config = {
            'ptank_threshold': app.fs_ptank_threshold.get(),
            'tfuel_target': app.fs_tfuel_target.get(),
            'tfuel_window': app.fs_tfuel_window.get(),
            'param_limits': param_limits
        }

        save_preset(preset_name, config)
        _fs_refresh_preset_list(app)
        app.fs_preset_var.set(preset_name)
        app.fs_preset_status.set(f"✓ Saved '{preset_name}'")
        app.fs_preset_name_var.set("")

        # Clear status after 3 seconds
        app.after(3000, lambda: app.fs_preset_status.set(""))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to save preset: {e}")


def _fs_load_preset(app):
    """Load a preset and apply it to the validation settings"""
    try:
        preset_name = app.fs_preset_var.get().strip()
        if not preset_name:
            messagebox.showerror("Error", "Please select a preset")
            return

        preset_data = get_preset(preset_name)
        if not preset_data:
            messagebox.showerror("Error", f"Preset '{preset_name}' not found")
            return

        # Apply settings
        app.fs_ptank_threshold.set(preset_data.get('ptank_threshold', '2.0'))
        app.fs_tfuel_target.set(preset_data.get('tfuel_target', '-30'))
        app.fs_tfuel_window.set(preset_data.get('tfuel_window', '30'))

        param_limits = preset_data.get('param_limits', {})

        # Clear all parameters first
        for var in app.fs_param_vars.values():
            var.set(False)
        for var in app.fs_param_min_vars.values():
            var.set("")
        for var in app.fs_param_max_vars.values():
            var.set("")

        # Apply parameter limits
        for param, limits in param_limits.items():
            if param in app.fs_param_vars:
                app.fs_param_vars[param].set(True)
                if 'min' in limits:
                    app.fs_param_min_vars[param].set(str(limits['min']))
                if 'max' in limits:
                    app.fs_param_max_vars[param].set(str(limits['max']))

        app.fs_preset_status.set(f"✓ Loaded '{preset_name}'")
        app.after(3000, lambda: app.fs_preset_status.set(""))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load preset: {e}")


def _fs_delete_preset(app):
    """Delete the selected preset"""
    try:
        preset_name = app.fs_preset_var.get().strip()
        if not preset_name:
            messagebox.showerror("Error", "Please select a preset to delete")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Delete preset '{preset_name}'?"):
            return

        delete_preset(preset_name)
        _fs_refresh_preset_list(app)
        app.fs_preset_status.set(f"✓ Deleted '{preset_name}'")
        app.after(3000, lambda: app.fs_preset_status.set(""))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete preset: {e}")


def _fs_validate(app):
    """Execute fuel systems validation"""
    try:
        if not app.fs_files:
            messagebox.showerror("Error", "Please select cycle files first")
            return

        # Get column selections
        time_col = app.fs_time_col.get().strip()
        ptank_col = app.fs_ptank_col.get().strip()
        tfuel_col = app.fs_tfuel_col.get().strip()

        if not time_col or not ptank_col or not tfuel_col:
            messagebox.showerror("Error", "Please select Time, Ptank, and tfuel columns")
            return

        # Get thresholds
        try:
            ptank_threshold = float(app.fs_ptank_threshold.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Ptank threshold. Please enter a number.")
            return

        enable_tfuel_check = app.fs_enable_tfuel_check.get()
        tfuel_target = 0.0
        tfuel_window = 0.0
        if enable_tfuel_check:
            try:
                tfuel_target = float(app.fs_tfuel_target.get())
                tfuel_window = float(app.fs_tfuel_window.get())
            except ValueError:
                messagebox.showerror("Error", "tfuel check is enabled but target/window values are invalid.")
                return

        # Fill end mode
        end_mode = app.fs_end_mode.get()
        soc_col = app.fs_soc_col.get().strip() if end_mode == "SOC" else None
        soc_threshold = 100.0
        if end_mode == "SOC":
            if not soc_col:
                messagebox.showerror("Error", "SOC end mode selected but no SOC column chosen")
                return
            try:
                soc_threshold = float(app.fs_soc_threshold.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid SOC threshold value.")
                return

        # Ramp rate check
        enable_ramp_check = app.fs_enable_ramp_check.get()
        ramp_limit = None
        if enable_ramp_check:
            ramp_str = app.fs_ramp_limit.get().strip()
            if ramp_str:
                try:
                    ramp_limit = float(ramp_str)
                except ValueError:
                    messagebox.showerror("Error", "Invalid ramp rate limit. Please enter a number or leave blank.")
                    return

        # Get parameter limits
        param_limits = {}
        for param, var in app.fs_param_vars.items():
            if var.get():
                min_val = app.fs_param_min_vars[param].get().strip()
                max_val = app.fs_param_max_vars[param].get().strip()

                limits = {}
                if min_val:
                    try:
                        limits['min'] = float(min_val)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid min value for {param}")
                        return
                if max_val:
                    try:
                        limits['max'] = float(max_val)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid max value for {param}")
                        return

                if limits:
                    param_limits[param] = limits

        # Run validation
        app.fs_results = []
        app.fs_cycle_data = []
        app.fs_results_text.delete("1.0", tk.END)
        app.fs_results_text.insert(tk.END, "Validating files...\n\n")
        app.fs_status.set("Validating...")
        app.update_idletasks()

        # Store configuration for visualization
        validation_config = {
            'time_col': time_col,
            'ptank_col': ptank_col,
            'tfuel_col': tfuel_col,
            'param_limits': param_limits,
            'ptank_threshold': ptank_threshold,
            'tfuel_target': tfuel_target,
            'tfuel_window': tfuel_window
        }

        for i, filepath in enumerate(app.fs_files, start=1):
            app.fs_status.set(f"Validating {i}/{len(app.fs_files)}")
            app.update_idletasks()

            result = validate_fuel_system_file(
                filepath,
                time_col,
                ptank_col,
                tfuel_col,
                param_limits,
                ptank_threshold,
                tfuel_target,
                tfuel_window,
                enable_tfuel_check=enable_tfuel_check,
                end_mode=end_mode,
                soc_col=soc_col,
                soc_threshold=soc_threshold,
                enable_ramp_check=enable_ramp_check,
                ramp_limit=ramp_limit
            )

            app.fs_results.append(result)

            # Store cycle data for visualization
            if result['status'] != 'ERROR':
                app.fs_cycle_data.append({
                    'filepath': filepath,
                    'result': result,
                    'config': validation_config
                })

        # Display results
        _fs_display_results(app)

        pass_count = sum(1 for r in app.fs_results if r['status'] == 'PASS')
        fail_count = sum(1 for r in app.fs_results if r['status'] == 'FAIL')
        error_count = sum(1 for r in app.fs_results if r['status'] == 'ERROR')

        app.fs_status.set(f"✓ Complete: {pass_count} passed, {fail_count} failed, {error_count} errors")

        # Setup visualization
        if app.fs_cycle_data:
            _fs_setup_visualization(app)

    except Exception as e:
        app.fs_status.set("Error")
        messagebox.showerror("Error", f"Validation failed: {e}")


def _fs_display_results(app):
    """Display validation results in the text widget"""
    app.fs_results_text.delete("1.0", tk.END)

    pass_count = sum(1 for r in app.fs_results if r['status'] == 'PASS')
    fail_count = sum(1 for r in app.fs_results if r['status'] == 'FAIL')
    error_count = sum(1 for r in app.fs_results if r['status'] == 'ERROR')

    # Summary
    app.fs_results_text.insert(tk.END, "=" * 80 + "\n")
    app.fs_results_text.insert(tk.END, f"VALIDATION SUMMARY\n")
    app.fs_results_text.insert(tk.END, "=" * 80 + "\n")
    app.fs_results_text.insert(tk.END, f"Total Files: {len(app.fs_results)}\n")
    app.fs_results_text.insert(tk.END, f"PASSED: {pass_count}\n")
    app.fs_results_text.insert(tk.END, f"FAILED: {fail_count}\n")
    app.fs_results_text.insert(tk.END, f"ERRORS: {error_count}\n")
    app.fs_results_text.insert(tk.END, "=" * 80 + "\n\n")

    # Detailed results
    for result in app.fs_results:
        status_symbol = "✓" if result['status'] == 'PASS' else ("✗" if result['status'] == 'FAIL' else "⚠")

        app.fs_results_text.insert(tk.END, f"{status_symbol} {result['file']} - {result['status']}\n")
        app.fs_results_text.insert(tk.END, f"  Fill: {result['cycle_points']} points (of {result['total_points']} total)\n")
        app.fs_results_text.insert(tk.END, f"  tfuel Check: {'PASS' if result['tfuel_check'] else 'FAIL'}\n")
        app.fs_results_text.insert(tk.END, f"    {result['tfuel_message']}\n")

        if result.get('soc_message'):
            soc_icon = "✓" if result.get('soc_reached_100') else "✗"
            app.fs_results_text.insert(tk.END, f"  SOC: {soc_icon} {result['soc_message']}\n")

        if result.get('ramp_message'):
            ramp_status = 'PASS' if result.get('ramp_pass', True) else 'FAIL'
            app.fs_results_text.insert(tk.END, f"  Ramp Rate: {ramp_status}\n")
            app.fs_results_text.insert(tk.END, f"    {result['ramp_message']}\n")

        if result['param_violations']:
            app.fs_results_text.insert(tk.END, f"  Parameter Violations:\n")
            for violation in result['param_violations']:
                app.fs_results_text.insert(tk.END, f"    - {violation}\n")
        else:
            app.fs_results_text.insert(tk.END, f"  Parameter Bounds: All within limits\n")

        app.fs_results_text.insert(tk.END, "\n")


def _fs_export_results(app):
    """Export validation results to formatted text report"""
    if not app.fs_results:
        messagebox.showwarning("Warning", "No results to export. Run validation first.")
        return

    try:
        out_path = filedialog.asksaveasfilename(
            title="Export validation results",
            defaultextension=".txt",
            initialfile="fuel_systems_validation_results.txt",
            filetypes=[("Text File", "*.txt"), ("CSV", "*.csv"), ("All", "*.*")]
        )
        if not out_path:
            return

        # Count results
        total = len(app.fs_results)
        passed = sum(1 for r in app.fs_results if r['status'] == 'PASS')
        failed = sum(1 for r in app.fs_results if r['status'] == 'FAIL')
        errors = sum(1 for r in app.fs_results if r['status'] == 'ERROR')

        with open(out_path, "w", encoding="utf-8") as f:
            # Header with branding
            f.write("=" * 80 + "\n")
            f.write("                  JERRY - HITT TEAM ANALYSIS TOOL\n")
            f.write("                   FUEL SYSTEMS VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")

            # Summary section
            f.write("VALIDATION SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Files: {total}\n")
            f.write(f"PASSED: {passed}\n")
            f.write(f"FAILED: {failed}\n")
            f.write(f"ERRORS: {errors}\n")
            f.write("=" * 80 + "\n\n")

            # Detailed results
            for idx, result in enumerate(app.fs_results, 1):
                file = result['file']
                status = result['status']
                tfuel_check = "PASS" if result['tfuel_check'] else "FAIL"
                tfuel_msg = result['tfuel_message']
                violations = result['param_violations']
                cycle_pts = result['cycle_points']
                total_pts = result['total_points']

                # Status symbol
                symbol = "✓" if status == "PASS" else "✗"

                f.write(f"{symbol} {file} - {status}\n")
                f.write(f"  Cycle: {cycle_pts} points (of {total_pts} total)\n")
                f.write(f"  tfuel Check: {tfuel_check}\n")
                f.write(f"    {tfuel_msg}\n")

                if violations:
                    f.write(f"  Parameter Bounds:\n")
                    for v in violations:
                        f.write(f"    • {v}\n")
                else:
                    f.write(f"  Parameter Bounds: All within limits\n")

                f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")

        messagebox.showinfo("Success", f"Results exported to:\n{out_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to export results: {e}")


def _fs_setup_visualization(app):
    """Setup cycle visualization after validation"""
    # Populate cycle dropdown
    cycle_names = [os.path.basename(d['filepath']) for d in app.fs_cycle_data]
    app.fs_cycle_combo["values"] = cycle_names
    app.fs_cycle_combo["state"] = "readonly"

    # Show first cycle
    app.fs_current_cycle_idx = 0
    app.fs_cycle_var.set(cycle_names[0])
    _fs_plot_cycle(app, 0)


def _fs_show_cycle(app, direction: int):
    """Navigate to previous or next cycle"""
    if not app.fs_cycle_data:
        return

    app.fs_current_cycle_idx += direction

    # Wrap around
    if app.fs_current_cycle_idx < 0:
        app.fs_current_cycle_idx = len(app.fs_cycle_data) - 1
    elif app.fs_current_cycle_idx >= len(app.fs_cycle_data):
        app.fs_current_cycle_idx = 0

    # Update dropdown and plot
    cycle_names = app.fs_cycle_combo["values"]
    app.fs_cycle_var.set(cycle_names[app.fs_current_cycle_idx])
    _fs_plot_cycle(app, app.fs_current_cycle_idx)


def _fs_show_selected_cycle(app):
    """Show cycle selected from dropdown"""
    if not app.fs_cycle_data:
        return

    cycle_name = app.fs_cycle_var.get()
    cycle_names = app.fs_cycle_combo["values"]

    if cycle_name in cycle_names:
        app.fs_current_cycle_idx = cycle_names.index(cycle_name)
        _fs_plot_cycle(app, app.fs_current_cycle_idx)


def _fs_plot_cycle(app, cycle_idx: int):
    """Plot a specific cycle with all validated parameters"""
    if cycle_idx < 0 or cycle_idx >= len(app.fs_cycle_data):
        return

    from powertech_tools.config.theme import PowertechTheme
    from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers
    import pandas as pd

    try:
        cycle_info = app.fs_cycle_data[cycle_idx]
        filepath = cycle_info['filepath']
        result = cycle_info['result']
        config = cycle_info['config']

        # Load full cycle data
        df = load_table_allow_duplicate_headers(filepath)

        # Get cycle boundaries (for marking on plot)
        start_idx = result['cycle_start_idx']
        end_idx = result['cycle_end_idx']

        if start_idx is None or end_idx is None:
            app.fs_viz_status.set("Error: Could not determine cycle boundaries")
            return

        # Use ENTIRE dataframe for plotting, not just the detected cycle portion
        cycle_df = df.copy()

        # Get time column - handle both numeric and datetime formats
        time_col = config['time_col']
        try:
            time = pd.to_numeric(cycle_df[time_col], errors='coerce')
            # If all values are NaN, it's probably datetime format
            if time.isna().all():
                time = pd.to_datetime(cycle_df[time_col], errors='coerce')
                # Convert to seconds elapsed from first timestamp
                if not time.isna().all():
                    time = (time - time.iloc[0]).dt.total_seconds()
        except Exception as e:
            time = pd.to_numeric(cycle_df[time_col], errors='coerce')

        # Convert to elapsed time from start of file
        if not time.isna().all():
            start_time = time.iloc[0] if not pd.isna(time.iloc[0]) else 0.0
            time_relative = (time - start_time).values  # Use .values to get numpy array
        else:
            # Fallback: use row numbers as time
            time_relative = cycle_df.index.values * 0.5  # Assume 0.5s sampling

        # Calculate time values at cycle boundaries for marking
        cycle_start_time = time_relative[start_idx] if start_idx < len(time_relative) else 0
        cycle_end_time = time_relative[end_idx] if end_idx < len(time_relative) else time_relative[-1]

        # Clear figure
        app.fs_fig.clear()

        # Get parameters to plot
        param_limits = config['param_limits']
        tfuel_col = config['tfuel_col']
        tfuel_window = config['tfuel_window']
        tfuel_target = config['tfuel_target']

        # Dark theme colors
        DARK_BG = '#1a1a2e'
        PLOT_BG = '#16213e'
        GRID_COLOR = '#334155'
        TEXT_COLOR = '#e2e8f0'
        TEXT_DIM = '#94a3b8'

        # Bright contrasting line colors for dark background
        dark_line_colors = [
            '#00d4ff',  # Cyan
            '#ff6bcb',  # Pink
            '#00ff88',  # Green
            '#ffd93d',  # Yellow
            '#ff8a50',  # Orange
            '#a78bfa',  # Purple
            '#34d399',  # Emerald
            '#f472b6',  # Rose
            '#60a5fa',  # Blue
            '#fb923c',  # Amber
            '#c084fc',  # Violet
            '#4ade80',  # Lime
        ]

        app.fs_fig.patch.set_facecolor(DARK_BG)

        # Create single plot for ALL parameters
        ax = app.fs_fig.add_subplot(1, 1, 1)

        # Get ALL columns to plot (exclude Time column)
        plot_params = [col for col in cycle_df.columns if col != time_col]

        # Plot all parameters with bright colors on dark background
        for i, param in enumerate(plot_params):
            try:
                param_data = pd.to_numeric(cycle_df[param], errors='coerce').values
                if not pd.isna(param_data).all():
                    color = dark_line_colors[i % len(dark_line_colors)]
                    ax.plot(time_relative, param_data, linewidth=1.0, label=param, alpha=0.85, color=color)
            except Exception:
                pass

        # Mark cycle boundaries with vertical lines
        ax.axvline(cycle_start_time, linestyle='-', linewidth=2, color='#00ff88', alpha=0.8, label='Cycle start (fill begins)')
        ax.axvline(cycle_end_time, linestyle='-', linewidth=2, color='#c084fc', alpha=0.8, label='Cycle end (fill ends)')

        # Mark tfuel time window boundary (relative to cycle start)
        tfuel_window_time = cycle_start_time + tfuel_window
        ax.axvline(tfuel_window_time, linestyle='--', linewidth=1.5, color='#ffd93d', alpha=0.8, label=f'Tfuel window ({tfuel_window}s from start)')

        # Show tfuel target
        ax.axhline(tfuel_target, linestyle=':', linewidth=1.5, color='#ff4d4d', alpha=0.8, label=f'Tfuel target ({tfuel_target}°C)')

        # Dark theme axis styling
        ax.set_ylim(-90, 105)
        ax.set_xlabel("Time from cycle start (s)", fontsize=10, fontweight='bold', color=TEXT_COLOR)
        ax.set_ylabel("Value", fontsize=10, fontweight='bold', color=TEXT_COLOR)
        ax.set_title("All Parameters", fontsize=11, fontweight="bold", color='#00d4ff')
        ax.grid(True, alpha=0.25, linestyle='--', color=GRID_COLOR)
        ax.set_facecolor(PLOT_BG)
        ax.tick_params(colors=TEXT_DIM, which='both')
        ax.spines['bottom'].set_color(GRID_COLOR)
        ax.spines['top'].set_color(GRID_COLOR)
        ax.spines['left'].set_color(GRID_COLOR)
        ax.spines['right'].set_color(GRID_COLOR)
        legend = ax.legend(fontsize=7, loc='best', ncol=2, facecolor=DARK_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)

        # Overall title
        status_color = '#00ff88' if result['status'] == 'PASS' else '#ff4d4d'
        app.fs_fig.suptitle(
            f"Cycle {cycle_idx + 1}/{len(app.fs_cycle_data)}: {os.path.basename(filepath)} - {result['status']}",
            fontsize=12,
            fontweight='bold',
            color=status_color
        )

        app.fs_fig.tight_layout()
        app.fs_canvas.draw()

        # Update status
        app.fs_viz_status.set(f"Showing cycle {cycle_idx + 1} of {len(app.fs_cycle_data)}")

    except Exception as e:
        app.fs_viz_status.set(f"Error plotting cycle: {e}")
        messagebox.showerror("Visualization Error", f"Failed to plot cycle: {e}")
