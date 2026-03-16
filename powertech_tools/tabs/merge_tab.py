# TDMS Conversion tab - Convert TDMS files to individual cycle TXT files

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict

from powertech_tools.data.tdms_converter import read_tdms_structure, convert_tdms_files_to_cycles
from powertech_tools.utils.helpers import ScrollableFrame, natural_sort_key


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
        text="Convert TDMS files to individual cycle TXT files (each TDMS file = one cycle)",
        style='Subtitle.TLabel'
    )
    desc_label.pack(anchor="w", pady=(0, 20))

    # File selection card
    card1 = ttk.LabelFrame(f, text="TDMS Files Selection", padding=20)
    card1.pack(fill="x", pady=(0, 15))

    # Store state in app instance
    app.tdms_files = []
    app.tdms_groups = []
    app.tdms_channels_dict = {}
    app.tdms_channel_vars = {}  # CheckButton variables for channel selection

    btn_frame = ttk.Frame(card1)
    btn_frame.pack(fill="x", pady=(0, 10))

    ttk.Button(
        btn_frame,
        text="📁 Choose TDMS Files",
        command=lambda: _tdms_choose_files(app),
        style='Action.TButton'
    ).pack(side="left")

    app.tdms_files_label = tk.StringVar(value="No files selected")
    ttk.Label(
        btn_frame,
        textvariable=app.tdms_files_label,
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

    # Time generation options
    time_frame = ttk.LabelFrame(config_frame, text="Time Column", padding=10)
    time_frame.pack(fill="x", pady=(10, 5))

    app.tdms_add_time = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        time_frame,
        text="Generate Time column",
        variable=app.tdms_add_time
    ).pack(anchor="w")

    timestep_row = ttk.Frame(time_frame)
    timestep_row.pack(fill="x", pady=(5, 0))
    ttk.Label(timestep_row, text="Time step (seconds):").pack(side="left")
    app.tdms_time_step = tk.StringVar(value="0.10")
    ttk.Entry(timestep_row, textvariable=app.tdms_time_step, width=10).pack(side="left", padx=10)

    app.tdms_add_datetime = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        time_frame,
        text="Include DateTime column (actual timestamps from TDMS)",
        variable=app.tdms_add_datetime
    ).pack(anchor="w", pady=(5, 0))

    # Cycle number column (optional)
    cycle_row = ttk.Frame(config_frame)
    cycle_row.pack(fill="x", pady=5)
    ttk.Label(cycle_row, text="Cycle # Column (optional):", width=20).pack(side="left")
    app.tdms_cycle_col = tk.StringVar(value="(None)")
    app.cb_tdms_cycle = ttk.Combobox(cycle_row, state="disabled", width=40, textvariable=app.tdms_cycle_col, values=[])
    app.cb_tdms_cycle.pack(side="left", padx=10)

    # Note
    note_label = ttk.Label(
        card2,
        text="Note: Select the group containing your test data, then select which parameters to include.",
        font=(PowertechTheme.FONT_FAMILY, 8),
        foreground="#666",
        justify="left"
    )
    note_label.pack(anchor="w", pady=(10, 0))

    # Parameters selection card
    card3 = ttk.LabelFrame(f, text="Select Parameters to Include", padding=15)
    card3.pack(fill="both", expand=True, pady=(0, 15))

    # Scrollable frame for checkboxes
    app.tdms_param_frame = ttk.Frame(card3)
    app.tdms_param_frame.pack(fill="both", expand=True)

    # Selection buttons
    btn_row = ttk.Frame(card3)
    btn_row.pack(fill="x", pady=(10, 0))
    ttk.Button(btn_row, text="Select All", command=lambda: _select_all_channels(app, True)).pack(side="left", padx=5)
    ttk.Button(btn_row, text="Deselect All", command=lambda: _select_all_channels(app, False)).pack(side="left")

    app.tdms_param_status = tk.StringVar(value="No channels available")
    ttk.Label(btn_row, textvariable=app.tdms_param_status, foreground="#666").pack(side="left", padx=15)

    # Action card
    action_card = ttk.LabelFrame(f, text="Convert to Cycle Files", padding=20)
    action_card.pack(fill="x", pady=(0, 0))

    ttk.Button(
        action_card,
        text="▶ CONVERT TO CYCLE FILES",
        command=lambda: _tdms_convert(app),
        style='Action.TButton'
    ).pack(side="left")

    app.tdms_status = tk.StringVar(value="")
    status_label = ttk.Label(action_card, textvariable=app.tdms_status, style='Status.TLabel')
    status_label.pack(side="left", padx=15)


def _tdms_choose_files(app):
    """Handle TDMS files selection"""
    paths = filedialog.askopenfilenames(
        title="Select TDMS files (each file = one cycle)",
        filetypes=[("TDMS Files", "*.tdms"), ("All", "*.*")]
    )
    if not paths:
        return

    try:
        app.tdms_files = sorted(list(paths), key=lambda p: natural_sort_key(os.path.basename(p)))
        app.tdms_files_label.set(f"✓ {len(app.tdms_files)} files selected")

        # Read structure from first file
        groups, channels_dict = read_tdms_structure(app.tdms_files[0])
        app.tdms_groups = groups
        app.tdms_channels_dict = channels_dict

        # Update group dropdown
        app.cb_tdms_group["values"] = groups
        app.cb_tdms_group["state"] = "readonly"

        # Auto-select first group if available
        if groups:
            app.tdms_group.set(groups[0])
            _tdms_group_changed(app)

        app.tdms_status.set("Ready to configure conversion")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read TDMS files: {e}")
        app.tdms_files = []
        app.tdms_files_label.set("No files selected")


def _tdms_group_changed(app):
    """Handle group selection change"""
    group = app.tdms_group.get()
    if not group or group not in app.tdms_channels_dict:
        return

    channels = app.tdms_channels_dict[group]

    # Update cycle column dropdown
    app.cb_tdms_cycle["values"] = ["(None)"] + channels
    app.cb_tdms_cycle["state"] = "readonly"

    # Try to auto-select cycle column
    channels_lower = [c.lower() for c in channels]
    if "cycle" in channels_lower:
        idx = channels_lower.index("cycle")
        app.tdms_cycle_col.set(channels[idx])
    else:
        app.tdms_cycle_col.set("(None)")

    # Build channel selection checkboxes
    _build_channel_checkboxes(app, channels)


def _build_channel_checkboxes(app, channels: List[str]):
    """Build checkboxes for channel selection"""
    # Clear existing checkboxes
    for widget in app.tdms_param_frame.winfo_children():
        widget.destroy()

    app.tdms_channel_vars = {}

    # Create scrollable canvas for many channels
    canvas = tk.Canvas(app.tdms_param_frame, height=300, bg="white")
    scrollbar = ttk.Scrollbar(app.tdms_param_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create checkboxes in 3 columns
    for idx, channel in enumerate(channels):
        var = tk.BooleanVar(value=True)  # All selected by default
        app.tdms_channel_vars[channel] = var

        row = idx // 3
        col = idx % 3

        cb = ttk.Checkbutton(scrollable_frame, text=channel, variable=var)
        cb.grid(row=row, column=col, sticky="w", padx=10, pady=2)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    app.tdms_param_status.set(f"{len(channels)} parameters available")


def _select_all_channels(app, select: bool):
    """Select or deselect all channels"""
    for var in app.tdms_channel_vars.values():
        var.set(select)


def _tdms_convert(app):
    """Execute TDMS conversion"""
    try:
        if not app.tdms_files:
            messagebox.showerror("Error", "Please select TDMS files first")
            return

        group = app.tdms_group.get()
        if not group:
            messagebox.showerror("Error", "Please select a data group")
            return

        # Get selected channels
        selected_channels = [ch for ch, var in app.tdms_channel_vars.items() if var.get()]
        if not selected_channels:
            messagebox.showerror("Error", "Please select at least one parameter")
            return

        # Get time generation options
        add_time = app.tdms_add_time.get()
        add_datetime = app.tdms_add_datetime.get()
        try:
            time_step = float(app.tdms_time_step.get())
            if time_step <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid time step. Please enter a positive number.")
            return

        # Get cycle column (optional)
        cycle_col = app.tdms_cycle_col.get().strip()
        if cycle_col == "(None)" or not cycle_col:
            cycle_col = None

        # Ask for output directory
        default_dir = os.path.dirname(app.tdms_files[0])
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
        created_files = convert_tdms_files_to_cycles(
            app.tdms_files,
            out_dir,
            group,
            selected_channels,
            add_time,
            time_step,
            cycle_col,
            add_datetime,
            progress
        )

        app.tdms_status.set(f"✓ Success! {len(created_files)} files created")
        messagebox.showinfo(
            "Conversion Complete",
            f"Created {len(created_files)} cycle files in:\n{out_dir}\n\n" +
            f"Parameters included: {', '.join(selected_channels[:5])}" +
            (f" and {len(selected_channels) - 5} more" if len(selected_channels) > 5 else "")
        )

    except Exception as e:
        app.tdms_status.set("Error")
        messagebox.showerror("Error", f"Conversion failed: {e}")
