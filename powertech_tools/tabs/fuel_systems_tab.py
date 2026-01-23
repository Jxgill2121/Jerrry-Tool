# Fuel Systems Validation tab - Advanced cycle validation with time-based checks

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict

from powertech_tools.utils.helpers import ScrollableFrame, natural_sort_key
from powertech_tools.utils.fuel_systems_presets import (
    save_preset, delete_preset, get_preset_names, get_preset
)
from powertech_tools.data.fuel_systems_validator import validate_fuel_system_file
from powertech_tools.data.loader import read_headers_only


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

    # Cycle detection settings
    cycle_frame = ttk.LabelFrame(config_frame, text="Cycle Detection (Ptank-based)", padding=10)
    cycle_frame.pack(fill="x", pady=(10, 5))

    ptank_row = ttk.Frame(cycle_frame)
    ptank_row.pack(fill="x", pady=2)
    ttk.Label(ptank_row, text="Ptank Threshold (MPa):").pack(side="left")
    app.fs_ptank_threshold = tk.StringVar(value="2.0")
    ttk.Entry(ptank_row, textvariable=app.fs_ptank_threshold, width=10).pack(side="left", padx=10)
    ttk.Label(ptank_row, text="(Cycle boundaries detected at this pressure)", font=(PowertechTheme.FONT_FAMILY, 8), foreground="#666").pack(side="left", padx=5)

    # tfuel timing check settings
    tfuel_frame = ttk.LabelFrame(config_frame, text="tfuel Timing Check", padding=10)
    tfuel_frame.pack(fill="x", pady=(10, 5))

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
        text="tfuel must reach target temperature within time window from cycle start",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    tfuel_desc.pack(anchor="w", pady=(5, 0))

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
        text="Select parameters to validate and set their min/max bounds. Parameters will be checked throughout the cycle.",
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
    results_card.pack(fill="both", expand=True, pady=(0, 0))

    app.fs_results_text = scrolledtext.ScrolledText(
        results_card,
        height=15,
        font=("Courier New", 9),
        wrap=tk.WORD
    )
    app.fs_results_text.pack(fill="both", expand=True)


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
        app.cb_fs_time["state"] = "readonly"
        app.cb_fs_ptank["state"] = "readonly"
        app.cb_fs_tfuel["state"] = "readonly"

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

    # Skip time, ptank, tfuel columns (they're handled separately)
    exclude_cols = {"time", "elapsed", "ptank", "tfuel"}
    param_headers = [h for h in headers if h.lower() not in exclude_cols]

    # Create rows
    for idx, param in enumerate(param_headers, start=1):
        var = tk.BooleanVar(value=True)
        min_var = tk.StringVar(value="")
        max_var = tk.StringVar(value="")

        app.fs_param_vars[param] = var
        app.fs_param_min_vars[param] = min_var
        app.fs_param_max_vars[param] = max_var

        cb = ttk.Checkbutton(scrollable_frame, text=param, variable=var)
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
            tfuel_target = float(app.fs_tfuel_target.get())
            tfuel_window = float(app.fs_tfuel_window.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid threshold values. Please enter numbers.")
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
        app.fs_results_text.delete("1.0", tk.END)
        app.fs_results_text.insert(tk.END, "Validating files...\n\n")
        app.fs_status.set("Validating...")
        app.update_idletasks()

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
                tfuel_window
            )

            app.fs_results.append(result)

        # Display results
        _fs_display_results(app)

        pass_count = sum(1 for r in app.fs_results if r['status'] == 'PASS')
        fail_count = sum(1 for r in app.fs_results if r['status'] == 'FAIL')
        error_count = sum(1 for r in app.fs_results if r['status'] == 'ERROR')

        app.fs_status.set(f"✓ Complete: {pass_count} passed, {fail_count} failed, {error_count} errors")

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
        app.fs_results_text.insert(tk.END, f"  Cycle: {result['cycle_points']} points (of {result['total_points']} total)\n")
        app.fs_results_text.insert(tk.END, f"  tfuel Check: {'PASS' if result['tfuel_check'] else 'FAIL'}\n")
        app.fs_results_text.insert(tk.END, f"    {result['tfuel_message']}\n")

        if result['param_violations']:
            app.fs_results_text.insert(tk.END, f"  Parameter Violations:\n")
            for violation in result['param_violations']:
                app.fs_results_text.insert(tk.END, f"    - {violation}\n")
        else:
            app.fs_results_text.insert(tk.END, f"  Parameter Bounds: All within limits\n")

        app.fs_results_text.insert(tk.END, "\n")


def _fs_export_results(app):
    """Export validation results to CSV"""
    if not app.fs_results:
        messagebox.showwarning("Warning", "No results to export. Run validation first.")
        return

    try:
        out_path = filedialog.asksaveasfilename(
            title="Export validation results",
            defaultextension=".csv",
            initialfile="fuel_systems_validation_results.csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")]
        )
        if not out_path:
            return

        with open(out_path, "w", encoding="utf-8") as f:
            # Header
            f.write("File,Status,tfuel Check,tfuel Message,Parameter Violations,Cycle Points,Total Points\n")

            # Data rows
            for result in app.fs_results:
                file = result['file']
                status = result['status']
                tfuel_check = "PASS" if result['tfuel_check'] else "FAIL"
                tfuel_msg = result['tfuel_message'].replace(',', ';')
                violations = " | ".join(result['param_violations']).replace(',', ';')
                cycle_pts = result['cycle_points']
                total_pts = result['total_points']

                f.write(f'"{file}",{status},{tfuel_check},"{tfuel_msg}","{violations}",{cycle_pts},{total_pts}\n')

        messagebox.showinfo("Success", f"Results exported to:\n{out_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to export results: {e}")
