"""
Max/Min Converter tab
Extracts max and min values for each parameter per cycle
"""

import io
import os
import tempfile

import pandas as pd
import streamlit as st

from powertech_tools.data.processor import compute_maxmin_from_multiple_files, compute_maxmin_template
from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers, read_headers_only
from powertech_tools.utils.helpers import natural_sort_key

_ACCEPTED_TYPES = ["txt", "log", "dat", "csv", "tsv"]

_MODE_LABELS = {
    "multi_single": "Multiple files, each file = 1 cycle",
    "multi_multi":  "Multiple files, each file has multiple cycles (Cycle column)",
    "single":       "Single file with Cycle column",
}


def render():
    st.subheader("Max/Min Converter")
    st.caption("Extract max and min values for each parameter per cycle")

    # --- Mode ---
    mode = st.radio(
        "Input Type",
        options=list(_MODE_LABELS.keys()),
        format_func=_MODE_LABELS.__getitem__,
        key="mm_mode",
        horizontal=True,
    )

    # --- File upload ---
    # Always accept multiple; in "single" mode we only use the first file
    uploaded_files = st.file_uploader(
        "Choose File(s)",
        type=_ACCEPTED_TYPES,
        accept_multiple_files=True,
        key="mm_uploaded_files",
    )

    if not uploaded_files:
        st.info("Upload one or more files to get started.")
        return

    if mode == "single" and len(uploaded_files) > 1:
        st.warning("Single file mode — only the first file will be used.")
        uploaded_files = [uploaded_files[0]]

    uploaded_files = sorted(uploaded_files, key=lambda f: natural_sort_key(f.name))
    current_names = [f.name for f in uploaded_files]

    # Save to temp dir and read headers/data when selection or mode changes
    if (
        st.session_state.get("mm_file_names") != current_names
        or st.session_state.get("mm_prev_mode") != mode
    ):
        tmpdir = tempfile.mkdtemp()
        saved_paths = []
        for uf in uploaded_files:
            path = os.path.join(tmpdir, uf.name)
            with open(path, "wb") as fh:
                fh.write(uf.getbuffer())
            saved_paths.append(path)

        try:
            if mode == "single":
                df = load_table_allow_duplicate_headers(saved_paths[0])
                headers = list(df.columns)
                st.session_state["mm_df"] = df
            else:
                headers, _, _, _ = read_headers_only(saved_paths[0])
                st.session_state["mm_df"] = None
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return

        st.session_state["mm_file_names"] = current_names
        st.session_state["mm_saved_paths"] = saved_paths
        st.session_state["mm_headers"] = headers
        st.session_state["mm_prev_mode"] = mode
        st.session_state.pop("mm_result_df", None)

    headers: list = st.session_state.get("mm_headers", [])
    saved_paths: list = st.session_state.get("mm_saved_paths", [])

    if not headers:
        st.error("No columns found in file.")
        return

    st.success(f"{len(uploaded_files)} file(s) — {len(headers)} columns detected")

    # --- Column configuration ---
    st.markdown("### Column Configuration")

    def _default_idx(candidates):
        for c in candidates:
            if c in headers:
                return headers.index(c)
        return 0

    time_col = st.selectbox(
        "Time Column",
        headers,
        index=_default_idx(["Time", "time", "TIME"]),
        key="mm_time_col",
    )

    cycle_col = None
    if mode in ("multi_multi", "single"):
        cycle_col = st.selectbox(
            "Cycle Column",
            headers,
            index=_default_idx(["Cycle", "cycle", "CYCLE"]),
            key="mm_cycle_col",
        )

    # --- Generate ---
    st.markdown("### Generate Output")

    if st.button("CREATE MAX/MIN FILE", type="primary", key="mm_generate_btn"):
        with st.spinner("Processing..."):
            try:
                if mode == "multi_single":
                    out_df = compute_maxmin_from_multiple_files(
                        saved_paths, time_col, min_points_per_file=10
                    )

                elif mode == "multi_multi":
                    all_dfs = []
                    for fp in sorted(saved_paths, key=lambda p: natural_sort_key(os.path.basename(p))):
                        df = load_table_allow_duplicate_headers(fp)
                        if cycle_col not in df.columns:
                            st.error(f"Cycle column '{cycle_col}' not found in {os.path.basename(fp)}")
                            return
                        all_dfs.append(df)
                    merged = pd.concat(all_dfs, ignore_index=True)
                    out_df = compute_maxmin_template(
                        merged, time_col, cycle_col,
                        min_points_per_cycle=10, skip_cycle_zero=True,
                    )

                else:  # single
                    df = st.session_state.get("mm_df")
                    if df is None:
                        st.error("No data loaded.")
                        return
                    if cycle_col not in df.columns:
                        st.error(f"Cycle column '{cycle_col}' not found.")
                        return
                    out_df = compute_maxmin_template(
                        df, time_col, cycle_col,
                        min_points_per_cycle=10, skip_cycle_zero=True,
                    )

                st.session_state["mm_result_df"] = out_df

            except Exception as e:
                st.error(f"Processing failed: {e}")

    # --- Result ---
    if "mm_result_df" in st.session_state:
        out_df: pd.DataFrame = st.session_state["mm_result_df"]

        n_cycles = len(out_df)
        n_params = (len(out_df.columns) - 2) // 2  # subtract Date Time + Cycle, then pairs
        st.success(f"Generated {n_cycles} cycle(s) — {n_params} parameter(s)")

        # Build Powertech-format output
        buf = io.StringIO()
        buf.write("Powertech Test Log\nTime step =0.10 s\n\nCycle test\n")
        buf.write("\t".join(out_df.columns) + "\n")
        out_df.to_csv(buf, sep="\t", index=False, header=False, lineterminator="\n")

        st.download_button(
            label="Download Max/Min File (.txt)",
            data=buf.getvalue().encode("utf-8"),
            file_name="maxmin_output.txt",
            mime="text/plain",
        )

        st.markdown("### Preview")
        st.dataframe(out_df.head(20), use_container_width=True)
