# Plot tab - Data visualization with scatter and overview modes

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, PngImagePlugin

from powertech_tools.utils.file_parser import load_maxmin_for_plot
from powertech_tools.utils.helpers import safe_float, safe_int, ScrollableFrame


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

    # Main title for all plots
    title_row = ttk.Frame(config_card)
    title_row.pack(fill="x", pady=(0, 10))

    ttk.Label(title_row, text="Main Title:", width=15).pack(side="left")
    app.plot_main_title = tk.StringVar(value="")
    ttk.Entry(title_row, textvariable=app.plot_main_title, width=40).pack(side="left", padx=10)
    ttk.Label(title_row, text="(e.g. PL-006117)", style='Subtitle.TLabel').pack(side="left", padx=5)

    # Cycle settings
    cycle_row = ttk.Frame(config_card)
    cycle_row.pack(fill="x", pady=(0, 10))

    ttk.Label(cycle_row, text="Cycle Column:", width=15).pack(side="left")
    app.cb_plot_cycle = ttk.Combobox(cycle_row, state="disabled", width=30, textvariable=app.plot_cycle_col, values=[])
    app.cb_plot_cycle.pack(side="left", padx=10)

    # X-axis settings row
    xaxis_row = ttk.Frame(config_card)
    xaxis_row.pack(fill="x", pady=(0, 10))

    ttk.Label(xaxis_row, text="X-Axis Range:", width=15).pack(side="left")
    app.plot_x_min = tk.StringVar(value="0")
    app.plot_x_max = tk.StringVar(value="")
    ttk.Label(xaxis_row, text="Min:").pack(side="left", padx=(0, 5))
    ttk.Entry(xaxis_row, textvariable=app.plot_x_min, width=10).pack(side="left", padx=5)
    ttk.Label(xaxis_row, text="Max:").pack(side="left", padx=(10, 5))
    ttk.Entry(xaxis_row, textvariable=app.plot_x_max, width=10).pack(side="left", padx=5)
    ttk.Label(xaxis_row, text="(leave Max blank for auto)", style='Subtitle.TLabel').pack(side="left", padx=5)

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

    # Container frame for grid layout - headers and rows share the same grid
    app.graph_grid_container = ttk.Frame(app.graph_rows_box)
    app.graph_grid_container.pack(fill="x")

    # Configure column widths for alignment
    col_widths = [70, 130, 100, 180, 180, 80, 80, 60, 100, 100, 100, 100]
    for col, w in enumerate(col_widths):
        app.graph_grid_container.grid_columnconfigure(col, minsize=w)

    # Header row
    ttk.Label(app.graph_grid_container, text="Graph", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=0, sticky="w", padx=(0,5), pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Title", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=1, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Y-Axis Label", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=2, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Y-Axis Variable 1", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=3, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Y-Axis Variable 2 (opt)", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=4, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Y-Axis Min", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=5, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Y-Axis Max", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=6, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Y Ticks", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=7, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Min Lower\nBound", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=8, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Min Upper\nBound", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=9, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Max Lower\nBound", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=10, sticky="w", padx=5, pady=(0,8))
    ttk.Label(app.graph_grid_container, text="Max Upper\nBound", font=(PowertechTheme.FONT_FAMILY, 9, 'bold')).grid(row=0, column=11, sticky="w", padx=5, pady=(0,8))

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

    ttk.Button(
        action_card,
        text="💾 Save PNG",
        command=lambda: _plot_export_image(app)
    ).pack(side="left", padx=10)

    ttk.Button(
        action_card,
        text="📂 Load from Graph",
        command=lambda: _plot_load_from_graph(app)
    ).pack(side="left", padx=10)

    app.plot_status = tk.StringVar(value="")
    ttk.Label(action_card, textvariable=app.plot_status, foreground=PowertechTheme.ACCENT).pack(side="left", padx=15)

    # Plot area
    plot_card = ttk.LabelFrame(inner_frame, text="Visualization", padding=15)
    plot_card.pack(fill="both", expand=True, pady=(0, 0))

    # Larger figure size for better readability
    app.fig = plt.Figure(figsize=(14, 10), dpi=100)
    app.fig.patch.set_facecolor(PowertechTheme.BG_CARD)
    app.canvas = FigureCanvasTkAgg(app.fig, master=plot_card)
    app.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

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

    # Remove old data rows (keep header row 0)
    container = app.graph_grid_container
    for widget in container.winfo_children():
        info = widget.grid_info()
        if info and int(info.get('row', 0)) > 0:
            widget.destroy()

    app.graph_selectors.clear()

    n = int(app.num_graphs_var.get() or 1)
    for i in range(n):
        row_num = i + 1  # Row 0 is header

        ttk.Label(container, text=f"Graph {i + 1}").grid(row=row_num, column=0, sticky="w", padx=(0,5), pady=3)

        title_var = tk.StringVar(value="")
        y_label_var = tk.StringVar(value="Value")
        y1_var = tk.StringVar(value="")
        y2_var = tk.StringVar(value="")
        y_min_var = tk.StringVar(value="")
        y_max_var = tk.StringVar(value="")
        y_ticks_var = tk.StringVar(value="")
        min_low_var = tk.StringVar(value="")
        min_high_var = tk.StringVar(value="")
        max_low_var = tk.StringVar(value="")
        max_high_var = tk.StringVar(value="")

        ttk.Entry(container, width=15, textvariable=title_var).grid(row=row_num, column=1, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=12, textvariable=y_label_var).grid(row=row_num, column=2, padx=5, pady=3, sticky="w")

        y1_cb = ttk.Combobox(container, state="disabled", width=22, textvariable=y1_var, values=[])
        y2_cb = ttk.Combobox(container, state="disabled", width=22, textvariable=y2_var, values=[""])
        y1_cb.grid(row=row_num, column=3, padx=5, pady=3, sticky="w")
        y2_cb.grid(row=row_num, column=4, padx=5, pady=3, sticky="w")

        ttk.Entry(container, width=8, textvariable=y_min_var).grid(row=row_num, column=5, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=8, textvariable=y_max_var).grid(row=row_num, column=6, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=6, textvariable=y_ticks_var).grid(row=row_num, column=7, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=10, textvariable=min_low_var).grid(row=row_num, column=8, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=10, textvariable=min_high_var).grid(row=row_num, column=9, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=10, textvariable=max_low_var).grid(row=row_num, column=10, padx=5, pady=3, sticky="w")
        ttk.Entry(container, width=10, textvariable=max_high_var).grid(row=row_num, column=11, padx=5, pady=3, sticky="w")

        app.graph_selectors.append({
            "title_var": title_var,
            "y_label_var": y_label_var,
            "y1_var": y1_var, "y2_var": y2_var,
            "y1_cb": y1_cb, "y2_cb": y2_cb,
            "y_min_var": y_min_var, "y_max_var": y_max_var,
            "y_ticks_var": y_ticks_var,
            "min_low_var": min_low_var, "min_high_var": min_high_var,
            "max_low_var": max_low_var, "max_high_var": max_high_var
        })

    _plot_refresh_graph_row_values(app)


def _plot_refresh_graph_row_values(app):
    """Refresh the dropdown values in graph configuration rows"""
    if app.plot_df is None:
        return

    display_list = [app.plot_internal_to_display[c] for c in app.plot_internal_cols]
    for sel in app.graph_selectors:
        y1_cb = sel["y1_cb"]
        y2_cb = sel["y2_cb"]
        y1_cb.configure(values=display_list, state="readonly")
        y2_cb.configure(values=[""] + display_list, state="readonly")


def _display_to_internal(app, display_name: str) -> Optional[str]:
    """Convert display name to internal column name"""
    for k, v in app.plot_internal_to_display.items():
        if v == display_name:
            return k
    return None


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

        if df.empty:
            messagebox.showerror("Error", "No data available")
            return

        plot_jobs = []
        for i, sel in enumerate(app.graph_selectors):
            y1_disp = sel["y1_var"].get().strip()
            y2_disp = sel["y2_var"].get().strip()
            y_min = safe_float(sel["y_min_var"].get())
            y_max = safe_float(sel["y_max_var"].get())
            y_ticks = safe_int(sel["y_ticks_var"].get())
            min_low = safe_float(sel["min_low_var"].get())
            min_high = safe_float(sel["min_high_var"].get())
            max_low = safe_float(sel["max_low_var"].get())
            max_high = safe_float(sel["max_high_var"].get())

            if any(x == "INVALID" for x in [y_min, y_max, min_low, min_high, max_low, max_high]):
                messagebox.showerror("Error", f"Graph {i+1}: limits must be numeric")
                return
            if y_ticks == "INVALID":
                messagebox.showerror("Error", f"Graph {i+1}: Y Ticks must be an integer")
                return

            custom_title = sel["title_var"].get().strip()
            y_label = sel["y_label_var"].get().strip() or "Value"

            if y1_disp or y2_disp:
                plot_jobs.append((i + 1, y1_disp, y2_disp, y_min, y_max, y_ticks, min_low, min_high, max_low, max_high, custom_title, y_label))

        if not plot_jobs:
            messagebox.showwarning("Warning", "Please select at least one variable")
            return

        # Generate scatter plots
        _plot_make_scatter(app, df, cycle_internal, plot_jobs)

    except Exception as e:
        messagebox.showerror("Error", str(e))


def _plot_make_scatter(app, df, cycle_internal, plot_jobs):
    """Generate scatter plots"""
    from powertech_tools.config.theme import PowertechTheme
    import numpy as np

    # Colors: max = red, min = blue
    COLOR_MAX = '#CC0000'  # Red for max
    COLOR_MIN = '#0066CC'  # Blue for min

    # Get X-axis limits
    x_min = safe_float(app.plot_x_min.get())
    x_max = safe_float(app.plot_x_max.get())

    app.fig.clear()
    n = len(plot_jobs)

    for idx, (graph_num, y1_disp, y2_disp, y_min, y_max, y_ticks, min_low, min_high, max_low, max_high, custom_title, y_label) in enumerate(plot_jobs, start=1):
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
                ax.plot(x, y, marker="o", linestyle="None", markersize=2, color=COLOR_MIN, label=y_disp, alpha=0.7)
            elif kind == "max":
                ax.plot(x, y, marker="o", linestyle="None", markersize=2, color=COLOR_MAX, label=y_disp, alpha=0.7)
            else:
                ax.plot(x, y, marker="o", linestyle="None", markersize=2, color=PowertechTheme.PRIMARY, label=y_disp, alpha=0.7)

            labels_for_title.append(y_disp)

        plot_series(y1_disp)
        plot_series(y2_disp)

        # Only show "Cycle" label on the last graph
        if idx == n:
            ax.set_xlabel("Cycle", fontsize=10, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        if custom_title:
            plot_title = custom_title
        elif labels_for_title:
            plot_title = " | ".join(labels_for_title)
        else:
            plot_title = f"Graph {graph_num}"
        ax.set_title(plot_title, fontsize=11, fontweight="bold", color=PowertechTheme.PRIMARY)
        ax.set_facecolor('#fafafa')

        # Set Y-axis limits if specified
        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)
        elif y_min is not None:
            ax.set_ylim(bottom=y_min)
        elif y_max is not None:
            ax.set_ylim(top=y_max)

        # Set X-axis limits if specified
        if x_min is not None and x_max is not None:
            ax.set_xlim(x_min, x_max)
        elif x_min is not None:
            ax.set_xlim(left=x_min)
        elif x_max is not None:
            ax.set_xlim(right=x_max)

        # Set Y-axis ticks if specified
        if y_ticks is not None and y_ticks > 1 and y_min is not None and y_max is not None:
            ax.set_yticks(np.linspace(y_min, y_max, y_ticks))

        # Draw limit lines - min = blue, max = red
        if min_low is not None:
            ax.axhline(min_low, linestyle=":", linewidth=1.5, color=COLOR_MIN, alpha=0.7, label=f"Min Lower Limit")
        if min_high is not None:
            ax.axhline(min_high, linestyle=":", linewidth=1.5, color=COLOR_MIN, alpha=0.7, label=f"Min Upper Limit")
        if max_low is not None:
            ax.axhline(max_low, linestyle="--", linewidth=1.5, color=COLOR_MAX, alpha=0.7, label=f"Max Lower Limit")
        if max_high is not None:
            ax.axhline(max_high, linestyle="--", linewidth=1.5, color=COLOR_MAX, alpha=0.7, label=f"Max Upper Limit")

        ax.legend(fontsize=14, loc='best')

    # Add main title if specified
    main_title = app.plot_main_title.get().strip()
    if main_title:
        app.fig.suptitle(main_title, fontsize=14, fontweight='bold', y=0.98)
        app.fig.tight_layout(rect=[0, 0, 1, 0.96])
    else:
        app.fig.tight_layout()
    app.canvas.draw()


def _plot_get_current_settings(app):
    """Get current graph settings as a dictionary"""
    settings = {
        'main_title': app.plot_main_title.get(),
        'num_graphs': app.num_graphs_var.get(),
        'x_min': app.plot_x_min.get(),
        'x_max': app.plot_x_max.get(),
        'graphs': []
    }

    for sel in app.graph_selectors:
        graph_config = {
            'title': sel["title_var"].get(),
            'y_label': sel["y_label_var"].get(),
            'y1_var': sel["y1_var"].get(),
            'y2_var': sel["y2_var"].get(),
            'y_min': sel["y_min_var"].get(),
            'y_max': sel["y_max_var"].get(),
            'y_ticks': sel["y_ticks_var"].get(),
            'min_low': sel["min_low_var"].get(),
            'min_high': sel["min_high_var"].get(),
            'max_low': sel["max_low_var"].get(),
            'max_high': sel["max_high_var"].get(),
        }
        settings['graphs'].append(graph_config)

    return settings


def _plot_export_image(app):
    """Export the current plot as PNG with embedded settings"""
    try:
        if not app.fig.get_axes():
            messagebox.showwarning("Warning", "No plot to export. Create plots first.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Save Plot as PNG",
            defaultextension=".png",
            initialfile="plot_export.png",
            filetypes=[("PNG Image", "*.png"), ("All", "*.*")]
        )
        if not out_path:
            return

        # Save the figure first to a temp location
        import tempfile
        temp_path = tempfile.mktemp(suffix='.png')
        app.fig.savefig(temp_path, dpi=200, bbox_inches='tight', facecolor=app.fig.get_facecolor())

        # Embed settings as PNG metadata
        settings = _plot_get_current_settings(app)
        settings_json = json.dumps(settings)

        # Read temp image and save with metadata to final location
        img = Image.open(temp_path)
        meta = PngImagePlugin.PngInfo()
        meta.add_text("jerry_settings", settings_json)
        img.save(out_path, "PNG", pnginfo=meta)
        img.close()

        # Clean up temp file
        os.remove(temp_path)

        app.plot_status.set(f"✓ Saved with settings")
        app.after(3000, lambda: app.plot_status.set(""))
        messagebox.showinfo("Success", f"Saved with settings:\n{out_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to export plot: {e}")


def _plot_load_from_graph(app):
    """Load settings from a previously saved graph PNG"""
    try:
        filepath = filedialog.askopenfilename(
            title="Load Settings from Graph",
            filetypes=[("PNG Image", "*.png"), ("All", "*.*")]
        )
        if not filepath:
            return

        # Read PNG and extract metadata
        img = Image.open(filepath)
        settings_json = img.info.get("jerry_settings")

        if not settings_json:
            messagebox.showwarning("Warning", "No settings found in this image.\nThis PNG was not saved with Jerry.")
            return

        settings = json.loads(settings_json)

        # Apply main title
        if 'main_title' in settings:
            app.plot_main_title.set(settings['main_title'])

        # Apply X-axis settings
        if 'x_min' in settings:
            app.plot_x_min.set(settings['x_min'])
        if 'x_max' in settings:
            app.plot_x_max.set(settings['x_max'])

        # Ensure we have enough graph rows
        num_graphs = settings.get('num_graphs', len(settings.get('graphs', [])))
        if num_graphs > len(app.graph_selectors):
            app.num_graphs_var.set(num_graphs)
            _plot_rebuild_graph_rows(app)

        # Apply graph settings
        for i, graph_config in enumerate(settings.get('graphs', [])):
            if i < len(app.graph_selectors):
                sel = app.graph_selectors[i]
                sel["title_var"].set(graph_config.get("title", ""))
                sel["y_label_var"].set(graph_config.get("y_label", ""))
                sel["y1_var"].set(graph_config.get("y1_var", ""))
                sel["y2_var"].set(graph_config.get("y2_var", ""))
                sel["y_min_var"].set(graph_config.get("y_min", ""))
                sel["y_max_var"].set(graph_config.get("y_max", ""))
                sel["y_ticks_var"].set(graph_config.get("y_ticks", ""))
                sel["min_low_var"].set(graph_config.get("min_low", ""))
                sel["min_high_var"].set(graph_config.get("min_high", ""))
                sel["max_low_var"].set(graph_config.get("max_low", ""))
                sel["max_high_var"].set(graph_config.get("max_high", ""))

        app.plot_status.set(f"✓ Loaded from {os.path.basename(filepath)}")
        app.after(3000, lambda: app.plot_status.set(""))
        messagebox.showinfo("Success", f"Settings loaded from:\n{os.path.basename(filepath)}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load settings: {e}")
