# TDMS Conversion tab - Convert TDMS files to individual cycle TXT files

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict

from powertech_tools.data.tdms_converter import read_tdms_structure, convert_tdms_to_cycle_files
from powertech_tools.utils.helpers import ScrollableFrame


def build_tab(parent, app):
    """
    Build the TDMS conversion tab UI.

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
    title_label = ttk.Label(f, text="TDMS to Cycle Files", style='Title.TLabel')
    title_label.pack(anchor="w", pady=(0, 5))

    desc_label = ttk.Label(
        f,
        text="Convert TDMS files directly to individual cycle TXT files",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection card
    card1 = ttk.LabelFrame(f, text="TDMS File Selection", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    # Store state in app instance
    app.tdms_file = tk.StringVar(value="")
    app.tdms_groups = []
    app.tdms_channels_dict = {}

    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x", pady=(0, 10))

    ttk.Button(
        btn_frame,
        text="📁 Choose TDMS File",
        command=lambda: _tdms_choose_file(app),
        style='Action.TButton'
    ).pack(side="left")

    app.tdms_file_label = tk.StringVar(value="No file selected")
    ttk.Label(
        btn_frame,
        textvariable=app.tdms_file_label,
        style='Status.TLabel'
    ).pack(side="left", padx=15)

    # Configuration card
    card2 = ttk.LabelFrame(f, text="Conversion Configuration", padding=20)
    card2.pack(fill="x", pady=(0, 15))

    config_frame = ttk.Frame(card2)
    config_frame.pack(fill="x")

    # Group selection
    group_row = ttk.Frame(config_frame)
    group_row.pack(fill="x", pady=5)
    ttk.Label(group_row, text="Data Group:", width=20).pack(side="left")
    app.tdms_group = tk.StringVar(value="")
    app.cb_tdms_group = ttk.Combobox(group_row, state="disabled", width=40, textvariable=app.tdms_group, values=[])
    app.cb_tdms_group.pack(side="left", padx=10)
    app.cb_tdms_group.bind("<<ComboboxSelected>>", lambda e: _tdms_group_changed(app))

    # Cycle column selection
    cycle_row = ttk.Frame(config_frame)
    cycle_row.pack(fill="x", pady=5)
    ttk.Label(cycle_row, text="Cycle Column:", width=20).pack(side="left")
    app.tdms_cycle_col = tk.StringVar(value="")
    app.cb_tdms_cycle = ttk.Combobox(cycle_row, state="disabled", width=40, textvariable=app.tdms_cycle_col, values=[])
    app.cb_tdms_cycle.pack(side="left", padx=10)

    # Time column selection
    time_row = ttk.Frame(config_frame)
    time_row.pack(fill="x", pady=5)
    ttk.Label(time_row, text="Time Column:", width=20).pack(side="left")
    app.tdms_time_col = tk.StringVar(value="")
    app.cb_tdms_time = ttk.Combobox(time_row, state="disabled", width=40, textvariable=app.tdms_time_col, values=[])
    app.cb_tdms_time.pack(side="left", padx=10)

    # Note
    note_label = ttk.Label(
        card2,
        text="Note: Select the group containing your test data, then select the cycle and time columns.\nIf no cycle column is selected, the entire file will be treated as one cycle.",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666",
        justify="left"
    )
    note_label.pack(anchor="w", pady=(10, 0))

    # Action card
    action_card = ttk.LabelFrame(f, text="Convert to Cycle Files", padding=20)
    action_card.pack(fill="x", pady=(0, 15))

    ttk.Button(
        action_card,
        text="▶ CONVERT TO CYCLE FILES",
        command=lambda: _tdms_convert(app),
        style='Action.TButton'
    ).pack(side="left")

    app.tdms_status = tk.StringVar(value="")
    status_label = ttk.Label(action_card, textvariable=app.tdms_status, style='Status.TLabel')
    status_label.pack(side="left", padx=15)

    # Preview card
    prev_card = ttk.LabelFrame(f, text="File Structure", padding=15)
    prev_card.pack(fill="both", expand=True, pady=(0, 0))

    app.tdms_preview = tk.Text(
        prev_card,
        height=15,
        wrap="none",
        bg="white",
        fg=PowertechTheme.TEXT_PRIMARY,
        font=(PowertechTheme.FONT_FAMILY, 9)
    )
    app.tdms_preview.pack(fill="both", expand=True)


def _tdms_choose_file(app):
    """Handle TDMS file selection"""
    path = filedialog.askopenfilename(
        title="Select TDMS file",
        filetypes=[("TDMS Files", "*.tdms"), ("All", "*.*")]
    )
    if not path:
        return

    try:
        app.tdms_file.set(path)
        app.tdms_file_label.set(f"✓ {os.path.basename(path)}")

        # Read TDMS structure
        groups, channels_dict = read_tdms_structure(path)
        app.tdms_groups = groups
        app.tdms_channels_dict = channels_dict

        # Update group dropdown
        app.cb_tdms_group["values"] = groups
        app.cb_tdms_group["state"] = "readonly"

        # Auto-select first group if available
        if groups:
            app.tdms_group.set(groups[0])
            _tdms_group_changed(app)

        # Show structure in preview
        app.tdms_preview.delete("1.0", tk.END)
        app.tdms_preview.insert(tk.END, f"✓ TDMS file loaded: {os.path.basename(path)}\n\n")
        app.tdms_preview.insert(tk.END, f"Groups found: {len(groups)}\n\n")

        for group in groups:
            channels = channels_dict[group]
            app.tdms_preview.insert(tk.END, f"Group: {group}\n")
            app.tdms_preview.insert(tk.END, f"  Channels ({len(channels)}): {', '.join(channels)}\n\n")

        app.tdms_status.set("Ready to configure conversion")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read TDMS file: {e}")
        app.tdms_file.set("")
        app.tdms_file_label.set("No file selected")


def _tdms_group_changed(app):
    """Handle group selection change"""
    group = app.tdms_group.get()
    if not group or group not in app.tdms_channels_dict:
        return

    channels = app.tdms_channels_dict[group]

    # Update channel dropdowns
    app.cb_tdms_cycle["values"] = ["(None)"] + channels
    app.cb_tdms_time["values"] = ["(None)"] + channels
    app.cb_tdms_cycle["state"] = "readonly"
    app.cb_tdms_time["state"] = "readonly"

    # Try to auto-select common column names
    channels_lower = [c.lower() for c in channels]

    # Auto-select cycle column
    if "cycle" in channels_lower:
        idx = channels_lower.index("cycle")
        app.tdms_cycle_col.set(channels[idx])
    else:
        app.tdms_cycle_col.set("(None)")

    # Auto-select time column
    time_candidates = ["time", "timestamp", "elapsed"]
    for candidate in time_candidates:
        if candidate in channels_lower:
            idx = channels_lower.index(candidate)
            app.tdms_time_col.set(channels[idx])
            break
    else:
        app.tdms_time_col.set("(None)")


def _tdms_convert(app):
    """Execute TDMS conversion"""
    try:
        tdms_path = app.tdms_file.get()
        if not tdms_path or not os.path.exists(tdms_path):
            messagebox.showerror("Error", "Please select a TDMS file first")
            return

        group = app.tdms_group.get()
        if not group:
            messagebox.showerror("Error", "Please select a data group")
            return

        # Get cycle and time columns (handle "(None)" selection)
        cycle_col = app.tdms_cycle_col.get().strip()
        if cycle_col == "(None)" or not cycle_col:
            cycle_col = None

        time_col = app.tdms_time_col.get().strip()
        if time_col == "(None)" or not time_col:
            time_col = None

        # Ask for output directory
        default_dir = os.path.dirname(tdms_path)
        out_dir = filedialog.askdirectory(
            title="Select output directory for cycle files",
            initialdir=default_dir
        )
        if not out_dir:
            return

        app.tdms_status.set("Converting...")

        # Progress callback
        def progress(current, total, msg):
            app.tdms_status.set(f"{msg} ({current}/{total})")
            app.update_idletasks()

        # Convert
        created_files = convert_tdms_to_cycle_files(
            tdms_path,
            out_dir,
            group,
            cycle_col,
            time_col,
            progress
        )

        app.tdms_status.set(f"✓ Success! {len(created_files)} files created")
        messagebox.showinfo(
            "Conversion Complete",
            f"Created {len(created_files)} cycle files in:\n{out_dir}\n\nFiles:\n" +
            "\n".join([os.path.basename(f) for f in created_files[:10]]) +
            (f"\n... and {len(created_files) - 10} more" if len(created_files) > 10 else "")
        )

    except Exception as e:
        app.tdms_status.set("Error")
        messagebox.showerror("Error", f"Conversion failed: {e}")
