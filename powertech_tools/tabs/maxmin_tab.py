# MaxMin tab - Generate max/min template from merged log file

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import pandas as pd

from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers
from powertech_tools.data.processor import compute_maxmin_template


def build_tab(parent, app):
    """
    Build the max/min analysis tab UI.

    Args:
        parent: Parent frame for this tab
        app: Main application instance (for storing state)
    """
    f = ttk.Frame(parent)
    f.pack(fill="both", expand=True, padx=20, pady=20)

    # Import theme for styling
    from powertech_tools.config.theme import PowertechTheme

    title_label = ttk.Label(f, text="Max/Min Analysis", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Generate max/min template from merged log file",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection
    card1 = ttk.LabelFrame(f, text="Input File", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    app.mm_infile = tk.StringVar(value="")
    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x")

    ttk.Button(
        btn_frame,
        text="📁 Choose Merged File",
        command=lambda: _mm_choose_file(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Label(btn_frame, textvariable=app.mm_infile, style='Status.TLabel').pack(side="left", padx=15)

    # Column selection
    card2 = ttk.LabelFrame(f, text="Column Configuration", padding=20)
    card2.pack(fill="x", pady=(0, 15))

    app.mm_df = None
    app.mm_time_col = tk.StringVar(value="")
    app.mm_cycle_col = tk.StringVar(value="")

    col_frame = ttk.Frame(card2)
    col_frame.pack(fill="x")

    # Time column
    time_row = ttk.Frame(col_frame)
    time_row.pack(fill="x", pady=5)
    ttk.Label(time_row, text="Time Column:", width=20).pack(side="left")
    app.cb_mm_time = ttk.Combobox(time_row, state="disabled", width=40, textvariable=app.mm_time_col, values=[])
    app.cb_mm_time.pack(side="left", padx=10)

    # Cycle column
    cycle_row = ttk.Frame(col_frame)
    cycle_row.pack(fill="x", pady=5)
    ttk.Label(cycle_row, text="Cycle Column:", width=20).pack(side="left")
    app.cb_mm_cycle = ttk.Combobox(cycle_row, state="disabled", width=40, textvariable=app.mm_cycle_col, values=[])
    app.cb_mm_cycle.pack(side="left", padx=10)

    # Action
    action_card = ttk.LabelFrame(f, text="Generate Analysis", padding=20)
    action_card.pack(fill="x", pady=(0, 15))

    ttk.Button(
        action_card,
        text="▶ CREATE MAX/MIN FILE",
        command=lambda: _mm_make(app),
        style='Action.TButton'
    ).pack(side="left")

    app.mm_status = tk.StringVar(value="")
    ttk.Label(action_card, textvariable=app.mm_status, style='Status.TLabel').pack(side="left", padx=15)

    # Preview
    prev_card = ttk.LabelFrame(f, text="Data Preview", padding=15)
    prev_card.pack(fill="both", expand=True, pady=(0, 0))

    app.mm_preview = tk.Text(
        prev_card,
        height=18,
        wrap="none",
        bg="white",
        fg=PowertechTheme.TEXT_PRIMARY,
        font=(PowertechTheme.FONT_FAMILY, 9)
    )
    app.mm_preview.pack(fill="both", expand=True)


def _mm_choose_file(app):
    """Handle file selection for max/min analysis"""
    path = filedialog.askopenfilename(
        title="Select merged log file",
        filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
    )
    if not path:
        return
    app.mm_infile.set(path)
    _mm_load_preview(app)


def _mm_load_preview(app):
    """Load and preview the selected file"""
    try:
        path = app.mm_infile.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", f"File not found: {path}")
            return

        df = load_table_allow_duplicate_headers(path)
        app.mm_df = df

        cols = list(df.columns)
        app.cb_mm_time["values"] = cols
        app.cb_mm_cycle["values"] = cols
        app.cb_mm_time["state"] = "readonly"
        app.cb_mm_cycle["state"] = "readonly"

        app.mm_time_col.set("Time" if "Time" in cols else cols[0])
        app.mm_cycle_col.set("Cycle" if "Cycle" in cols else cols[-1])

        app.mm_preview.delete("1.0", tk.END)
        preview_text = f"✓ Loaded: {len(df):,} rows × {len(cols)} columns\n\n"
        preview_text += df.head(20).to_string(index=False)
        app.mm_preview.insert(tk.END, preview_text)

        app.mm_status.set("✓ File loaded successfully")
    except Exception as e:
        app.mm_df = None
        messagebox.showerror("Error", str(e))


def _mm_make(app):
    """Generate the max/min template file"""
    try:
        if app.mm_df is None:
            messagebox.showerror("Error", "Please load a file first")
            return

        df = app.mm_df.copy()
        time_c = app.mm_time_col.get().strip()
        cycle_c = app.mm_cycle_col.get().strip()

        if time_c not in df.columns or cycle_c not in df.columns:
            messagebox.showerror("Error", "Invalid column selection")
            return

        out_df = compute_maxmin_template(df, time_c, cycle_c)

        default_name = os.path.splitext(os.path.basename(app.mm_infile.get().strip()))[0] + "_maxmin.txt"
        out_path = filedialog.asksaveasfilename(
            title="Save max/min file",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if not out_path:
            return

        header_block = ["Powertech Test Log", "Time step =0.10 s", "", "Cycle test"]

        with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
            for line in header_block:
                f.write(line + "\n")
            f.write("\t".join(list(out_df.columns)) + "\n")
            out_df.to_csv(f, sep="\t", index=False, header=False, lineterminator="\n")

        app.mm_status.set(f"✓ File created successfully")
        messagebox.showinfo("Complete", f"Max/Min file created:\n{out_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
