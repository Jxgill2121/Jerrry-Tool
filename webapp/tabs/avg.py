"""
Cycle Averages & Statistics tab
Calculates averages, durations, and ramp rates across multiple cycle files
"""

import io
import os
import tempfile

import pandas as pd
import streamlit as st

from powertech_tools.data.processor import (
    stream_file_duration_seconds,
    stream_file_means,
    stream_ptank_initial_ramp_stats,
)
from powertech_tools.utils.file_parser import read_headers_only
from powertech_tools.utils.helpers import natural_sort_key

_ACCEPTED_TYPES = ["txt", "log", "dat", "csv", "tsv"]


def render():
    st.subheader("Cycle Averages & Statistics")
    st.caption("Calculate averages, durations, and ramp rates across multiple cycle files")

    # --- Step 1: File upload ---
    st.markdown("### Step 1: Select Cycle Files")
    uploaded_files = st.file_uploader(
        "Choose Cycle Files",
        type=_ACCEPTED_TYPES,
        accept_multiple_files=True,
        key="avg_uploaded_files",
    )

    if not uploaded_files:
        st.info("Upload one or more cycle files to get started.")
        return

    uploaded_files = sorted(uploaded_files, key=lambda f: natural_sort_key(f.name))
    current_names = [f.name for f in uploaded_files]

    # Save to temp dir and read headers when selection changes
    if st.session_state.get("avg_file_names") != current_names:
        tmpdir = tempfile.mkdtemp()
        saved_paths = []
        for uf in uploaded_files:
            path = os.path.join(tmpdir, uf.name)
            with open(path, "wb") as fh:
                fh.write(uf.getbuffer())
            saved_paths.append(path)

        try:
            headers, _, _, _ = read_headers_only(saved_paths[0])
        except Exception as e:
            st.error(f"Could not read file headers: {e}")
            return

        st.session_state["avg_file_names"] = current_names
        st.session_state["avg_saved_paths"] = saved_paths
        st.session_state["avg_headers"] = headers
        st.session_state.pop("avg_result_df", None)

    headers: list = st.session_state.get("avg_headers", [])
    saved_paths: list = st.session_state.get("avg_saved_paths", [])

    if not headers:
        st.error("No columns found in file.")
        return

    st.success(f"{len(uploaded_files)} file(s) selected — {len(headers)} columns detected")

    # --- Step 2: Duration configuration ---
    st.markdown("### Step 2: Duration Configuration")
    col1, col2 = st.columns(2)

    with col1:
        dur_mode = st.selectbox(
            "Mode",
            ["Elapsed", "Time"],
            key="avg_dur_mode",
        )

    with col2:
        def _default_idx(candidates):
            for c in candidates:
                if c in headers:
                    return headers.index(c)
            return 0

        dur_col = st.selectbox(
            "Column",
            headers,
            index=_default_idx(["Elapsed", "Time", "time"]),
            key="avg_dur_col",
        )

    # --- Step 3: Ramp rate (optional) ---
    st.markdown("### Step 3: Ptank Ramp Rate (Optional)")
    do_ramp = st.checkbox("Compute Ptank ramp rate", value=True, key="avg_do_ramp")

    if do_ramp:
        ptank_col = st.selectbox(
            "Ptank Column",
            headers,
            index=_default_idx(["Ptank", "ptank", "PTank"]),
            key="avg_ptank_col",
        )
    else:
        ptank_col = None

    # --- Step 4: Columns to average ---
    st.markdown("### Step 4: Select Variables to Average")
    # Default: exclude obvious non-numeric columns
    non_avg_defaults = {"Time", "time", "Elapsed", "elapsed", "DateTime", "Cycle", "cycle", "Date  Time"}
    default_cols = [h for h in headers if h not in non_avg_defaults]

    selected_cols = st.multiselect(
        "Columns to average",
        options=headers,
        default=default_cols,
        key="avg_selected_cols",
    )

    # --- Step 5: Compute ---
    st.markdown("### Step 5: Compute")

    if st.button("COMPUTE AVERAGES", type="primary", key="avg_compute_btn"):
        if not dur_col:
            st.error("Please select a duration column.")
        elif do_ramp and not ptank_col:
            st.error("Please select a Ptank column.")
        else:
            with st.spinner(f"Processing {len(saved_paths)} file(s)..."):
                try:
                    per_file_rows = []
                    total_sums = {c: 0.0 for c in selected_cols}
                    total_counts = {c: 0 for c in selected_cols}

                    progress = st.progress(0)
                    for i, fp in enumerate(saved_paths):
                        row = {"File": os.path.basename(fp)}

                        row["Cycle Duration (s)"] = stream_file_duration_seconds(
                            fp, dur_mode, dur_col, chunksize=50000
                        )

                        if do_ramp:
                            mean_ramp, max_ramp = stream_ptank_initial_ramp_stats(
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
                                ramp_cap_mpa_min=50.0,
                            )
                            row["Ptank Ramp Mean (MPa/min)"] = mean_ramp
                            row["Ptank Ramp Max (MPa/min)"] = max_ramp

                        if selected_cols:
                            means, counts = stream_file_means(fp, selected_cols, chunksize=50000)
                            for c in selected_cols:
                                row[f"{c} (mean)"] = means[c]
                                row[f"{c} (N)"] = counts[c]
                                if counts[c] and means[c] is not None:
                                    total_sums[c] += means[c] * counts[c]
                                    total_counts[c] += counts[c]

                        per_file_rows.append(row)
                        progress.progress((i + 1) / len(saved_paths))

                    progress.empty()
                    result_df = pd.DataFrame(per_file_rows)
                    st.session_state["avg_result_df"] = result_df
                    st.session_state["avg_total_sums"] = total_sums
                    st.session_state["avg_total_counts"] = total_counts
                    st.session_state["avg_selected_cols_snapshot"] = selected_cols
                    st.session_state["avg_do_ramp_snapshot"] = do_ramp

                except Exception as e:
                    st.error(f"Computation failed: {e}")

    # --- Results ---
    if "avg_result_df" not in st.session_state:
        return

    result_df: pd.DataFrame = st.session_state["avg_result_df"]
    total_sums: dict = st.session_state["avg_total_sums"]
    total_counts: dict = st.session_state["avg_total_counts"]
    snap_cols: list = st.session_state["avg_selected_cols_snapshot"]
    snap_ramp: bool = st.session_state["avg_do_ramp_snapshot"]

    st.success("Analysis complete")

    # Duration summary
    st.markdown("### Duration Summary")
    dur_series = pd.to_numeric(result_df["Cycle Duration (s)"], errors="coerce")
    if dur_series.notna().any():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Duration", f"{dur_series.mean():.2f} s")
        c2.metric("Min Duration", f"{dur_series.min():.2f} s")
        c3.metric("Max Duration", f"{dur_series.max():.2f} s")
        c4.metric("Total Duration", f"{dur_series.sum():.2f} s")
    else:
        st.warning("Duration could not be computed.")

    # Ramp rate summary
    if snap_ramp and "Ptank Ramp Mean (MPa/min)" in result_df.columns:
        st.markdown("### Ptank Ramp Rate")
        mr = pd.to_numeric(result_df["Ptank Ramp Mean (MPa/min)"], errors="coerce")
        mx = pd.to_numeric(result_df["Ptank Ramp Max (MPa/min)"], errors="coerce")
        if mr.notna().any():
            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Mean Ramp", f"{mr.mean():.2f} MPa/min")
            c2.metric("Max Mean Ramp", f"{mr.max():.2f} MPa/min")
            c3.metric("Peak Ramp Rate", f"{mx.max():.2f} MPa/min" if mx.notna().any() else "N/A")
        else:
            st.warning("No ramp data found in any file.")

    # Signal averages
    if snap_cols:
        st.markdown("### Signal Averages")
        avg_rows = []
        for c in snap_cols:
            file_means = pd.to_numeric(result_df.get(f"{c} (mean)", pd.Series()), errors="coerce")
            unweighted = float(file_means.mean()) if file_means.notna().any() else None
            weighted = (total_sums[c] / total_counts[c]) if total_counts.get(c, 0) > 0 else None
            avg_rows.append({
                "Parameter": c,
                "Unweighted Mean": f"{unweighted:.4f}" if unweighted is not None else "N/A",
                "Weighted Mean": f"{weighted:.4f}" if weighted is not None else "N/A",
            })
        st.dataframe(pd.DataFrame(avg_rows), use_container_width=True, hide_index=True)

    # Per-file results
    st.markdown("### Per-File Results")
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    # Download
    csv_buf = io.StringIO()
    result_df.to_csv(csv_buf, index=False)
    st.download_button(
        label="Download Results (CSV)",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="cycle_averages.csv",
        mime="text/csv",
    )
