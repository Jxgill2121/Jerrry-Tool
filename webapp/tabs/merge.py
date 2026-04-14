"""
TDMS to Cycle Files tab
Converts TDMS files to individual cycle TXT files (each TDMS file = one cycle)
"""

import io
import os
import tempfile
import zipfile

import streamlit as st

from powertech_tools.data.tdms_converter import read_tdms_structure, convert_tdms_files_to_cycles
from powertech_tools.utils.helpers import natural_sort_key


def render():
    st.subheader("TDMS to Cycle Files")
    st.caption("Convert TDMS files to individual cycle TXT files (each TDMS file = one cycle)")

    # --- File upload ---
    uploaded_files = st.file_uploader(
        "Choose TDMS Files",
        type=["tdms"],
        accept_multiple_files=True,
        key="merge_uploaded_files",
    )

    if not uploaded_files:
        st.info("Upload one or more TDMS files to get started.")
        return

    uploaded_files = sorted(uploaded_files, key=lambda f: natural_sort_key(f.name))
    st.success(f"{len(uploaded_files)} file(s) selected")

    # Save to temp dir and read structure when file selection changes
    current_names = [f.name for f in uploaded_files]
    if st.session_state.get("merge_file_names") != current_names:
        tmpdir = tempfile.mkdtemp()
        saved_paths = []
        for uf in uploaded_files:
            path = os.path.join(tmpdir, uf.name)
            with open(path, "wb") as fh:
                fh.write(uf.getbuffer())
            saved_paths.append(path)

        try:
            groups, channels_dict = read_tdms_structure(saved_paths[0])
        except Exception as e:
            st.error(f"Failed to read TDMS structure: {e}")
            return

        st.session_state["merge_file_names"] = current_names
        st.session_state["merge_saved_paths"] = saved_paths
        st.session_state["merge_groups"] = groups
        st.session_state["merge_channels_dict"] = channels_dict
        # Clear any old channel selections when files change
        for key in list(st.session_state.keys()):
            if key.startswith("merge_ch_"):
                del st.session_state[key]

    groups: list = st.session_state["merge_groups"]
    channels_dict: dict = st.session_state["merge_channels_dict"]
    saved_paths: list = st.session_state["merge_saved_paths"]

    if not groups:
        st.error("No groups found in the TDMS file.")
        return

    # --- Configuration ---
    st.markdown("### Conversion Configuration")

    default_group = "Measurements" if "Measurements" in groups else groups[0]
    selected_group = st.selectbox(
        "Data Group",
        groups,
        index=groups.index(default_group),
        key="merge_selected_group",
    )

    channels = channels_dict.get(selected_group, [])

    with st.expander("Time Column Options", expanded=True):
        add_time = st.checkbox("Generate Time column", value=True, key="merge_add_time")
        time_step = st.number_input(
            "Time step (seconds)",
            value=0.10,
            min_value=0.001,
            step=0.01,
            format="%.3f",
            disabled=not add_time,
            key="merge_time_step",
        )
        add_datetime = st.checkbox(
            "Include DateTime column (actual timestamps from TDMS)",
            value=True,
            key="merge_add_datetime",
        )

    channels_lower = [c.lower() for c in channels]
    cycle_col_options = ["(None)"] + channels
    default_cycle_idx = (channels_lower.index("cycle") + 1) if "cycle" in channels_lower else 0
    cycle_col = st.selectbox(
        "Cycle # Column (optional)",
        cycle_col_options,
        index=default_cycle_idx,
        key="merge_cycle_col",
    )
    if cycle_col == "(None)":
        cycle_col = None

    # --- Channel selection ---
    st.markdown("### Select Parameters to Include")

    col_all, col_none = st.columns([1, 1])
    with col_all:
        if st.button("Select All"):
            for ch in channels:
                st.session_state[f"merge_ch_{ch}"] = True
            st.rerun()
    with col_none:
        if st.button("Deselect All"):
            for ch in channels:
                st.session_state[f"merge_ch_{ch}"] = False
            st.rerun()

    grid = st.columns(3)
    selected_channels = []
    for idx, channel in enumerate(channels):
        key = f"merge_ch_{channel}"
        if key not in st.session_state:
            st.session_state[key] = True
        checked = grid[idx % 3].checkbox(channel, key=key)
        if checked:
            selected_channels.append(channel)

    st.caption(f"{len(selected_channels)} / {len(channels)} parameters selected")

    # --- Convert ---
    st.markdown("### Convert")

    if st.button(
        "CONVERT TO CYCLE FILES",
        type="primary",
        disabled=len(selected_channels) == 0,
        key="merge_convert_btn",
    ):
        with st.spinner("Converting..."):
            try:
                out_dir = tempfile.mkdtemp()
                progress_placeholder = st.empty()
                log_lines: list[str] = []

                def progress(current, total, msg):
                    log_lines.append(f"({current}/{total}) {msg}")
                    progress_placeholder.info("\n".join(log_lines[-3:]))

                created_files = convert_tdms_files_to_cycles(
                    saved_paths,
                    out_dir,
                    selected_group,
                    selected_channels,
                    add_time,
                    time_step,
                    cycle_col,
                    add_datetime,
                    progress,
                )

                progress_placeholder.empty()

                # Zip all output files for download
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for fp in created_files:
                        zf.write(fp, os.path.basename(fp))
                zip_buffer.seek(0)

                st.success(f"Converted {len(created_files)} file(s) successfully!")
                st.download_button(
                    label=f"Download {len(created_files)} Cycle File(s) (ZIP)",
                    data=zip_buffer,
                    file_name="cycle_files.zip",
                    mime="application/zip",
                )

            except Exception as e:
                st.error(f"Conversion failed: {e}")
