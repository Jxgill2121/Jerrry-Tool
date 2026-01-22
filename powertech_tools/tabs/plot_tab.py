# Plot tab - Data visualization with scatter and overview modes

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from powertech_tools.utils.file_parser import load_maxmin_for_plot
from powertech_tools.utils.helpers import safe_float, safe_int, ScrollableFrame
from powertech_tools.utils.plot_presets import (
    save_preset, delete_preset, get_preset_names, get_preset
)


def build_tab(parent, app):
    """
    Build the plot tab UI.

    Args:
        parent: Parent frame for this tab
        app: Main application instance (for storing state)
    """
    # Import theme for styling
    from powertech_tools.config.theme import PowertechTheme

    # Create scrollable container for entire tab
    scrollable = ScrollableFrame(parent)
    scrollable.pack(fill="both", expand=True)
    inner_frame = ttk.Frame(scrollable.content)
    inner_frame.pack(fill="both", expand=True, padx=15, pady=15)

    title_label = ttk.Label(inner_frame, text="Data Visualization", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        inner_frame,
        text="Plot max/min values across cycles with customizable graphs",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection
    card1 = ttk.LabelFrame(inner_frame, text="Input File", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    app.plot_infile = tk.StringVar(value="")
    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x")

    ttk.Button(
        btn_frame,
        text="📁 Choose Max/Min File",
        command=lambda: _plot_choose_file(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Label(btn_frame, textvariable=app.plot_infile, style='Status.TLabel').pack(side="left", padx=15)

    # Plot configuration
    config_card = ttk.LabelFrame(inner_frame, text="Plot Configuration", padding=20)
    config_card.pack(fill="x", pady=(0, 15))

    app.plot_df = None
    app.plot_internal_cols = []
    app.plot_internal_to_display = {}
    app.plot_internal_kind = {}

    app.plot_cycle_col = tk.StringVar(value="")
    app.plot_cycle_from = tk.StringVar(value="")
    app.plot_cycle_to = tk.StringVar(value="")

    # Visualization mode
    app.plot_mode = tk.StringVar(value="scatter")

    # Cycle settings
    cycle_row = ttk.Frame(config_card)
    cycle_row.pack(fill="x", pady=(0, 10))

    ttk.Label(cycle_row, text="Cycle Column:", width=15).pack(side="left")
    app.cb_plot_cycle = ttk.Combobox(cycle_row, state="disabled", width=30, textvariable=app.plot_cycle_col, values=[])
    app.cb_plot_cycle.pack(side="left", padx=10)

    ttk.Label(cycle_row, text="Range:", width=8).pack(side="left", padx=(20, 5))
    ttk.Entry(cycle_row, textvariable=app.plot_cycle_from, width=10).pack(side="left", padx=5)
    ttk.Label(cycle_row, text="to").pack(side="left", padx=5)
    ttk.Entry(cycle_row, textvariable=app.plot_cycle_to, width=10).pack(side="left", padx=5)
    ttk.Label(cycle_row, text="(optional)", style='Subtitle.TLabel').pack(side="left", padx=5)

    # Visualization mode selector
    mode_row = ttk.Frame(config_card)
    mode_row.pack(fill="x", pady=(10, 10))

    ttk.Label(mode_row, text="Visualization Mode:", width=15, font=(PowertechTheme.FONT_FAMILY, 10, 'bold')).pack(side="left")
    ttk.Radiobutton(mode_row, text="📊 Scatter Plot (Standard)", variable=app.plot_mode, value="scatter").pack(side="left", padx=10)
    ttk.Radiobutton(mode_row, text="📈 Overview Mode (Rolling Stats + Heatmap)", variable=app.plot_mode, value="overview").pack(side="left", padx=10)

    app.plot_mode_suggestion = tk.StringVar(value="")
    ttk.Label(mode_row, textvariable=app.plot_mode_suggestion, style='Subtitle.TLabel', foreground=PowertechTheme.ACCENT).pack(side="left", padx=15)

    # Preset management section
    preset_frame = ttk.LabelFrame(config_card, text="Parameter Presets (Save/Load Bounds)", padding=15)
    preset_frame.pack(fill="x", pady=(15, 0))

    preset_desc = ttk.Label(
        preset_frame,
        text="Save commonly used min/max bounds for different test types (e.g., R134a, R410A)",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666"
    )
    preset_desc.pack(anchor="w", pady=(0, 10))

    preset_row1 = ttk.Frame(preset_frame)
    preset_row1.pack(fill="x", pady=5)

    ttk.Label(preset_row1, text="Select Preset:", width=15).pack(side="left")
    app.preset_var = tk.StringVar(value="")
    app.preset_combo = ttk.Combobox(preset_row1, state="readonly", width=30, textvariable=app.preset_var)
    app.preset_combo.pack(side="left", padx=10)

    ttk.Button(
        preset_row1,
        text="⬇ Load Preset",
        command=lambda: _load_preset(app)
    ).pack(side="left", padx=5)

    ttk.Button(
        preset_row1,
        text="🗑 Delete",
        command=lambda: _delete_preset(app)
    ).pack(side="left", padx=5)

    preset_row2 = ttk.Frame(preset_frame)
    preset_row2.pack(fill="x", pady=5)

    ttk.Label(preset_row2, text="Save As:", width=15).pack(side="left")
    app.preset_name_var = tk.StringVar(value="")
    ttk.Entry(preset_row2, textvariable=app.preset_name_var, width=30).pack(side="left", padx=10)

    ttk.Button(
        preset_row2,
        text="💾 Save Current Settings",
        command=lambda: _save_preset(app)
    ).pack(side="left", padx=5)

    app.preset_status = tk.StringVar(value="")
    ttk.Label(preset_row2, textvariable=app.preset_status, foreground=PowertechTheme.ACCENT).pack(side="left", padx=10)

    # Refresh preset list
    _refresh_preset_list(app)

    # Graph setup
    graph_row = ttk.Frame(config_card)
    graph_row.pack(fill="x", pady=(0, 10))

    ttk.Label(graph_row, text="Number of Graphs:", width=15).pack(side="left")
    app.num_graphs_var = tk.IntVar(value=2)
    ttk.Spinbox(
        graph_row, from_=1, to=10, width=8, textvariable=app.num_graphs_var,
        command=lambda: _plot_rebuild_graph_rows(app)
    ).pack(side="left", padx=10)

    ttk.Button(
        graph_row,
        text="🔄 Rebuild Graph Rows",
        command=lambda: _plot_rebuild_graph_rows(app)
    ).pack(side="left", padx=10)

    # Graph selection area
    app.graph_rows_box = ttk.LabelFrame(config_card, text="Graph Variables", padding=15)
    app.graph_rows_box.pack(fill="x", pady=(10, 0))

    hdr = ttk.Frame(app.graph_rows_box)
    hdr.pack(fill="x", pady=(0, 8))
    ttk.Label(hdr, text="#", width=3, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=0, sticky="w")
    ttk.Label(hdr, text="Y-Axis Variable 1", width=30, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(hdr, text="Y-Axis Variable 2", width=30, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=2, sticky="w", padx=5)
    ttk.Label(hdr, text="Y Min", width=8, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=3, sticky="w", padx=5)
    ttk.Label(hdr, text="Y Max", width=8, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=4, sticky="w", padx=5)
    ttk.Label(hdr, text="Min Lower", width=8, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=5, sticky="w", padx=5)
    ttk.Label(hdr, text="Min Upper", width=8, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=6, sticky="w", padx=5)
    ttk.Label(hdr, text="Max Lower", width=8, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=7, sticky="w", padx=5)
    ttk.Label(hdr, text="Max Upper", width=8, font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=8, sticky="w", padx=5)

    app.graph_selectors = []

    # Action
    action_card = ttk.LabelFrame(inner_frame, text="Generate Plots", padding=20)
    action_card.pack(fill="x", pady=(0, 15))

    app.plot_btn = ttk.Button(
        action_card,
        text="▶ CREATE PLOTS",
        command=lambda: _plot_make(app),
        state="disabled",
        style='Action.TButton'
    )
    app.plot_btn.pack(side="left")

    # Plot area
    plot_card = ttk.LabelFrame(inner_frame, text="Visualization", padding=15)
    plot_card.pack(fill="both", expand=True, pady=(0, 0))

    # Larger figure size for better readability
    app.fig = plt.Figure(figsize=(14, 10), dpi=100)
    app.fig.patch.set_facecolor(PowertechTheme.BG_CARD)
    app.canvas = FigureCanvasTkAgg(app.fig, master=plot_card)
    app.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    toolbar = NavigationToolbar2Tk(app.canvas, plot_card)
    toolbar.update()

    _plot_rebuild_graph_rows(app)


def _plot_choose_file(app):
    """Handle file selection for plotting"""
    path = filedialog.askopenfilename(
        title="Select max/min file",
        filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
    )
    if not path:
        return
    app.plot_infile.set(path)
    _plot_load_file(app)


def _plot_load_file(app):
    """Load the selected file for plotting"""
    try:
        path = app.plot_infile.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", f"File not found: {path}")
            return

        df, internal_cols, internal_to_display, internal_kind = load_maxmin_for_plot(path)

        app.plot_df = df
        app.plot_internal_cols = internal_cols
        app.plot_internal_to_display = internal_to_display
        app.plot_internal_kind = internal_kind

        cycle_internal = None
        for c in internal_cols:
            if internal_to_display.get(c, "") == "Cycle":
                cycle_internal = c
                break
        if cycle_internal is None:
            cycle_internal = internal_cols[1] if len(internal_cols) > 1 else internal_cols[0]

        app.cb_plot_cycle["values"] = [internal_to_display[c] for c in internal_cols]
        app.cb_plot_cycle["state"] = "readonly"
        app.plot_cycle_col.set(internal_to_display[cycle_internal])

        _plot_refresh_graph_row_values(app)
        app.plot_btn["state"] = "normal"
        messagebox.showinfo("Success", "File loaded successfully")
    except Exception as e:
        app.plot_df = None
        app.plot_btn["state"] = "disabled"
        messagebox.showerror("Error", str(e))


def _plot_rebuild_graph_rows(app):
    """Rebuild the graph configuration rows"""
    from powertech_tools.config.theme import PowertechTheme

    kids = app.graph_rows_box.winfo_children()
    for w in kids[1:]:
        w.destroy()

    app.graph_selectors.clear()

    n = int(app.num_graphs_var.get() or 1)
    for i in range(n):
        rowf = ttk.Frame(app.graph_rows_box)
        rowf.pack(fill="x", pady=3)

        ttk.Label(rowf, text=str(i + 1), width=3).grid(row=0, column=0, sticky="w")

        y1_var = tk.StringVar(value="")
        y2_var = tk.StringVar(value="")
        y_min_var = tk.StringVar(value="")
        y_max_var = tk.StringVar(value="")
        min_low_var = tk.StringVar(value="")
        min_high_var = tk.StringVar(value="")
        max_low_var = tk.StringVar(value="")
        max_high_var = tk.StringVar(value="")

        y1_cb = ttk.Combobox(rowf, state="disabled", width=30, textvariable=y1_var, values=[])
        y2_cb = ttk.Combobox(rowf, state="disabled", width=30, textvariable=y2_var, values=[""])
        y1_cb.grid(row=0, column=1, padx=5, sticky="w")
        y2_cb.grid(row=0, column=2, padx=5, sticky="w")

        ttk.Entry(rowf, width=8, textvariable=y_min_var).grid(row=0, column=3, padx=5, sticky="w")
        ttk.Entry(rowf, width=8, textvariable=y_max_var).grid(row=0, column=4, padx=5, sticky="w")
        ttk.Entry(rowf, width=8, textvariable=min_low_var).grid(row=0, column=5, padx=5, sticky="w")
        ttk.Entry(rowf, width=8, textvariable=min_high_var).grid(row=0, column=6, padx=5, sticky="w")
        ttk.Entry(rowf, width=8, textvariable=max_low_var).grid(row=0, column=7, padx=5, sticky="w")
        ttk.Entry(rowf, width=8, textvariable=max_high_var).grid(row=0, column=8, padx=5, sticky="w")

        app.graph_selectors.append({
            "y1_var": y1_var, "y2_var": y2_var,
            "y_min_var": y_min_var, "y_max_var": y_max_var,
            "min_low_var": min_low_var, "min_high_var": min_high_var,
            "max_low_var": max_low_var, "max_high_var": max_high_var
        })

    _plot_refresh_graph_row_values(app)


def _plot_refresh_graph_row_values(app):
    """Refresh the dropdown values in graph configuration rows"""
    if app.plot_df is None:
        return

    display_list = [app.plot_internal_to_display[c] for c in app.plot_internal_cols]
    for i, _sel in enumerate(app.graph_selectors):
        row = app.graph_rows_box.winfo_children()[i + 1]
        y1_cb = row.grid_slaves(row=0, column=1)[0]
        y2_cb = row.grid_slaves(row=0, column=2)[0]
        y1_cb.configure(values=display_list, state="readonly")
        y2_cb.configure(values=[""] + display_list, state="readonly")


def _display_to_internal(app, display_name: str) -> Optional[str]:
    """Convert display name to internal column name"""
    for k, v in app.plot_internal_to_display.items():
        if v == display_name:
            return k
    return None


def _refresh_preset_list(app):
    """Refresh the preset dropdown list"""
    preset_names = get_preset_names()
    app.preset_combo["values"] = preset_names
    if preset_names:
        app.preset_var.set(preset_names[0])
    else:
        app.preset_var.set("")


def _save_preset(app):
    """Save current graph settings as a preset"""
    try:
        preset_name = app.preset_name_var.get().strip()
        if not preset_name:
            messagebox.showerror("Error", "Please enter a preset name")
            return

        # Collect current settings from all graph rows
        graph_configs = []
        for sel in app.graph_selectors:
            config = {
                "y1_var": sel["y1_var"].get(),
                "y2_var": sel["y2_var"].get(),
                "y_min_var": sel["y_min_var"].get(),
                "y_max_var": sel["y_max_var"].get(),
                "min_low_var": sel["min_low_var"].get(),
                "min_high_var": sel["min_high_var"].get(),
                "max_low_var": sel["max_low_var"].get(),
                "max_high_var": sel["max_high_var"].get()
            }
            graph_configs.append(config)

        save_preset(preset_name, graph_configs)
        _refresh_preset_list(app)
        app.preset_var.set(preset_name)
        app.preset_status.set(f"✓ Saved '{preset_name}'")
        app.preset_name_var.set("")

        # Clear status after 3 seconds
        app.after(3000, lambda: app.preset_status.set(""))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to save preset: {e}")


def _load_preset(app):
    """Load a preset and apply it to the graph settings"""
    try:
        preset_name = app.preset_var.get().strip()
        if not preset_name:
            messagebox.showerror("Error", "Please select a preset")
            return

        preset_data = get_preset(preset_name)
        if not preset_data:
            messagebox.showerror("Error", f"Preset '{preset_name}' not found")
            return

        # Ensure we have enough graph rows
        if len(preset_data) > len(app.graph_selectors):
            app.num_graphs_var.set(len(preset_data))
            _plot_rebuild_graph_rows(app)

        # Apply preset to each graph row
        for i, config in enumerate(preset_data):
            if i < len(app.graph_selectors):
                sel = app.graph_selectors[i]
                sel["y1_var"].set(config.get("y1", ""))
                sel["y2_var"].set(config.get("y2", ""))
                sel["y_min_var"].set(config.get("y_min", ""))
                sel["y_max_var"].set(config.get("y_max", ""))
                sel["min_low_var"].set(config.get("min_low", ""))
                sel["min_high_var"].set(config.get("min_high", ""))
                sel["max_low_var"].set(config.get("max_low", ""))
                sel["max_high_var"].set(config.get("max_high", ""))

        app.preset_status.set(f"✓ Loaded '{preset_name}'")
        app.after(3000, lambda: app.preset_status.set(""))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load preset: {e}")


def _delete_preset(app):
    """Delete the selected preset"""
    try:
        preset_name = app.preset_var.get().strip()
        if not preset_name:
            messagebox.showerror("Error", "Please select a preset to delete")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Delete preset '{preset_name}'?"):
            return

        delete_preset(preset_name)
        _refresh_preset_list(app)
        app.preset_status.set(f"✓ Deleted '{preset_name}'")
        app.after(3000, lambda: app.preset_status.set(""))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete preset: {e}")


def _plot_make(app):
    """Generate the plots"""
    try:
        if app.plot_df is None:
            messagebox.showerror("Error", "Please load a file first")
            return

        df = app.plot_df.copy()

        cycle_display = app.plot_cycle_col.get().strip()
        cycle_internal = _display_to_internal(app, cycle_display)
        if not cycle_internal or cycle_internal not in df.columns:
            messagebox.showerror("Error", "Invalid cycle column")
            return

        df[cycle_internal] = pd.to_numeric(df[cycle_internal], errors="coerce")
        df = df[df[cycle_internal].notna()].reset_index(drop=True)

        c_from = safe_int(app.plot_cycle_from.get())
        c_to = safe_int(app.plot_cycle_to.get())
        if c_from == "INVALID" or c_to == "INVALID":
            messagebox.showerror("Error", "Cycle range must be integers")
            return
        if c_from is not None:
            df = df[df[cycle_internal] >= c_from]
        if c_to is not None:
            df = df[df[cycle_internal] <= c_to]
        df = df.reset_index(drop=True)

        if df.empty:
            messagebox.showerror("Error", "No data in selected range")
            return

        # Check cycle count and suggest mode
        num_cycles = len(df)
        if num_cycles > 100 and app.plot_mode.get() == "scatter":
            app.plot_mode_suggestion.set(f"💡 {num_cycles} cycles detected - Overview Mode recommended!")
        else:
            app.plot_mode_suggestion.set("")

        plot_jobs = []
        for i, sel in enumerate(app.graph_selectors):
            y1_disp = sel["y1_var"].get().strip()
            y2_disp = sel["y2_var"].get().strip()
            y_min = safe_float(sel["y_min_var"].get())
            y_max = safe_float(sel["y_max_var"].get())
            min_low = safe_float(sel["min_low_var"].get())
            min_high = safe_float(sel["min_high_var"].get())
            max_low = safe_float(sel["max_low_var"].get())
            max_high = safe_float(sel["max_high_var"].get())

            if any(x == "INVALID" for x in [y_min, y_max, min_low, min_high, max_low, max_high]):
                messagebox.showerror("Error", f"Graph {i+1}: limits must be numeric")
                return

            if y1_disp or y2_disp:
                plot_jobs.append((i + 1, y1_disp, y2_disp, y_min, y_max, min_low, min_high, max_low, max_high))

        if not plot_jobs:
            messagebox.showwarning("Warning", "Please select at least one variable")
            return

        # Route to appropriate plotting function
        mode = app.plot_mode.get()
        if mode == "overview":
            _plot_make_overview(app, df, cycle_internal, plot_jobs)
        else:
            _plot_make_scatter(app, df, cycle_internal, plot_jobs)

    except Exception as e:
        messagebox.showerror("Error", str(e))


def _plot_make_scatter(app, df, cycle_internal, plot_jobs):
    """Generate scatter plots"""
    from powertech_tools.config.theme import PowertechTheme

    app.fig.clear()
    n = len(plot_jobs)

    for idx, (graph_num, y1_disp, y2_disp, y_min, y_max, min_low, min_high, max_low, max_high) in enumerate(plot_jobs, start=1):
        ax = app.fig.add_subplot(n, 1, idx)

        x = df[cycle_internal]
        labels_for_title = []

        def plot_series(y_disp: str):
            if not y_disp:
                return
            y_int = _display_to_internal(app, y_disp)
            if not y_int or y_int not in df.columns:
                return

            y = pd.to_numeric(df[y_int], errors="coerce")
            kind = app.plot_internal_kind.get(y_int, "other")

            if kind == "min":
                ax.plot(x, y, marker="o", linestyle="None", markersize=4, color=PowertechTheme.ACCENT, label=y_disp, alpha=0.6)
            elif kind == "max":
                ax.plot(x, y, marker="o", linestyle="None", markersize=4, color=PowertechTheme.ERROR, label=y_disp, alpha=0.6)
            else:
                ax.plot(x, y, marker="o", linestyle="None", markersize=4, color=PowertechTheme.PRIMARY, label=y_disp, alpha=0.6)

            labels_for_title.append(y_disp)

        plot_series(y1_disp)
        plot_series(y2_disp)

        ax.set_xlabel("Cycle", fontsize=10, fontweight='bold')
        ax.set_ylabel("Value", fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_title(" | ".join(labels_for_title) if labels_for_title else f"Graph {graph_num}",
                     fontsize=11, fontweight="bold", color=PowertechTheme.PRIMARY)
        ax.set_facecolor('#fafafa')

        # Set Y-axis limits if specified
        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)
        elif y_min is not None:
            ax.set_ylim(bottom=y_min)
        elif y_max is not None:
            ax.set_ylim(top=y_max)

        # Draw limit lines - separate for min and max
        if min_low is not None:
            ax.axhline(min_low, linestyle=":", linewidth=1.5, color=PowertechTheme.ACCENT, alpha=0.7, label=f"Min Lower Limit")
        if min_high is not None:
            ax.axhline(min_high, linestyle=":", linewidth=1.5, color=PowertechTheme.ACCENT, alpha=0.7, label=f"Min Upper Limit")
        if max_low is not None:
            ax.axhline(max_low, linestyle="--", linewidth=1.5, color=PowertechTheme.ERROR, alpha=0.7, label=f"Max Lower Limit")
        if max_high is not None:
            ax.axhline(max_high, linestyle="--", linewidth=1.5, color=PowertechTheme.ERROR, alpha=0.7, label=f"Max Upper Limit")

        ax.legend(fontsize=9, loc='best')

    app.fig.tight_layout()
    app.canvas.draw()


def _plot_make_overview(app, df, cycle_internal, plot_jobs):
    """Generate overview plots with rolling statistics and heatmap"""
    from powertech_tools.config.theme import PowertechTheme
    import numpy as np

    app.fig.clear()

    num_cycles = len(df)

    # Determine layout
    n_vars = len(plot_jobs)

    if n_vars == 1:
        n_rows = 2
    else:
        n_rows = n_vars + 1

    # Calculate rolling window (adaptive based on data size)
    window = max(10, min(100, num_cycles // 20))

    x = df[cycle_internal]

    # Plot rolling statistics for each variable
    for idx, (graph_num, y1_disp, y2_disp, y_min, y_max, min_low, min_high, max_low, max_high) in enumerate(plot_jobs, start=1):
        if n_vars == 1:
            ax = app.fig.add_subplot(n_rows, 1, 1)
        else:
            ax = app.fig.add_subplot(n_rows, 1, idx)

        labels_for_title = []

        def plot_rolling_series(y_disp: str, color_base: str):
            if not y_disp:
                return
            y_int = _display_to_internal(app, y_disp)
            if not y_int or y_int not in df.columns:
                return

            y = pd.to_numeric(df[y_int], errors="coerce")
            kind = app.plot_internal_kind.get(y_int, "other")

            # Determine color
            if kind == "min":
                color = PowertechTheme.ACCENT
            elif kind == "max":
                color = PowertechTheme.ERROR
            else:
                color = PowertechTheme.PRIMARY

            # Calculate rolling statistics
            y_series = pd.Series(y.values)
            rolling_mean = y_series.rolling(window=window, center=True, min_periods=1).mean()
            rolling_std = y_series.rolling(window=window, center=True, min_periods=1).std()

            # Plot mean line
            ax.plot(x, rolling_mean, linewidth=2.5, color=color, label=f"{y_disp} (avg)", alpha=0.9)

            # Plot confidence envelope (mean ± std)
            ax.fill_between(x,
                           rolling_mean - rolling_std,
                           rolling_mean + rolling_std,
                           color=color, alpha=0.15, label=f"{y_disp} (±1σ)")

            # Plot actual data points (lighter, smaller)
            ax.plot(x, y, marker=".", linestyle="None", markersize=2, color=color, alpha=0.2)

            labels_for_title.append(y_disp)

        plot_rolling_series(y1_disp, "blue")
        plot_rolling_series(y2_disp, "red")

        ax.set_xlabel("Cycle", fontsize=9, fontweight='bold')
        ax.set_ylabel("Value", fontsize=9, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        title_text = " | ".join(labels_for_title) if labels_for_title else f"Graph {graph_num}"
        ax.set_title(f"Rolling Statistics (Window={window}) - {title_text}",
                     fontsize=10, fontweight="bold", color=PowertechTheme.PRIMARY)
        ax.set_facecolor('#fafafa')

        # Set Y-axis limits if specified
        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)
        elif y_min is not None:
            ax.set_ylim(bottom=y_min)
        elif y_max is not None:
            ax.set_ylim(top=y_max)

        # Add limit lines if specified
        if min_low is not None:
            ax.axhline(min_low, linestyle=":", linewidth=1.5, color=PowertechTheme.ACCENT, alpha=0.8, label=f"Min Lower")
        if min_high is not None:
            ax.axhline(min_high, linestyle=":", linewidth=1.5, color=PowertechTheme.ACCENT, alpha=0.8, label=f"Min Upper")
        if max_low is not None:
            ax.axhline(max_low, linestyle="--", linewidth=1.5, color=PowertechTheme.ERROR, alpha=0.8, label=f"Max Lower")
        if max_high is not None:
            ax.axhline(max_high, linestyle="--", linewidth=1.5, color=PowertechTheme.ERROR, alpha=0.8, label=f"Max Upper")

        ax.legend(fontsize=8, loc='best', framealpha=0.9)

    # Create heatmap showing binned cycle performance
    ax_heat = app.fig.add_subplot(n_rows, 1, n_rows)

    # Determine bin size
    bin_size = max(1, num_cycles // 30)
    n_bins = (num_cycles + bin_size - 1) // bin_size

    # Collect all variables to plot in heatmap
    heatmap_vars = []
    heatmap_labels = []
    for graph_num, y1_disp, y2_disp, y_min, y_max, min_low, min_high, max_low, max_high in plot_jobs:
        for y_disp in [y1_disp, y2_disp]:
            if y_disp:
                y_int = _display_to_internal(app, y_disp)
                if y_int and y_int in df.columns:
                    heatmap_vars.append((y_int, y_disp, y_min, y_max, min_low, min_high, max_low, max_high))
                    heatmap_labels.append(y_disp)

    if heatmap_vars:
        heatmap_data = []
        bin_labels = []

        for bin_idx in range(n_bins):
            start_idx = bin_idx * bin_size
            end_idx = min((bin_idx + 1) * bin_size, num_cycles)
            bin_df = df.iloc[start_idx:end_idx]

            bin_start_cycle = int(bin_df[cycle_internal].iloc[0])
            bin_end_cycle = int(bin_df[cycle_internal].iloc[-1])
            bin_labels.append(f"{bin_start_cycle}-{bin_end_cycle}")

            row_data = []
            for y_int, y_disp, y_min, y_max, min_low, min_high, max_low, max_high in heatmap_vars:
                y_vals = pd.to_numeric(bin_df[y_int], errors="coerce").dropna()
                if len(y_vals) > 0:
                    avg_val = y_vals.mean()
                    row_data.append(avg_val)
                else:
                    row_data.append(0)

            heatmap_data.append(row_data)

        heatmap_array = pd.DataFrame(heatmap_data, columns=heatmap_labels, index=bin_labels).T

        # Create heatmap
        im = ax_heat.imshow(heatmap_array.values, aspect='auto', cmap='RdYlGn_r', interpolation='nearest')

        # Set ticks
        ax_heat.set_yticks(range(len(heatmap_labels)))
        ax_heat.set_yticklabels(heatmap_labels, fontsize=8)

        # Only show some x-axis labels to avoid crowding
        x_tick_indices = np.linspace(0, len(bin_labels)-1, min(10, len(bin_labels)), dtype=int)
        ax_heat.set_xticks(x_tick_indices)
        ax_heat.set_xticklabels([bin_labels[i] for i in x_tick_indices], rotation=45, ha='right', fontsize=7)

        ax_heat.set_xlabel("Cycle Range", fontsize=9, fontweight='bold')
        ax_heat.set_title(f"Binned Average Values (Bin Size={bin_size} cycles)",
                        fontsize=10, fontweight="bold", color=PowertechTheme.PRIMARY)

        # Add colorbar
        cbar = app.fig.colorbar(im, ax=ax_heat, orientation='vertical', pad=0.02, fraction=0.046)
        cbar.ax.tick_params(labelsize=8)
        cbar.set_label('Average Value', fontsize=8)

    app.fig.tight_layout()
    app.canvas.draw()
