# Cycle Viewer tab - Per-cycle visualization with spec sheet limits

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from powertech_tools.utils.helpers import ScrollableFrame
from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers, read_headers_only


def build_tab(parent, app):
    """
    Build the Cycle Viewer tab UI.

    Args:
        parent: Parent frame for this tab
        app: Main application instance (for storing state)
    """
    from powertech_tools.config.theme import PowertechTheme

    scrollable = ScrollableFrame(parent)
    scrollable.pack(fill="both", expand=True)
    f = ttk.Frame(scrollable.content)
    f.pack(fill="both", expand=True, padx=15, pady=15)

    # Title
    title_label = ttk.Label(f, text="Cycle Viewer", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Visualize individual cycles with Ptank, Tskin, Tfluid, Tair and spec sheet limits",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # Initialize state
    app.cv_df = None
    app.cv_files = []
    app.cv_cycle_values = []

    # File selection card
    card1 = ttk.LabelFrame(f, text="Data Source", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x", pady=(0, 10))

    ttk.Button(
        btn_frame,
        text="Load File with Cycle Column",
        command=lambda: _cv_load_single_file(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Button(
        btn_frame,
        text="Load Multiple TXT Files (1 per cycle)",
        command=lambda: _cv_load_multiple_files(app)
    ).pack(side="left", padx=10)

    app.cv_file_label = tk.StringVar(value="No file loaded")
    ttk.Label(btn_frame, textvariable=app.cv_file_label, style='Status.TLabel').pack(side="left", padx=15)

    # Column selection
    col_frame = ttk.Frame(card1)
    col_frame.pack(fill="x", pady=5)

    ttk.Label(col_frame, text="Time Column:", width=12).pack(side="left")
    app.cv_time_col = tk.StringVar(value="")
    app.cb_cv_time = ttk.Combobox(col_frame, state="disabled", width=15, textvariable=app.cv_time_col, values=[])
    app.cb_cv_time.pack(side="left", padx=5)

    ttk.Label(col_frame, text="Cycle Column:", width=12).pack(side="left", padx=(15, 0))
    app.cv_cycle_col = tk.StringVar(value="")
    app.cb_cv_cycle = ttk.Combobox(col_frame, state="disabled", width=15, textvariable=app.cv_cycle_col, values=[])
    app.cb_cv_cycle.pack(side="left", padx=5)
    app.cb_cv_cycle.bind("<<ComboboxSelected>>", lambda e: _cv_update_cycle_list(app))

    # Test name entry
    name_frame = ttk.Frame(card1)
    name_frame.pack(fill="x", pady=5)
    ttk.Label(name_frame, text="Test Name:", width=12).pack(side="left")
    app.cv_test_name = tk.StringVar(value="")
    ttk.Entry(name_frame, textvariable=app.cv_test_name, width=60).pack(side="left", padx=5)
    ttk.Label(name_frame, text="(appears in plot title)", font=(PowertechTheme.FONT_FAMILY, 8), foreground="#666").pack(side="left")

    # Channel mapping card
    card2 = ttk.LabelFrame(f, text="Channel Mapping", padding=20)
    card2.pack(fill="x", pady=(0, 15))

    ch_desc = ttk.Label(
        card2,
        text="Select columns for each parameter (leave blank to skip)",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    ch_desc.pack(anchor="w", pady=(0, 10))

    ch_frame = ttk.Frame(card2)
    ch_frame.pack(fill="x")

    # Ptank
    ttk.Label(ch_frame, text="Ptank:", width=8).grid(row=0, column=0, sticky="w")
    app.cv_ptank_col = tk.StringVar(value="")
    app.cb_cv_ptank = ttk.Combobox(ch_frame, state="disabled", width=18, textvariable=app.cv_ptank_col, values=[])
    app.cb_cv_ptank.grid(row=0, column=1, padx=5, pady=2)

    # Tskin
    ttk.Label(ch_frame, text="Tskin:", width=8).grid(row=0, column=2, sticky="w", padx=(15, 0))
    app.cv_tskin_col = tk.StringVar(value="")
    app.cb_cv_tskin = ttk.Combobox(ch_frame, state="disabled", width=18, textvariable=app.cv_tskin_col, values=[])
    app.cb_cv_tskin.grid(row=0, column=3, padx=5, pady=2)

    # Tfluid
    ttk.Label(ch_frame, text="Tfluid:", width=8).grid(row=1, column=0, sticky="w")
    app.cv_tfluid_col = tk.StringVar(value="")
    app.cb_cv_tfluid = ttk.Combobox(ch_frame, state="disabled", width=18, textvariable=app.cv_tfluid_col, values=[])
    app.cb_cv_tfluid.grid(row=1, column=1, padx=5, pady=2)

    # Tair
    ttk.Label(ch_frame, text="Tair:", width=8).grid(row=1, column=2, sticky="w", padx=(15, 0))
    app.cv_tair_col = tk.StringVar(value="")
    app.cb_cv_tair = ttk.Combobox(ch_frame, state="disabled", width=18, textvariable=app.cv_tair_col, values=[])
    app.cb_cv_tair.grid(row=1, column=3, padx=5, pady=2)

    # Spec sheet limits card
    card3 = ttk.LabelFrame(f, text="Spec Sheet Limits (Dashed Lines)", padding=20)
    card3.pack(fill="x", pady=(0, 15))

    limits_desc = ttk.Label(
        card3,
        text="Enter limit values to draw horizontal dashed lines on the plot",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    limits_desc.pack(anchor="w", pady=(0, 10))

    limits_frame = ttk.Frame(card3)
    limits_frame.pack(fill="x")

    # Pressure limits (high)
    ttk.Label(limits_frame, text="Phigh_min:", width=10).grid(row=0, column=0, sticky="w")
    app.cv_phigh_min = tk.StringVar(value="")
    ttk.Entry(limits_frame, textvariable=app.cv_phigh_min, width=10).grid(row=0, column=1, padx=5, pady=2)

    ttk.Label(limits_frame, text="Phigh_max:", width=10).grid(row=0, column=2, sticky="w", padx=(15, 0))
    app.cv_phigh_max = tk.StringVar(value="")
    ttk.Entry(limits_frame, textvariable=app.cv_phigh_max, width=10).grid(row=0, column=3, padx=5, pady=2)

    # Pressure limits (low)
    ttk.Label(limits_frame, text="Plow_min:", width=10).grid(row=1, column=0, sticky="w")
    app.cv_plow_min = tk.StringVar(value="")
    ttk.Entry(limits_frame, textvariable=app.cv_plow_min, width=10).grid(row=1, column=1, padx=5, pady=2)

    ttk.Label(limits_frame, text="Plow_max:", width=10).grid(row=1, column=2, sticky="w", padx=(15, 0))
    app.cv_plow_max = tk.StringVar(value="")
    ttk.Entry(limits_frame, textvariable=app.cv_plow_max, width=10).grid(row=1, column=3, padx=5, pady=2)

    # Temperature limits
    ttk.Label(limits_frame, text="T_min:", width=10).grid(row=2, column=0, sticky="w")
    app.cv_t_min = tk.StringVar(value="")
    ttk.Entry(limits_frame, textvariable=app.cv_t_min, width=10).grid(row=2, column=1, padx=5, pady=2)

    ttk.Label(limits_frame, text="T_max:", width=10).grid(row=2, column=2, sticky="w", padx=(15, 0))
    app.cv_t_max = tk.StringVar(value="")
    ttk.Entry(limits_frame, textvariable=app.cv_t_max, width=10).grid(row=2, column=3, padx=5, pady=2)

    # Mode and cycle selection card
    card4 = ttk.LabelFrame(f, text="View Mode", padding=20)
    card4.pack(fill="x", pady=(0, 15))

    mode_frame = ttk.Frame(card4)
    mode_frame.pack(fill="x", pady=(0, 10))

    app.cv_mode = tk.StringVar(value="per_cycle")
    ttk.Radiobutton(
        mode_frame,
        text="Per-Cycle (single cycle)",
        variable=app.cv_mode,
        value="per_cycle",
        command=lambda: _cv_mode_changed(app)
    ).pack(side="left")

    ttk.Radiobutton(
        mode_frame,
        text="Over Duration",
        variable=app.cv_mode,
        value="duration",
        command=lambda: _cv_mode_changed(app)
    ).pack(side="left", padx=20)

    # Cycle selection row (Per-Cycle mode)
    app.cv_single_row = ttk.Frame(card4)
    app.cv_single_row.pack(fill="x", pady=5)

    ttk.Label(app.cv_single_row, text="Cycle:", width=10).pack(side="left")
    app.cv_selected_cycle = tk.StringVar(value="")
    app.cv_cycle_spinbox = ttk.Combobox(
        app.cv_single_row,
        state="disabled",
        width=15,
        textvariable=app.cv_selected_cycle,
        values=[]
    )
    app.cv_cycle_spinbox.pack(side="left", padx=5)

    ttk.Button(
        app.cv_single_row,
        text="< Prev",
        command=lambda: _cv_navigate_cycle(app, -1)
    ).pack(side="left", padx=5)

    ttk.Button(
        app.cv_single_row,
        text="Next >",
        command=lambda: _cv_navigate_cycle(app, 1)
    ).pack(side="left", padx=5)

    # Duration mode options row
    app.cv_range_row = ttk.Frame(card4)
    ttk.Label(app.cv_range_row, text="Time Unit:", width=10).pack(side="left")
    app.cv_time_unit = tk.StringVar(value="hours")
    ttk.Combobox(
        app.cv_range_row,
        textvariable=app.cv_time_unit,
        values=["seconds", "minutes", "hours"],
        state="readonly",
        width=10
    ).pack(side="left", padx=5)

    # Action buttons
    action_frame = ttk.Frame(card4)
    action_frame.pack(fill="x", pady=(10, 0))

    ttk.Button(
        action_frame,
        text="Plot",
        command=lambda: _cv_plot(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Button(
        action_frame,
        text="Save PNG",
        command=lambda: _cv_save_png(app)
    ).pack(side="left", padx=10)

    app.cv_status = tk.StringVar(value="")
    ttk.Label(action_frame, textvariable=app.cv_status, style='Status.TLabel').pack(side="left", padx=15)

    # Plot area
    plot_card = ttk.LabelFrame(f, text="Visualization", padding=15)
    plot_card.pack(fill="both", expand=True, pady=(0, 0))

    app.cv_fig = plt.Figure(figsize=(14, 8), dpi=100)
    app.cv_fig.patch.set_facecolor('white')
    app.cv_canvas = FigureCanvasTkAgg(app.cv_fig, master=plot_card)
    app.cv_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    toolbar = NavigationToolbar2Tk(app.cv_canvas, plot_card)
    toolbar.update()

    # Keyboard navigation
    app.bind("<Left>", lambda e: _cv_navigate_cycle(app, -1))
    app.bind("<Right>", lambda e: _cv_navigate_cycle(app, 1))


def _cv_mode_changed(app):
    """Handle mode change between per-cycle and duration"""
    mode = app.cv_mode.get()
    if mode == "per_cycle":
        app.cv_range_row.pack_forget()
        app.cv_single_row.pack(fill="x", pady=5)
    else:
        app.cv_single_row.pack_forget()
        app.cv_range_row.pack(fill="x", pady=5)


def _cv_load_single_file(app):
    """Load a single file with Cycle column"""
    path = filedialog.askopenfilename(
        title="Select file with Cycle column",
        filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
    )
    if not path:
        return

    try:
        df = load_table_allow_duplicate_headers(path)
        app.cv_df = df
        app.cv_files = []
        app.cv_file_label.set(os.path.basename(path))

        cols = list(df.columns)
        _cv_setup_columns(app, cols)

        # Auto-detect test name from filename
        basename = os.path.splitext(os.path.basename(path))[0]
        app.cv_test_name.set(basename)

        app.cv_status.set("File loaded")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")


def _cv_load_multiple_files(app):
    """Load multiple TXT files (one per cycle)"""
    paths = filedialog.askopenfilenames(
        title="Select cycle files (one per cycle)",
        filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
    )
    if not paths:
        return

    try:
        app.cv_files = sorted(list(paths))
        app.cv_df = None
        app.cv_file_label.set(f"{len(paths)} files selected")

        # Read headers from first file
        headers, _, _, _ = read_headers_only(paths[0])
        _cv_setup_columns(app, headers)

        # Create synthetic cycle list from filenames
        app.cv_cycle_values = list(range(1, len(paths) + 1))
        app.cv_cycle_spinbox["values"] = app.cv_cycle_values
        app.cv_cycle_spinbox["state"] = "readonly"
        if app.cv_cycle_values:
            app.cv_selected_cycle.set(str(app.cv_cycle_values[0]))

        # Disable cycle column selector (not needed for multi-file mode)
        app.cb_cv_cycle["state"] = "disabled"
        app.cv_cycle_col.set("")

        # Auto-detect test name from first filename
        basename = os.path.splitext(os.path.basename(paths[0]))[0]
        app.cv_test_name.set(basename)

        app.cv_status.set("Files loaded")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load files: {e}")


def _cv_setup_columns(app, cols):
    """Setup column dropdowns with available columns"""
    # Update all comboboxes
    for cb in [app.cb_cv_time, app.cb_cv_cycle, app.cb_cv_ptank,
               app.cb_cv_tskin, app.cb_cv_tfluid, app.cb_cv_tair]:
        cb["values"] = [""] + cols
        cb["state"] = "readonly"

    # Auto-detect columns
    cols_lower = {c.lower(): c for c in cols}

    # Time
    for t in ["time", "elapsed"]:
        if t in cols_lower:
            app.cv_time_col.set(cols_lower[t])
            break

    # Cycle
    for c in ["cycle"]:
        if c in cols_lower:
            app.cv_cycle_col.set(cols_lower[c])
            break

    # Ptank
    for p in ["ptank", "pressure", "p_tank"]:
        if p in cols_lower:
            app.cv_ptank_col.set(cols_lower[p])
            break

    # Tskin
    for t in ["tskin", "t_skin", "skintemp"]:
        if t in cols_lower:
            app.cv_tskin_col.set(cols_lower[t])
            break

    # Tfluid
    for t in ["tfluid", "t_fluid", "tfuel", "fluidtemp"]:
        if t in cols_lower:
            app.cv_tfluid_col.set(cols_lower[t])
            break

    # Tair
    for t in ["tair", "t_air", "tamb", "airtemp", "ambient"]:
        if t in cols_lower:
            app.cv_tair_col.set(cols_lower[t])
            break

    # Update cycle list if we have a single file with cycle column
    _cv_update_cycle_list(app)


def _cv_update_cycle_list(app):
    """Update the cycle selection list based on data"""
    if app.cv_df is None:
        return

    cycle_col = app.cv_cycle_col.get().strip()
    if not cycle_col or cycle_col not in app.cv_df.columns:
        return

    try:
        cycles = pd.to_numeric(app.cv_df[cycle_col], errors='coerce').dropna().unique()
        cycles = sorted([int(c) for c in cycles if not pd.isna(c)])
        app.cv_cycle_values = cycles

        app.cv_cycle_spinbox["values"] = cycles
        app.cv_cycle_spinbox["state"] = "readonly"

        if cycles:
            app.cv_selected_cycle.set(str(cycles[0]))

    except Exception:
        pass


def _cv_navigate_cycle(app, direction):
    """Navigate to previous/next cycle"""
    if not app.cv_cycle_values:
        return

    try:
        current = int(app.cv_selected_cycle.get())
        idx = app.cv_cycle_values.index(current)
        new_idx = idx + direction

        if 0 <= new_idx < len(app.cv_cycle_values):
            app.cv_selected_cycle.set(str(app.cv_cycle_values[new_idx]))
            _cv_plot(app)
    except (ValueError, IndexError):
        pass


def _cv_plot(app):
    """Generate the plot"""
    try:
        mode = app.cv_mode.get()

        if mode == "per_cycle":
            _cv_plot_single_cycle(app)
        else:
            _cv_plot_duration(app)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to plot: {e}")


def _cv_plot_single_cycle(app):
    """Plot a single cycle"""
    # Get cycle data
    if app.cv_files:
        # Multi-file mode
        try:
            cycle_idx = int(app.cv_selected_cycle.get()) - 1
            if cycle_idx < 0 or cycle_idx >= len(app.cv_files):
                messagebox.showerror("Error", "Invalid cycle selection")
                return

            df = load_table_allow_duplicate_headers(app.cv_files[cycle_idx])
            cycle_num = cycle_idx + 1

        except (ValueError, IndexError) as e:
            messagebox.showerror("Error", f"Invalid cycle: {e}")
            return

    elif app.cv_df is not None:
        # Single file mode
        cycle_col = app.cv_cycle_col.get().strip()
        if not cycle_col:
            messagebox.showerror("Error", "Select a Cycle column")
            return

        try:
            cycle_num = int(app.cv_selected_cycle.get())
        except ValueError:
            messagebox.showerror("Error", "Select a cycle")
            return

        app.cv_df[cycle_col] = pd.to_numeric(app.cv_df[cycle_col], errors='coerce')
        df = app.cv_df[app.cv_df[cycle_col] == cycle_num].copy()

        if df.empty:
            messagebox.showerror("Error", f"No data for cycle {cycle_num}")
            return

    else:
        messagebox.showerror("Error", "Load data first")
        return

    # Get time column
    time_col = app.cv_time_col.get().strip()
    if time_col and time_col in df.columns:
        time_data = pd.to_numeric(df[time_col], errors='coerce').values
        # Make time relative to start
        time_data = time_data - time_data[0]
    else:
        time_data = np.arange(len(df))

    # Plot
    _cv_render_plot(app, df, time_data, cycle_num, time_unit="seconds")


def _cv_plot_duration(app):
    """Plot all data over duration with time in hours"""
    if app.cv_df is None and not app.cv_files:
        messagebox.showerror("Error", "Load data first")
        return

    if app.cv_files:
        # Multi-file mode - concatenate ALL files
        dfs = []
        for filepath in app.cv_files:
            df_part = load_table_allow_duplicate_headers(filepath)
            dfs.append(df_part)

        if not dfs:
            messagebox.showerror("Error", "No files loaded")
            return

        df = pd.concat(dfs, ignore_index=True)

    else:
        # Single file mode - use all data
        df = app.cv_df.copy()

    if df.empty:
        messagebox.showerror("Error", "No data")
        return

    # Get selected time unit
    time_unit = app.cv_time_unit.get() if hasattr(app, 'cv_time_unit') else "hours"

    # Conversion factors from seconds
    unit_divisors = {"seconds": 1.0, "minutes": 60.0, "hours": 3600.0}
    divisor = unit_divisors.get(time_unit, 3600.0)

    # Get time column and convert to selected unit
    time_col = app.cv_time_col.get().strip()
    if time_col and time_col in df.columns:
        time_data = pd.to_numeric(df[time_col], errors='coerce').values
        time_data = time_data - time_data[0]
        time_data = time_data / divisor
    else:
        # Assume 1 row = 1 second, convert to selected unit
        time_data = np.arange(len(df)) / divisor

    _cv_render_plot(app, df, time_data, "Full Duration", time_unit=time_unit)


def _cv_render_plot(app, df, time_data, cycle_label, time_unit="seconds"):
    """Render the actual plot with dual y-axes (pressure left, temperature right)"""
    app.cv_fig.clear()
    ax_pressure = app.cv_fig.add_subplot(1, 1, 1)
    ax_temp = ax_pressure.twinx()  # Second y-axis for temperature

    # Define colors matching the Excel chart style
    colors = {
        'Ptank': '#0066CC',   # Blue
        'Tskin': '#CC6600',   # Brown/orange
        'Tfluid': '#669900',  # Olive green
        'Tair': '#00CCCC',    # Cyan
    }

    limit_colors = {
        'Phigh': '#CC0000',   # Red dashed
        'Plow': '#000066',    # Dark blue dashed
        'T': '#333333',       # Dark gray dashed
    }

    # Collect handles for combined legend
    legend_handles = []
    legend_labels = []

    # Plot Ptank on LEFT axis (pressure)
    ptank_col = app.cv_ptank_col.get().strip()
    if ptank_col and ptank_col in df.columns:
        data = pd.to_numeric(df[ptank_col], errors='coerce').values
        line, = ax_pressure.plot(time_data, data, '-', color=colors['Ptank'], linewidth=1.5, label='Ptank')
        legend_handles.append(line)
        legend_labels.append('Ptank')

    # Plot temperatures on RIGHT axis
    tskin_col = app.cv_tskin_col.get().strip()
    if tskin_col and tskin_col in df.columns:
        data = pd.to_numeric(df[tskin_col], errors='coerce').values
        line, = ax_temp.plot(time_data, data, '-', color=colors['Tskin'], linewidth=1.5, label='Tskin')
        legend_handles.append(line)
        legend_labels.append('Tskin')

    tfluid_col = app.cv_tfluid_col.get().strip()
    if tfluid_col and tfluid_col in df.columns:
        data = pd.to_numeric(df[tfluid_col], errors='coerce').values
        line, = ax_temp.plot(time_data, data, '-', color=colors['Tfluid'], linewidth=1.5, label='Tfluid')
        legend_handles.append(line)
        legend_labels.append('Tfluid')

    tair_col = app.cv_tair_col.get().strip()
    if tair_col and tair_col in df.columns:
        data = pd.to_numeric(df[tair_col], errors='coerce').values
        line, = ax_temp.plot(time_data, data, '-', color=colors['Tair'], linewidth=1.5, label='Tair')
        legend_handles.append(line)
        legend_labels.append('Tair')

    # Plot dashed horizontal lines for limits
    def safe_float(s):
        try:
            return float(s) if s.strip() else None
        except (ValueError, AttributeError):
            return None

    # Pressure limits on LEFT axis
    phigh_min = safe_float(app.cv_phigh_min.get())
    phigh_max = safe_float(app.cv_phigh_max.get())
    if phigh_min is not None:
        line = ax_pressure.axhline(phigh_min, linestyle='--', color=limit_colors['Phigh'], linewidth=1, alpha=0.8)
        legend_handles.append(line)
        legend_labels.append('Phigh_min')
    if phigh_max is not None:
        line = ax_pressure.axhline(phigh_max, linestyle='--', color=limit_colors['Phigh'], linewidth=1, alpha=0.8)
        legend_handles.append(line)
        legend_labels.append('Phigh_max')

    plow_min = safe_float(app.cv_plow_min.get())
    plow_max = safe_float(app.cv_plow_max.get())
    if plow_min is not None:
        line = ax_pressure.axhline(plow_min, linestyle='--', color=limit_colors['Plow'], linewidth=1, alpha=0.8)
        legend_handles.append(line)
        legend_labels.append('Plow_min')
    if plow_max is not None:
        line = ax_pressure.axhline(plow_max, linestyle='--', color=limit_colors['Plow'], linewidth=1, alpha=0.8)
        legend_handles.append(line)
        legend_labels.append('Plow_max')

    # Temperature limits on RIGHT axis
    t_min = safe_float(app.cv_t_min.get())
    t_max = safe_float(app.cv_t_max.get())
    if t_min is not None:
        line = ax_temp.axhline(t_min, linestyle='--', color=limit_colors['T'], linewidth=1, alpha=0.8)
        legend_handles.append(line)
        legend_labels.append('T_min')
    if t_max is not None:
        line = ax_temp.axhline(t_max, linestyle='--', color=limit_colors['T'], linewidth=1, alpha=0.8)
        legend_handles.append(line)
        legend_labels.append('T_max')

    # Axis labels
    if time_unit == "hours":
        ax_pressure.set_xlabel("Time [h]", fontsize=10, fontweight='bold')
    else:
        ax_pressure.set_xlabel("Time [s]", fontsize=10, fontweight='bold')

    ax_pressure.set_ylabel("Pressure [MPa]", fontsize=10, fontweight='bold', color=colors['Ptank'])
    ax_temp.set_ylabel("Temperature [°C]", fontsize=10, fontweight='bold', color=colors['Tskin'])

    # Color the tick labels to match
    ax_pressure.tick_params(axis='y', labelcolor=colors['Ptank'])
    ax_temp.tick_params(axis='y', labelcolor=colors['Tskin'])

    # Grid (only on primary axis)
    ax_pressure.grid(True, alpha=0.3, linestyle='-')
    ax_pressure.set_facecolor('white')

    # Title
    test_name = app.cv_test_name.get().strip() or "Test"
    if time_unit == "hours":
        title = f"{test_name} - {cycle_label}"
    else:
        title = f"{test_name} Cycle #{cycle_label}"
    ax_pressure.set_title(title, fontsize=12, fontweight='bold')

    # Legend at bottom (combined from both axes)
    if legend_handles:
        ax_pressure.legend(
            legend_handles,
            legend_labels,
            loc='upper center',
            bbox_to_anchor=(0.5, -0.12),
            ncol=min(len(legend_labels), 6),
            fontsize=8,
            frameon=True
        )

    app.cv_fig.tight_layout()
    app.cv_fig.subplots_adjust(bottom=0.18)  # Make room for legend
    app.cv_canvas.draw()

    app.cv_status.set(f"Plotted cycle {cycle_label}")


def _cv_save_png(app):
    """Save current plot as PNG"""
    if not app.cv_fig.get_axes():
        messagebox.showwarning("Warning", "No plot to save. Create a plot first.")
        return

    try:
        out_path = filedialog.asksaveasfilename(
            title="Save Plot as PNG",
            defaultextension=".png",
            initialfile="cycle_plot.png",
            filetypes=[("PNG Image", "*.png"), ("All", "*.*")]
        )
        if not out_path:
            return

        app.cv_fig.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
        messagebox.showinfo("Success", f"Saved: {out_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to save: {e}")
