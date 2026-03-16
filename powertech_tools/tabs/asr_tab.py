# ASR (Accelerated Stress Rupture) Validation tab
# Validates cumulative time within value bands for ASR testing

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict

import pandas as pd

from powertech_tools.utils.helpers import safe_float, ScrollableFrame, natural_sort_key
from powertech_tools.data.asr_validator import (
    validate_asr_temperature,
    format_duration,
    load_asr_data_from_file
)


def build_tab(parent, app):
    """
    Build the ASR validation tab UI.

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

    title_label = ttk.Label(f, text="ASR Validation", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Accelerated Stress Rupture - Calculate cumulative time within value bands for multiple parameters",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection - MULTIPLE FILES
    card1 = ttk.LabelFrame(f, text="Step 1: Load Test Data", padding=20)
    card1.pack(fill="x", pady=(0, 12))

    app.asr_files = []
    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x")

    ttk.Button(
        btn_frame,
        text="Load TXT/CSV Files",
        command=lambda: _asr_choose_files(app),
        style='Action.TButton'
    ).pack(side="left", padx=(0, 10))

    app.asr_files_label = tk.StringVar(value="No files selected")
    ttk.Label(btn_frame, textvariable=app.asr_files_label, style='Status.TLabel').pack(side="left", padx=10)

    # Time column selection
    card2 = ttk.LabelFrame(f, text="Step 2: Select Time Column", padding=20)
    card2.pack(fill="x", pady=(0, 12))

    time_row = ttk.Frame(card2)
    time_row.pack(fill="x", pady=5)
    ttk.Label(time_row, text="Time Column:", width=20).pack(side="left")
    app.asr_time_col = tk.StringVar(value="")
    app.cb_asr_time = ttk.Combobox(time_row, state="disabled", width=35, textvariable=app.asr_time_col, values=[])
    app.cb_asr_time.pack(side="left", padx=10)

    # Target duration (optional reference)
    target_row = ttk.Frame(card2)
    target_row.pack(fill="x", pady=5)
    ttk.Label(target_row, text="Target Duration (optional):", width=20).pack(side="left")
    app.asr_target_hours = tk.StringVar(value="22")
    ttk.Entry(target_row, textvariable=app.asr_target_hours, width=15).pack(side="left", padx=10)
    ttk.Label(target_row, text="hours").pack(side="left")

    # Parameters selection with bands
    card3 = ttk.LabelFrame(f, text="Step 3: Select Parameters & Set Bands", padding=15)
    card3.pack(fill="both", expand=True, pady=(0, 12))

    ttk.Label(
        card3,
        text="Select parameters to validate and set min/max bands for each:",
        style='Subtitle.TLabel'
    ).pack(anchor="w", pady=(0, 10))

    # Scrollable frame for parameter checkboxes with bands
    app.asr_param_frame = ttk.Frame(card3)
    app.asr_param_frame.pack(fill="both", expand=True)

    # Selection buttons
    btn_row = ttk.Frame(card3)
    btn_row.pack(fill="x", pady=(10, 0))
    ttk.Button(btn_row, text="Select All", command=lambda: _select_all_params(app, True)).pack(side="left", padx=5)
    ttk.Button(btn_row, text="Deselect All", command=lambda: _select_all_params(app, False)).pack(side="left")

    # Actions
    card4 = ttk.LabelFrame(f, text="Step 4: Run Validation", padding=20)
    card4.pack(fill="x", pady=(0, 12))

    action_frame = ttk.Frame(card4)
    action_frame.pack(fill="x")

    ttk.Button(
        action_frame,
        text="CALCULATE ASR DURATION",
        command=lambda: _asr_validate(app),
        style='Action.TButton'
    ).pack(side="left", padx=(0, 10))

    ttk.Button(
        action_frame,
        text="EXPORT TO EXCEL",
        command=lambda: _asr_export_excel(app)
    ).pack(side="left", padx=(0, 10))

    app.asr_status = tk.StringVar(value="")
    ttk.Label(action_frame, textvariable=app.asr_status, style='Status.TLabel').pack(side="left", padx=15)

    # Results
    card5 = ttk.LabelFrame(f, text="ASR Validation Results", padding=15)
    card5.pack(fill="both", expand=True)

    app.asr_results_text = tk.Text(
        card5,
        height=15,
        wrap="none",
        bg="white",
        fg=PowertechTheme.TEXT_PRIMARY,
        font=(PowertechTheme.FONT_FAMILY, 10)
    )
    app.asr_results_text.pack(fill="both", expand=True)

    # Scrollbars for results
    xscroll = ttk.Scrollbar(card5, orient="horizontal", command=app.asr_results_text.xview)
    xscroll.pack(fill="x")
    app.asr_results_text.configure(xscrollcommand=xscroll.set)

    # Store data
    app.asr_df = None
    app.asr_columns = []
    app.asr_param_vars = {}
    app.asr_param_min_vars = {}
    app.asr_param_max_vars = {}
    app.asr_results = {}  # Store results for each parameter


def _asr_choose_files(app):
    """Load multiple TXT/CSV files for ASR validation"""
    paths = filedialog.askopenfilenames(
        title="Select ASR test data files",
        filetypes=[("Text/CSV", "*.txt *.csv *.log *.dat *.tsv"), ("All", "*.*")]
    )
    if not paths:
        return

    try:
        # Sort files naturally
        app.asr_files = sorted(list(paths), key=lambda p: natural_sort_key(os.path.basename(p)))
        app.asr_files_label.set(f"{len(app.asr_files)} files selected")

        # Load and concatenate all files
        all_dfs = []
        columns = None

        for i, path in enumerate(app.asr_files):
            df, cols = load_asr_data_from_file(path)
            df['_file_index'] = i
            df['_file_name'] = os.path.basename(path)
            all_dfs.append(df)

            if columns is None:
                columns = cols

        # Concatenate all data
        app.asr_df = pd.concat(all_dfs, ignore_index=True)
        app.asr_columns = columns

        # Update time column dropdown
        app.cb_asr_time["values"] = columns
        app.cb_asr_time["state"] = "readonly"

        # Auto-select time column
        time_candidates = ['time', 'Time', 'TIME', 't', 'T', 'Elapsed Time', 'Elapsed_Time']
        for tc in time_candidates:
            if tc in columns:
                app.asr_time_col.set(tc)
                break
        else:
            if columns:
                app.asr_time_col.set(columns[0])

        # Build parameter selection UI with bands
        _build_param_selection(app, columns)

        app.asr_status.set(f"Loaded {len(app.asr_df)} data points from {len(app.asr_files)} files")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load files: {e}")
        import traceback
        traceback.print_exc()


def _build_param_selection(app, columns: List[str]):
    """Build parameter selection UI with individual min/max bands"""
    # Clear existing widgets
    for widget in app.asr_param_frame.winfo_children():
        widget.destroy()

    app.asr_param_vars = {}
    app.asr_param_min_vars = {}
    app.asr_param_max_vars = {}

    # Create scrollable canvas
    canvas = tk.Canvas(app.asr_param_frame, height=200, bg="white")
    scrollbar = ttk.Scrollbar(app.asr_param_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Header row
    header_frame = ttk.Frame(scrollable_frame)
    header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=(0, 5))
    ttk.Label(header_frame, text="Parameter", width=25, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
    ttk.Label(header_frame, text="Min", width=12, font=("Arial", 9, "bold")).grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(header_frame, text="Max", width=12, font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="w", padx=5)

    # Exclude time-like columns from parameter list
    exclude_cols = {"time", "elapsed", "t", "_file_index", "_file_name"}
    param_columns = [c for c in columns if c.lower() not in exclude_cols]

    # Default band values for common parameters
    default_bands = {
        'tskin': (83, 87),
        'twall': (83, 87),
        'tfluid': (83, 87),
        'tfuel': (83, 87),
        'temp': (83, 87),
        'temperature': (83, 87),
        'ptank': (0, 100),
        'pressure': (0, 100),
    }

    # Create rows for each parameter
    for idx, param in enumerate(param_columns, start=1):
        var = tk.BooleanVar(value=False)  # Not selected by default

        # Get default band values
        param_lower = param.lower()
        default_min, default_max = 83, 87  # Default for temperature-like
        for key, (dmin, dmax) in default_bands.items():
            if key in param_lower:
                default_min, default_max = dmin, dmax
                break

        min_var = tk.StringVar(value=str(default_min))
        max_var = tk.StringVar(value=str(default_max))

        app.asr_param_vars[param] = var
        app.asr_param_min_vars[param] = min_var
        app.asr_param_max_vars[param] = max_var

        row_frame = ttk.Frame(scrollable_frame)
        row_frame.grid(row=idx, column=0, columnspan=4, sticky="ew", padx=5, pady=2)

        cb = ttk.Checkbutton(row_frame, text=param, variable=var, width=25)
        cb.grid(row=0, column=0, sticky="w")

        min_entry = ttk.Entry(row_frame, textvariable=min_var, width=10)
        min_entry.grid(row=0, column=1, padx=5)

        max_entry = ttk.Entry(row_frame, textvariable=max_var, width=10)
        max_entry.grid(row=0, column=2, padx=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Enable mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)


def _select_all_params(app, select: bool):
    """Select or deselect all parameters"""
    for var in app.asr_param_vars.values():
        var.set(select)


def _asr_validate(app):
    """Run ASR validation for all selected parameters"""
    try:
        if app.asr_df is None or app.asr_df.empty:
            messagebox.showerror("Error", "Please load data files first")
            return

        time_col = app.asr_time_col.get().strip()
        if not time_col or time_col not in app.asr_df.columns:
            messagebox.showerror("Error", "Please select a valid time column")
            return

        # Get selected parameters
        selected_params = [p for p, var in app.asr_param_vars.items() if var.get()]
        if not selected_params:
            messagebox.showerror("Error", "Please select at least one parameter to validate")
            return

        # Parse target hours (optional)
        target_hours = safe_float(app.asr_target_hours.get())
        if target_hours == "INVALID":
            target_hours = None

        app.asr_results = {}
        app.asr_results_text.delete("1.0", tk.END)

        results_text = "=" * 70 + "\n"
        results_text += "                    ASR VALIDATION RESULTS\n"
        results_text += f"                    Files: {len(app.asr_files)}\n"
        results_text += "=" * 70 + "\n\n"

        # Validate each selected parameter
        for param in selected_params:
            if param not in app.asr_df.columns:
                continue

            # Get band values
            val_min = safe_float(app.asr_param_min_vars[param].get())
            val_max = safe_float(app.asr_param_max_vars[param].get())

            if val_min == "INVALID" or val_min is None:
                results_text += f"[{param}] ERROR: Invalid minimum value\n\n"
                continue
            if val_max == "INVALID" or val_max is None:
                results_text += f"[{param}] ERROR: Invalid maximum value\n\n"
                continue
            if val_min >= val_max:
                results_text += f"[{param}] ERROR: Min must be less than max\n\n"
                continue

            # Run validation
            summary, detail_df = validate_asr_temperature(
                app.asr_df,
                time_col,
                param,
                val_min,
                val_max,
                time_unit="seconds"
            )

            app.asr_results[param] = {
                'summary': summary,
                'detail_df': detail_df,
                'band': (val_min, val_max)
            }

            # Format results
            total_sec = summary['total_duration']
            in_band_sec = summary['time_in_band']
            in_band_hours = in_band_sec / 3600

            total_fmt = format_duration(total_sec, "auto")
            in_band_fmt = format_duration(in_band_sec, "auto")

            results_text += "-" * 50 + "\n"
            results_text += f"  {param.upper()}\n"
            results_text += "-" * 50 + "\n"
            results_text += f"  Band:           {val_min} - {val_max}\n"
            results_text += f"  Total Duration: {total_fmt}\n"
            results_text += f"  Time IN BAND:   {in_band_fmt} ({summary['percent_in_band']:.2f}%)\n"
            results_text += f"  In Band (hrs):  {in_band_hours:.4f}\n"

            # Target comparison if provided
            if target_hours is not None and target_hours > 0:
                progress = (in_band_hours / target_hours) * 100
                status = "MET" if in_band_hours >= target_hours else "NOT MET"
                results_text += f"  Target:         {target_hours:.2f} hrs - {status} ({progress:.1f}%)\n"

            # Statistics
            stats = summary['temp_stats']
            results_text += f"  Range:          {stats['min']:.2f} - {stats['max']:.2f}\n"
            results_text += f"  Mean:           {stats['mean']:.2f}\n"
            results_text += f"  Excursions:     {summary['excursion_count']}\n"
            results_text += "\n"

        results_text += "=" * 70 + "\n"

        app.asr_results_text.insert(tk.END, results_text)
        app.asr_status.set(f"Validated {len(selected_params)} parameters across {len(app.asr_files)} files")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        import traceback
        traceback.print_exc()


def _asr_export_excel(app):
    """Export ASR results to Excel"""
    try:
        if not app.asr_results:
            messagebox.showerror("Error", "Please run validation first")
            return

        out_path = filedialog.asksaveasfilename(
            title="Save ASR results",
            defaultextension=".xlsx",
            initialfile="asr_validation_results.xlsx",
            filetypes=[("Excel", "*.xlsx"), ("All", "*.*")]
        )
        if not out_path:
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import PatternFill, Font, Alignment
        except ImportError:
            messagebox.showerror("Missing Library", "openpyxl required\n\nInstall: pip install openpyxl")
            return

        wb = Workbook()

        # Summary sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"

        # Header
        header_fill = PatternFill(start_color="1e3a5f", end_color="1e3a5f", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        summary_headers = ["Parameter", "Band Min", "Band Max", "Total (hrs)", "In Band (hrs)",
                         "In Band %", "Min Value", "Max Value", "Mean", "Excursions", "Target Met"]
        ws_summary.append(summary_headers)
        for cell in ws_summary[1]:
            cell.fill = header_fill
            cell.font = header_font

        # Parse target
        target_hours = safe_float(app.asr_target_hours.get())
        if target_hours == "INVALID":
            target_hours = None

        # Add data for each parameter
        for param, data in app.asr_results.items():
            summary = data['summary']
            band = data['band']
            in_band_hours = summary['time_in_band'] / 3600
            total_hours = summary['total_duration'] / 3600
            stats = summary['temp_stats']

            target_met = ""
            if target_hours is not None and target_hours > 0:
                target_met = "Yes" if in_band_hours >= target_hours else "No"

            ws_summary.append([
                param,
                band[0],
                band[1],
                f"{total_hours:.4f}",
                f"{in_band_hours:.4f}",
                f"{summary['percent_in_band']:.2f}%",
                f"{stats['min']:.2f}",
                f"{stats['max']:.2f}",
                f"{stats['mean']:.2f}",
                summary['excursion_count'],
                target_met
            ])

        # Create detail sheet for each parameter
        for param, data in app.asr_results.items():
            # Sanitize sheet name (max 31 chars, no special chars)
            sheet_name = param[:28].replace("/", "_").replace("\\", "_").replace("*", "_")

            ws_detail = wb.create_sheet(f"{sheet_name}_Exc")
            ws_detail.append(["Start Time (s)", "End Time (s)", "Duration (s)", "Min Value", "Max Value"])

            for cell in ws_detail[1]:
                cell.fill = header_fill
                cell.font = header_font

            for exc in data['summary']['excursions']:
                ws_detail.append([
                    exc['start_time'],
                    exc['end_time'],
                    exc['duration'],
                    exc['min_temp'],
                    exc['max_temp']
                ])

        wb.save(out_path)
        messagebox.showinfo("Success", f"Excel file saved:\n{out_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        import traceback
        traceback.print_exc()
