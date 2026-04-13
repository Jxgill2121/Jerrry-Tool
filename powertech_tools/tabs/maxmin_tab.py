# MaxMin tab - Generate max/min values per cycle

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import pandas as pd

from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers
from powertech_tools.data.processor import compute_maxmin_template, compute_maxmin_from_multiple_files
from powertech_tools.utils.helpers import ScrollableFrame


def build_tab(parent, app):
    """Build the max/min tab UI."""
    scrollable = ScrollableFrame(parent)
    scrollable.pack(fill="both", expand=True)
    f = ttk.Frame(scrollable.content)
    f.pack(fill="both", expand=True, padx=15, pady=15)

    from powertech_tools.config.theme import PowertechTheme

    title_label = ttk.Label(f, text="Max/Min Converter", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Extract max and min values for each parameter per cycle",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # Mode selection
    mode_card = ttk.LabelFrame(f, text="Input Type", padding=20)
    mode_card.pack(fill="x", pady=(0, 15))

    app.mm_mode = tk.StringVar(value="multi_single")
    mode_frame = ttk.Frame(mode_card)
    mode_frame.pack(fill="x")

    ttk.Radiobutton(
        mode_frame,
        text="Multiple files, each file = 1 cycle",
        variable=app.mm_mode,
        value="multi_single",
        command=lambda: _mm_mode_changed(app)
    ).pack(anchor="w", pady=2)

    ttk.Radiobutton(
        mode_frame,
        text="Multiple files, each file has multiple cycles (Cycle column)",
        variable=app.mm_mode,
        value="multi_multi",
        command=lambda: _mm_mode_changed(app)
    ).pack(anchor="w", pady=2)

    ttk.Radiobutton(
        mode_frame,
        text="Single file with Cycle column",
        variable=app.mm_mode,
        value="single",
        command=lambda: _mm_mode_changed(app)
    ).pack(anchor="w", pady=2)

    # File selection
    card1 = ttk.LabelFrame(f, text="Input Files", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    app.mm_infile = tk.StringVar(value="")
    app.mm_infiles = []
    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x")

    app.mm_choose_btn = ttk.Button(
        btn_frame,
        text="Select TXT Files",
        command=lambda: _mm_choose_files(app),
        style='Action.TButton'
    )
    app.mm_choose_btn.pack(side="left")

    app.mm_files_label = tk.StringVar(value="No files selected")
    ttk.Label(btn_frame, textvariable=app.mm_files_label, style='Status.TLabel').pack(side="left", padx=15)

    # Column selection
    card2 = ttk.LabelFrame(f, text="Column Configuration", padding=20)
    card2.pack(fill="x", pady=(0, 15))

    app.mm_df = None
    app.mm_time_col = tk.StringVar(value="Time")
    app.mm_cycle_col = tk.StringVar(value="")

    col_frame = ttk.Frame(card2)
    col_frame.pack(fill="x")

    # Time column
    time_row = ttk.Frame(col_frame)
    time_row.pack(fill="x", pady=5)
    ttk.Label(time_row, text="Time Column:", width=20).pack(side="left")
    app.cb_mm_time = ttk.Combobox(time_row, state="disabled", width=40, textvariable=app.mm_time_col, values=[])
    app.cb_mm_time.pack(side="left", padx=10)

    # Cycle column (only for single file mode)
    app.mm_cycle_row = ttk.Frame(col_frame)
    app.mm_cycle_row.pack(fill="x", pady=5)
    ttk.Label(app.mm_cycle_row, text="Cycle Column:", width=20).pack(side="left")
    app.cb_mm_cycle = ttk.Combobox(app.mm_cycle_row, state="disabled", width=40, textvariable=app.mm_cycle_col, values=[])
    app.cb_mm_cycle.pack(side="left", padx=10)

    # Hide cycle row initially (multiple mode is default)
    app.mm_cycle_row.pack_forget()

    # Action
    action_card = ttk.LabelFrame(f, text="Generate Output", padding=20)
    action_card.pack(fill="x", pady=(0, 15))

    ttk.Button(
        action_card,
        text="CREATE MAX/MIN FILE",
        command=lambda: _mm_make(app),
        style='Action.TButton'
    ).pack(side="left")

    app.mm_status = tk.StringVar(value="")
    ttk.Label(action_card, textvariable=app.mm_status, style='Status.TLabel').pack(side="left", padx=15)

    # Preview
    prev_card = ttk.LabelFrame(f, text="Preview", padding=15)
    prev_card.pack(fill="both", expand=True)

    app.mm_preview = tk.Text(
        prev_card,
        height=18,
        wrap="none",
        bg="white",
        fg=PowertechTheme.TEXT_PRIMARY,
        font=(PowertechTheme.FONT_FAMILY, 9)
    )
    app.mm_preview.pack(fill="both", expand=True)


def _mm_mode_changed(app):
    """Handle mode change"""
    mode = app.mm_mode.get()
    if mode == "multi_single":
        app.mm_cycle_row.pack_forget()
        app.mm_choose_btn["text"] = "Select TXT Files"
    elif mode == "multi_multi":
        app.mm_cycle_row.pack(fill="x", pady=5)
        app.mm_choose_btn["text"] = "Select TXT Files"
        if app.mm_infiles:
            app.cb_mm_cycle["state"] = "readonly"
    else:  # single
        app.mm_cycle_row.pack(fill="x", pady=5)
        app.mm_choose_btn["text"] = "Select File"
        if app.mm_df is not None:
            app.cb_mm_cycle["state"] = "readonly"


def _mm_choose_files(app):
    """Handle file selection"""
    mode = app.mm_mode.get()

    if mode in ("multi_single", "multi_multi"):
        paths = filedialog.askopenfilenames(
            title="Select TXT files",
            filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
        )
        if not paths:
            return

        app.mm_infiles = list(paths)
        app.mm_files_label.set(f"{len(paths)} files selected")
        app.mm_df = None

        try:
            from powertech_tools.utils.file_parser import read_headers_only
            headers, _, _, _ = read_headers_only(paths[0])
            app.cb_mm_time["values"] = headers
            app.cb_mm_time["state"] = "readonly"

            # Auto-select Time
            for tc in ["Time", "time", "TIME"]:
                if tc in headers:
                    app.mm_time_col.set(tc)
                    break
            else:
                if headers:
                    app.mm_time_col.set(headers[0])

            # For multi_multi mode, also set up cycle column
            if mode == "multi_multi":
                app.cb_mm_cycle["values"] = headers
                app.cb_mm_cycle["state"] = "readonly"
                for cc in ["Cycle", "cycle", "CYCLE"]:
                    if cc in headers:
                        app.mm_cycle_col.set(cc)
                        break

        except Exception as e:
            messagebox.showerror("Error", f"Could not read headers: {e}")
            return

        app.mm_preview.delete("1.0", tk.END)
        app.mm_preview.insert(tk.END, f"{len(paths)} files selected\n\n")
        app.mm_preview.insert(tk.END, f"Columns: {', '.join(headers)}\n\n")
        app.mm_preview.insert(tk.END, "Files:\n")
        for i, p in enumerate(sorted(app.mm_infiles), start=1):
            app.mm_preview.insert(tk.END, f"  {i}. {os.path.basename(p)}\n")
        app.mm_status.set("Ready")

    else:  # single
        path = filedialog.askopenfilename(
            title="Select file with Cycle column",
            filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
        )
        if not path:
            return

        app.mm_infiles = []
        app.mm_files_label.set(os.path.basename(path))

        try:
            df = load_table_allow_duplicate_headers(path)
            app.mm_df = df
            app.mm_infile.set(path)

            cols = list(df.columns)
            app.cb_mm_time["values"] = cols
            app.cb_mm_cycle["values"] = cols
            app.cb_mm_time["state"] = "readonly"
            app.cb_mm_cycle["state"] = "readonly"

            # Auto-select
            for tc in ["Time", "time"]:
                if tc in cols:
                    app.mm_time_col.set(tc)
                    break
            for cc in ["Cycle", "cycle"]:
                if cc in cols:
                    app.mm_cycle_col.set(cc)
                    break

            app.mm_preview.delete("1.0", tk.END)
            app.mm_preview.insert(tk.END, f"Loaded: {len(df):,} rows x {len(cols)} columns\n\n")
            app.mm_preview.insert(tk.END, df.head(15).to_string(index=False))
            app.mm_status.set("Ready")

        except Exception as e:
            messagebox.showerror("Error", str(e))


def _mm_make(app):
    """Generate max/min file"""
    try:
        mode = app.mm_mode.get()
        time_c = app.mm_time_col.get().strip()

        if mode == "multi_single":
            # Multiple files, each = 1 cycle
            if not app.mm_infiles:
                messagebox.showerror("Error", "Select files first")
                return

            out_df = compute_maxmin_from_multiple_files(app.mm_infiles, time_c, min_points_per_file=10)

            app.mm_preview.delete("1.0", tk.END)
            app.mm_preview.insert(tk.END, f"Processed {len(app.mm_infiles)} cycles\n")
            app.mm_preview.insert(tk.END, f"Parameters: {(len(out_df.columns) - 2) // 2}\n")

        elif mode == "multi_multi":
            # Multiple files, each has multiple cycles
            if not app.mm_infiles:
                messagebox.showerror("Error", "Select files first")
                return

            cycle_c = app.mm_cycle_col.get().strip()
            if not cycle_c:
                messagebox.showerror("Error", "Select a Cycle column")
                return

            # Load and concatenate all files
            all_dfs = []
            for filepath in sorted(app.mm_infiles):
                df = load_table_allow_duplicate_headers(filepath)
                if cycle_c not in df.columns:
                    messagebox.showerror("Error", f"Cycle column '{cycle_c}' not in {os.path.basename(filepath)}")
                    return
                all_dfs.append(df)

            merged_df = pd.concat(all_dfs, ignore_index=True)

            out_df = compute_maxmin_template(
                merged_df, time_c, cycle_c,
                min_points_per_cycle=10,
                skip_cycle_zero=True
            )

            app.mm_preview.delete("1.0", tk.END)
            app.mm_preview.insert(tk.END, f"Processed {len(app.mm_infiles)} files\n")
            app.mm_preview.insert(tk.END, f"Output: {len(out_df)} cycles\n")

        else:  # single
            if app.mm_df is None:
                messagebox.showerror("Error", "Load a file first")
                return

            cycle_c = app.mm_cycle_col.get().strip()
            if not cycle_c or cycle_c not in app.mm_df.columns:
                messagebox.showerror("Error", "Select a valid Cycle column")
                return

            out_df = compute_maxmin_template(
                app.mm_df, time_c, cycle_c,
                min_points_per_cycle=10,
                skip_cycle_zero=True
            )

            app.mm_preview.delete("1.0", tk.END)
            app.mm_preview.insert(tk.END, f"Processed {len(out_df)} cycles\n")

        # Save
        out_path = filedialog.asksaveasfilename(
            title="Save max/min file",
            defaultextension=".txt",
            initialfile="maxmin_output.txt",
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

        app.mm_status.set("File created")
        messagebox.showinfo("Done", f"Saved: {out_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
