# Avg tab - Calculate averages, durations, and ramp rates across multiple cycle files

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

import pandas as pd

from powertech_tools.utils.file_parser import read_headers_only
from powertech_tools.utils.helpers import natural_sort_key, ScrollableFrame
from powertech_tools.data.processor import (
    stream_file_means,
    stream_file_duration_seconds,
    stream_ptank_initial_ramp_stats
)


def build_tab(parent, app):
    """
    Build the cycle averages tab UI.

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

    title_label = ttk.Label(f, text="Cycle Averages & Statistics", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Calculate averages, durations, and ramp rates across multiple cycle files",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection
    card1 = ttk.LabelFrame(f, text="Step 1: Select Cycle Files", padding=20)
    card1.pack(fill="x", pady=(0, 12))

    app.avg_files = []
    app.avg_files_label = tk.StringVar(value="No files selected")

    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x")

    ttk.Button(
        btn_frame,
        text="📁 Choose Cycle Files",
        command=lambda: _avg_choose_files(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Label(btn_frame, textvariable=app.avg_files_label, style='Status.TLabel').pack(side="left", padx=15)

    # Duration settings
    card2 = ttk.LabelFrame(f, text="Step 2: Duration Configuration", padding=20)
    card2.pack(fill="x", pady=(0, 12))

    app.duration_mode = tk.StringVar(value="Elapsed")
    dur_row = ttk.Frame(card2)
    dur_row.pack(fill="x")

    ttk.Label(dur_row, text="Mode:", width=15).pack(side="left")
    ttk.Combobox(
        dur_row, width=15, state="readonly",
        values=["Elapsed", "Time"], textvariable=app.duration_mode
    ).pack(side="left", padx=10)

    app.duration_col = tk.StringVar(value="")
    ttk.Label(dur_row, text="Column:", width=10).pack(side="left", padx=(20, 5))
    app.cb_duration_col = ttk.Combobox(dur_row, width=30, state="disabled", textvariable=app.duration_col, values=[])
    app.cb_duration_col.pack(side="left", padx=10)

    # Ramp rate settings
    card3 = ttk.LabelFrame(f, text="Step 3: Ptank Ramp Rate (Optional)", padding=20)
    card3.pack(fill="x", pady=(0, 12))

    app.compute_ramp = tk.BooleanVar(value=True)
    ramp_row1 = ttk.Frame(card3)
    ramp_row1.pack(fill="x", pady=(0, 8))

    ttk.Checkbutton(ramp_row1, text="Compute Ptank ramp rate", variable=app.compute_ramp).pack(side="left")

    ramp_row2 = ttk.Frame(card3)
    ramp_row2.pack(fill="x")

    ttk.Label(ramp_row2, text="Ptank Column:", width=15).pack(side="left")
    app.ptank_col = tk.StringVar(value="")
    app.cb_ptank_col = ttk.Combobox(ramp_row2, width=30, state="disabled", textvariable=app.ptank_col, values=[])
    app.cb_ptank_col.pack(side="left", padx=10)

    app.ramp_positive_only = tk.BooleanVar(value=True)
    ttk.Checkbutton(ramp_row2, text="Filling only (dP>0)", variable=app.ramp_positive_only).pack(side="left", padx=15)

    # Column selection
    card4 = ttk.LabelFrame(f, text="Step 4: Select Variables to Average", padding=20)
    card4.pack(fill="both", expand=False, pady=(0, 12))

    list_frame = ttk.Frame(card4)
    list_frame.pack(fill="both", expand=True)

    app.avg_cols_listbox = tk.Listbox(
        list_frame,
        selectmode="extended",
        height=8,
        bg="white",
        fg=PowertechTheme.TEXT_PRIMARY,
        font=(PowertechTheme.FONT_FAMILY, 9)
    )
    app.avg_cols_listbox.pack(side="left", fill="both", expand=True)
    sb = ttk.Scrollbar(list_frame, orient="vertical", command=app.avg_cols_listbox.yview)
    sb.pack(side="right", fill="y")
    app.avg_cols_listbox.configure(yscrollcommand=sb.set)

    # Actions
    card5 = ttk.LabelFrame(f, text="Step 5: Compute", padding=20)
    card5.pack(fill="x", pady=(0, 12))

    action_frame = ttk.Frame(card5)
    action_frame.pack(fill="x")

    ttk.Button(
        action_frame,
        text="📊 LOAD COLUMNS",
        command=lambda: _avg_load_cols(app)
    ).pack(side="left", padx=(0, 10))

    ttk.Button(
        action_frame,
        text="▶ COMPUTE AVERAGES",
        command=lambda: _avg_compute(app),
        style='Action.TButton'
    ).pack(side="left", padx=(0, 10))

    ttk.Button(
        action_frame,
        text="💾 SAVE RESULTS (CSV)",
        command=lambda: _avg_save_csv(app)
    ).pack(side="left")

    app.avg_status = tk.StringVar(value="")
    ttk.Label(action_frame, textvariable=app.avg_status, style='Status.TLabel').pack(side="left", padx=15)

    # Results
    card6 = ttk.LabelFrame(f, text="Results", padding=15)
    card6.pack(fill="both", expand=True)

    # Create frame for text with scrollbars
    text_frame = ttk.Frame(card6)
    text_frame.pack(fill="both", expand=True)

    # Scrollbars
    scrollbar_y = ttk.Scrollbar(text_frame, orient="vertical")
    scrollbar_x = ttk.Scrollbar(text_frame, orient="horizontal")

    app.avg_text = tk.Text(
        text_frame,
        height=15,
        wrap="none",
        bg="white",
        fg=PowertechTheme.TEXT_PRIMARY,
        font=(PowertechTheme.FONT_FAMILY, 9),
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )

    scrollbar_y.config(command=app.avg_text.yview)
    scrollbar_x.config(command=app.avg_text.xview)

    # Pack scrollbars and text
    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x.pack(side="bottom", fill="x")
    app.avg_text.pack(side="left", fill="both", expand=True)

    app.avg_results_df = None


def _avg_choose_files(app):
    """Handle file selection for averaging"""
    paths = filedialog.askopenfilenames(
        title="Select cycle files",
        filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
    )
    if not paths:
        return
    app.avg_files = sorted(list(paths), key=lambda p: natural_sort_key(os.path.basename(p)))
    app.avg_files_label.set(f"✓ {len(app.avg_files)} files selected")
    app.avg_status.set("Files ready")


def _avg_load_cols(app):
    """Load column names from the first selected file"""
    try:
        if not app.avg_files:
            messagebox.showerror("Error", "Please select files first")
            return

        headers, _delim, _idx, _lines = read_headers_only(app.avg_files[0])

        app.avg_cols_listbox.delete(0, tk.END)
        for h in headers:
            app.avg_cols_listbox.insert(tk.END, h)

        app.cb_duration_col["values"] = headers
        app.cb_duration_col["state"] = "readonly"

        app.cb_ptank_col["values"] = headers
        app.cb_ptank_col["state"] = "readonly"

        if "Elapsed" in headers:
            app.duration_col.set("Elapsed")
            app.duration_mode.set("Elapsed")
        elif "Time" in headers:
            app.duration_col.set("Time")
            app.duration_mode.set("Time")
        else:
            app.duration_col.set(headers[0])

        ptank_guess = None
        for h in headers:
            if h.lower() == "ptank" or h.lower().startswith("ptank"):
                ptank_guess = h
                break
        if ptank_guess is None:
            for h in headers:
                if "ptank" in h.lower():
                    ptank_guess = h
                    break
        app.ptank_col.set(ptank_guess if ptank_guess else (headers[0] if headers else ""))

        app.avg_status.set(f"✓ Loaded {len(headers)} columns")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def _avg_compute(app):
    """Compute averages for all selected files"""
    try:
        if not app.avg_files:
            messagebox.showerror("Error", "Please select files first")
            return

        dur_mode = app.duration_mode.get().strip()
        dur_col = app.duration_col.get().strip()
        if not dur_col:
            messagebox.showerror("Error", "Please select duration column")
            return

        sel = list(app.avg_cols_listbox.curselection())
        selected_cols = [app.avg_cols_listbox.get(i) for i in sel] if sel else []

        do_ramp = bool(app.compute_ramp.get())
        ptank_col = app.ptank_col.get().strip()
        if do_ramp and not ptank_col:
            messagebox.showerror("Error", "Please select Ptank column")
            return

        per_file_rows = []
        total_sums = {c: 0.0 for c in selected_cols}
        total_counts = {c: 0 for c in selected_cols}

        app.avg_text.delete("1.0", tk.END)
        app.avg_text.insert(tk.END, f"═══ PROCESSING {len(app.avg_files)} FILES ═══\n\n")
        app.avg_text.insert(tk.END, f"Duration Mode: {dur_mode} (Column: {dur_col})\n")
        if do_ramp:
            app.avg_text.insert(tk.END, f"Ramp Analysis: Enabled (Column: {ptank_col})\n")
        app.avg_text.insert(tk.END, f"Averaging: {len(selected_cols)} variables\n\n")

        for fp in app.avg_files:
            row = {"File": os.path.basename(fp)}

            dur_s = stream_file_duration_seconds(fp, dur_mode, dur_col, chunksize=50000)
            row["Cycle Duration (s)"] = dur_s

            if do_ramp:
                init_mean_mpa_min, init_max_mpa_min = stream_ptank_initial_ramp_stats(
                    fp,
                    time_mode=dur_mode,
                    time_col=dur_col,
                    ptank_col=ptank_col,
                    start_dp=1.0,
                    window_minutes=5.0,
                    window_dp=20.0,
                    min_points=30,
                    dt_min=0.02,
                    dt_max=2.0,
                    ramp_cap_mpa_min=50.0
                )
                row["Ptank Initial Ramp Mean (MPa/min)"] = init_mean_mpa_min
                row["Ptank Initial Ramp Max (MPa/min)"] = init_max_mpa_min

            if selected_cols:
                means, counts = stream_file_means(fp, selected_cols, chunksize=50000)
                for c in selected_cols:
                    row[f"{c} (mean)"] = means[c]
                    row[f"{c} (N)"] = counts[c]

                    if counts[c] and means[c] is not None:
                        total_sums[c] += means[c] * counts[c]
                        total_counts[c] += counts[c]

            per_file_rows.append(row)

        df = pd.DataFrame(per_file_rows)

        lines = []
        lines.append("═══════════════════════════════════")
        lines.append("     CYCLE DURATION SUMMARY")
        lines.append("═══════════════════════════════════")
        dur_series = pd.to_numeric(df["Cycle Duration (s)"], errors="coerce")
        if dur_series.notna().any():
            lines.append(f"Average Duration: {float(dur_series.mean()):.2f} s")
            lines.append(f"Min Duration:     {float(dur_series.min()):.2f} s")
            lines.append(f"Max Duration:     {float(dur_series.max()):.2f} s")
            lines.append(f"Total Duration:   {float(dur_series.sum()):.2f} s")
        else:
            lines.append("⚠ Duration could not be computed")
        lines.append("")

        if do_ramp:
            lines.append("═══════════════════════════════════")
            lines.append("    PTANK RAMP RATE ANALYSIS")
            lines.append("═══════════════════════════════════")

            mr = pd.to_numeric(df["Ptank Initial Ramp Mean (MPa/min)"], errors="coerce")
            mx = pd.to_numeric(df["Ptank Initial Ramp Max (MPa/min)"], errors="coerce")

            if mr.notna().any():
                lines.append(f"Avg Mean Ramp: {float(mr.mean()):.2f} MPa/min")
                lines.append(f"Max Mean Ramp: {float(mr.max()):.2f} MPa/min")
            else:
                lines.append("⚠ No ramp data found")
            if mx.notna().any():
                lines.append(f"Peak Ramp Rate: {float(mx.max()):.2f} MPa/min")
            lines.append("")

        if selected_cols:
            lines.append("═══════════════════════════════════")
            lines.append("    OVERALL SIGNAL AVERAGES")
            lines.append("═══════════════════════════════════")
            lines.append("Unweighted = avg of per-file means")
            lines.append("Weighted   = mean across all samples")
            lines.append("")
            for c in selected_cols:
                file_means = pd.to_numeric(df[f"{c} (mean)"], errors="coerce")
                unweighted = float(file_means.mean()) if file_means.notna().any() else None
                weighted = (total_sums[c] / total_counts[c]) if total_counts[c] > 0 else None
                lines.append(f"{c}:")
                lines.append(f"  Unweighted = {unweighted:.4f}" if unweighted else "  Unweighted = N/A")
                lines.append(f"  Weighted   = {weighted:.4f}" if weighted else "  Weighted   = N/A")

        lines.append("\n═══════════════════════════════════")
        lines.append("    PER-FILE RESULTS (First 25)")
        lines.append("═══════════════════════════════════\n")

        app.avg_text.insert(tk.END, "\n".join(lines))
        app.avg_text.insert(tk.END, "\n" + df.head(25).to_string(index=False))

        app.avg_results_df = df
        app.avg_status.set("✓ Analysis complete")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def _avg_save_csv(app):
    """Save the computed results to CSV"""
    try:
        if app.avg_results_df is None:
            messagebox.showerror("Error", "Please compute results first")
            return

        out_path = filedialog.asksaveasfilename(
            title="Save results",
            defaultextension=".csv",
            initialfile="cycle_averages.csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")]
        )
        if not out_path:
            return

        app.avg_results_df.to_csv(out_path, index=False)
        messagebox.showinfo("Success", f"Results saved to:\n{out_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
