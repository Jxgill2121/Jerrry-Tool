# Merge tab - Combine multiple log files into a single merged file

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List

from powertech_tools.data.loader import merge_selected_files
from powertech_tools.utils.helpers import natural_sort_key, ScrollableFrame


def build_tab(parent, app):
    """
    Build the merge tab UI.

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
    title_label = ttk.Label(f, text="Merge Multiple Log Files", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Combine multiple .txt log files into a single merged file for analysis",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection card
    card = ttk.LabelFrame(f, text="File Selection", padding=20)
    card.pack(fill="x", pady=(0, 15))

    # Store state in app instance
    app.merge_files = []
    app.merge_files_label = tk.StringVar(value="No files selected")

    btn_frame = ttk.Frame(card)
    btn_frame.pack(fill="x", pady=(0, 10))

    ttk.Button(
        btn_frame,
        text="📁 Choose Files",
        command=lambda: _merge_choose_files(app),
        style='Action.TButton'
    ).pack(side="left")

    ttk.Label(
        btn_frame,
        textvariable=app.merge_files_label,
        style='Status.TLabel'
    ).pack(side="left", padx=15)

    # Action card
    action_card = ttk.LabelFrame(f, text="Merge Operation", padding=20)
    action_card.pack(fill="x", pady=(0, 15))

    ttk.Button(
        action_card,
        text="▶ MERGE FILES",
        command=lambda: _merge_now(app),
        style='Action.TButton'
    ).pack(side="left")

    app.merge_status = tk.StringVar(value="")
    status_label = ttk.Label(action_card, textvariable=app.merge_status, style='Status.TLabel')
    status_label.pack(side="left", padx=15)


def _merge_choose_files(app):
    """Handle file selection for merge operation"""
    paths = filedialog.askopenfilenames(
        title="Select .txt log files to merge",
        filetypes=[("Text/Log", "*.txt *.log *.dat *.csv *.tsv"), ("All", "*.*")]
    )
    if not paths:
        return
    app.merge_files = sorted(list(paths), key=lambda p: natural_sort_key(os.path.basename(p)))
    app.merge_files_label.set(f"✓ {len(app.merge_files)} files selected")
    app.merge_status.set("Ready to merge")


def _merge_now(app):
    """Execute the merge operation"""
    try:
        if not app.merge_files:
            messagebox.showerror("Error", "Please select files first")
            return

        default_dir = os.path.dirname(app.merge_files[0])
        out_path = filedialog.asksaveasfilename(
            title="Save merged file",
            defaultextension=".txt",
            initialfile="merged_output.txt",
            initialdir=default_dir,
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if not out_path:
            return

        merge_selected_files(app.merge_files, out_path)
        app.merge_status.set(f"✓ Success! File saved")
        messagebox.showinfo("Complete", f"Merged file created:\n{out_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
