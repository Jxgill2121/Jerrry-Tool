"""
Fuel Systems Validation tab
Advanced cycle validation with Ptank-based fill detection and time-based tfuel checks
"""

import io
import json
import os
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from powertech_tools.data.fuel_systems_validator import validate_fuel_system_file
from powertech_tools.utils.file_parser import read_headers_only, load_table_allow_duplicate_headers

_ACCEPTED = ["txt", "log", "dat", "csv"]

_DARK_BG     = "#1a1a2e"
_PLOT_BG     = "#16213e"
_GRID_COLOR  = "#334155"
_TEXT_COLOR  = "#e2e8f0"
_TEXT_DIM    = "#94a3b8"
_LINE_COLORS = [
    "#00d4ff", "#ff6bcb", "#00ff88", "#ffd93d", "#ff8a50",
    "#a78bfa", "#34d399", "#f472b6", "#60a5fa", "#fb923c",
    "#c084fc", "#4ade80",
]


def render():
    st.subheader("Fuel Systems Validation")
    st.caption("Advanced cycle validation with Ptank-based cycle detection and time-based tfuel checks")

    # ── Step 1: Upload files ──────────────────────────────────────────────────
    st.markdown("### Step 1: Load Cycle Files")
    uploaded = st.file_uploader(
        "Choose cycle TXT/log files",
        type=_ACCEPTED,
        accept_multiple_files=True,
        key="fs_uploaded_files",
    )

    if not uploaded:
        st.info("Upload one or more cycle files (output of TDMS→Cycle converter).")
        return

    current_names = [f.name for f in uploaded]
    if st.session_state.get("fs_file_names") != current_names:
        tmpdir = tempfile.mkdtemp()
        paths = []
        for uf in uploaded:
            p = os.path.join(tmpdir, uf.name)
            with open(p, "wb") as fh:
                fh.write(uf.getbuffer())
            paths.append(p)
        try:
            headers, _, _, _ = read_headers_only(paths[0])
        except Exception as e:
            st.error(f"Could not read headers: {e}")
            return
        st.session_state.update({
            "fs_file_names":  current_names,
            "fs_paths":       paths,
            "fs_headers":     headers,
        })
        # clear downstream state
        for k in ("fs_results", "fs_cycle_data", "fs_param_df"):
            st.session_state.pop(k, None)

    paths   = st.session_state["fs_paths"]
    headers = st.session_state["fs_headers"]
    st.success(f"{len(paths)} file(s) loaded — {len(headers)} column(s) detected")

    # ── Step 2: Column selectors ──────────────────────────────────────────────
    st.markdown("### Step 2: Column Assignments")
    hl = [h.lower() for h in headers]

    def _default(candidates):
        for c in candidates:
            if c in hl:
                return headers[hl.index(c)]
        return headers[0]

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        time_col  = st.selectbox("Time Column",  headers, index=headers.index(_default(["time","elapsed"])), key="fs_time_col")
    with cc2:
        ptank_col = st.selectbox("Ptank Column", headers, index=headers.index(_default(["ptank"])), key="fs_ptank_col")
    with cc3:
        tfuel_col = st.selectbox("tfuel Column", headers, index=headers.index(_default(["tfuel"])), key="fs_tfuel_col")

    # ── Step 3: Validation configuration ─────────────────────────────────────
    st.markdown("### Step 3: Validation Configuration")

    with st.expander("Fill Detection", expanded=True):
        fd1, fd2 = st.columns(2)
        with fd1:
            ptank_threshold = st.number_input(
                "Ptank Threshold (MPa)",
                value=2.0, step=0.1, format="%.1f",
                help="Fill start detected from Ptank crossing this value",
                key="fs_ptank_threshold",
            )
        with fd2:
            end_mode = st.radio(
                "End of Fill Based On",
                ["Ptank", "SOC"],
                horizontal=True,
                key="fs_end_mode",
            )

        if end_mode == "SOC":
            s1, s2 = st.columns(2)
            with s1:
                soc_col_opts = [""] + headers
                soc_col_default = _default(["soc"]) if "soc" in hl else ""
                soc_col = st.selectbox(
                    "SOC Column",
                    soc_col_opts,
                    index=soc_col_opts.index(soc_col_default) if soc_col_default in soc_col_opts else 0,
                    key="fs_soc_col",
                )
            with s2:
                soc_threshold = st.number_input(
                    "SOC Threshold (%)",
                    value=100.0, step=1.0, format="%.1f",
                    key="fs_soc_threshold",
                )
        else:
            soc_col = None
            soc_threshold = 100.0

    with st.expander("tfuel Timing Check (optional)", expanded=True):
        enable_tfuel = st.checkbox("Enable tfuel timing check", value=True, key="fs_enable_tfuel")
        t1, t2 = st.columns(2)
        with t1:
            tfuel_target = st.number_input(
                "Target Temperature (°C)",
                value=-30.0, step=1.0, format="%.1f",
                disabled=not enable_tfuel,
                key="fs_tfuel_target",
            )
        with t2:
            tfuel_window = st.number_input(
                "Time Window (seconds)",
                value=30.0, step=1.0, format="%.0f",
                disabled=not enable_tfuel,
                key="fs_tfuel_window",
            )
        st.caption("tfuel must reach target temperature within the time window from fill start")

    with st.expander("Average Pressure Ramp Rate Check (optional)"):
        enable_ramp = st.checkbox("Enable ramp rate check", value=False, key="fs_enable_ramp")
        ramp_limit_str = st.text_input(
            "Min Ramp Rate (MPa/min) — leave blank to report only",
            value="",
            disabled=not enable_ramp,
            key="fs_ramp_limit",
        )
        ramp_limit = None
        if enable_ramp and ramp_limit_str.strip():
            try:
                ramp_limit = float(ramp_limit_str)
            except ValueError:
                st.warning("Invalid ramp rate limit — will report only.")

    # ── Step 4: Parameter bounds ──────────────────────────────────────────────
    st.markdown("### Step 4: Parameter Bounds")
    st.caption(
        "Select parameters to validate and set min/max bounds. "
        "tfuel bounds apply AFTER the timing window."
    )

    exclude = {time_col.lower(), ptank_col.lower()}
    param_headers = [h for h in headers if h.lower() not in exclude]

    if "fs_param_df" not in st.session_state or \
            list(st.session_state["fs_param_df"]["Parameter"]) != param_headers:
        rows = []
        for p in param_headers:
            rows.append({
                "Parameter": p,
                "Selected":  True,
                "Min":       None,
                "Max":       None,
            })
        st.session_state["fs_param_df"] = pd.DataFrame(rows)

    pb1, pb2 = st.columns([1, 1])
    with pb1:
        if st.button("Select All", key="fs_sel_all"):
            df_p = st.session_state["fs_param_df"].copy()
            df_p["Selected"] = True
            st.session_state["fs_param_df"] = df_p
            st.rerun()
    with pb2:
        if st.button("Deselect All", key="fs_desel_all"):
            df_p = st.session_state["fs_param_df"].copy()
            df_p["Selected"] = False
            st.session_state["fs_param_df"] = df_p
            st.rerun()

    edited_params = st.data_editor(
        st.session_state["fs_param_df"],
        column_config={
            "Parameter": st.column_config.TextColumn("Parameter", disabled=True),
            "Selected":  st.column_config.CheckboxColumn("Validate?"),
            "Min":       st.column_config.NumberColumn("Min Bound", format="%.4f"),
            "Max":       st.column_config.NumberColumn("Max Bound", format="%.4f"),
        },
        use_container_width=True,
        hide_index=True,
        key="fs_param_editor",
        num_rows="fixed",
    )

    # ── Preset save / load ────────────────────────────────────────────────────
    with st.expander("Save / Load Presets (JSON)"):
        pr1, pr2 = st.columns(2)
        with pr1:
            preset_name = st.text_input("Preset name", key="fs_preset_name")
            if st.button("Save preset as JSON", key="fs_save_preset") and preset_name:
                config_out = {
                    "ptank_threshold": ptank_threshold,
                    "end_mode":        end_mode,
                    "soc_threshold":   soc_threshold,
                    "enable_tfuel":    enable_tfuel,
                    "tfuel_target":    tfuel_target,
                    "tfuel_window":    tfuel_window,
                    "enable_ramp":     enable_ramp,
                    "ramp_limit":      ramp_limit_str,
                    "param_limits":    _build_param_limits(edited_params, tfuel_col),
                }
                st.download_button(
                    "Download Preset",
                    data=json.dumps(config_out, indent=2),
                    file_name=f"{preset_name}.json",
                    mime="application/json",
                    key="fs_dl_preset",
                )
        with pr2:
            preset_up = st.file_uploader("Upload preset JSON", type=["json"], key="fs_preset_up")
            if preset_up:
                try:
                    p = json.loads(preset_up.read())
                    param_limits_loaded = p.get("param_limits", {})
                    rows = []
                    for ph in param_headers:
                        lims = param_limits_loaded.get(ph, {})
                        rows.append({
                            "Parameter": ph,
                            "Selected":  ph in param_limits_loaded,
                            "Min":       lims.get("min"),
                            "Max":       lims.get("max"),
                        })
                    st.session_state["fs_param_df"] = pd.DataFrame(rows)
                    st.success("Preset loaded — press VALIDATE FILES.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load preset: {e}")

    # ── Step 5: Validate ──────────────────────────────────────────────────────
    st.markdown("### Step 5: Validate")
    if st.button("VALIDATE FILES", type="primary", key="fs_validate_btn"):
        param_limits = _build_param_limits(edited_params, tfuel_col)

        results     = []
        cycle_data  = []
        progress    = st.progress(0, text="Validating…")

        for i, filepath in enumerate(paths):
            progress.progress((i) / len(paths), text=f"Validating {i+1}/{len(paths)}: {os.path.basename(filepath)}")
            res = validate_fuel_system_file(
                filepath,
                time_col,
                ptank_col,
                tfuel_col,
                param_limits,
                ptank_threshold=ptank_threshold,
                tfuel_target=tfuel_target if enable_tfuel else 0.0,
                tfuel_window=tfuel_window if enable_tfuel else 30.0,
                enable_tfuel_check=enable_tfuel,
                end_mode=end_mode,
                soc_col=soc_col if soc_col else None,
                soc_threshold=soc_threshold,
                enable_ramp_check=enable_ramp,
                ramp_limit=ramp_limit,
            )
            results.append(res)
            if res["status"] != "ERROR":
                cycle_data.append({
                    "filepath": filepath,
                    "result":   res,
                    "config": {
                        "time_col":     time_col,
                        "ptank_col":    ptank_col,
                        "tfuel_col":    tfuel_col,
                        "param_limits": param_limits,
                        "tfuel_target": tfuel_target,
                        "tfuel_window": tfuel_window,
                    },
                })

        progress.progress(1.0, text="Done")
        st.session_state["fs_results"]    = results
        st.session_state["fs_cycle_data"] = cycle_data
        st.session_state["fs_viz_idx"]    = 0

    # ── Results ───────────────────────────────────────────────────────────────
    if "fs_results" not in st.session_state:
        return

    results    = st.session_state["fs_results"]
    cycle_data = st.session_state.get("fs_cycle_data", [])

    pass_n  = sum(1 for r in results if r["status"] == "PASS")
    fail_n  = sum(1 for r in results if r["status"] == "FAIL")
    error_n = sum(1 for r in results if r["status"] == "ERROR")

    st.markdown("### Results")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Total Files", len(results))
    mc2.metric("PASS", pass_n)
    mc3.metric("FAIL", fail_n)
    mc4.metric("ERROR", error_n)

    for res in results:
        status = res["status"]
        icon   = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⚠️")
        with st.expander(f"{icon} {res['file']} — {status}"):
            dc1, dc2 = st.columns(2)
            dc1.metric("Fill Points", res["cycle_points"])
            dc2.metric("Total Points", res["total_points"])

            tfuel_ok = res["tfuel_check"]
            st.markdown(f"**tfuel Check:** {'PASS' if tfuel_ok else 'FAIL'}")
            st.caption(res["tfuel_message"])

            if res.get("soc_message"):
                soc_icon = "✅" if res.get("soc_reached_100") else "❌"
                st.markdown(f"**SOC:** {soc_icon} {res['soc_message']}")

            if res.get("ramp_message"):
                ramp_ok = res.get("ramp_pass", True)
                st.markdown(f"**Ramp Rate:** {'PASS' if ramp_ok else 'FAIL'}")
                st.caption(res["ramp_message"])

            if res["param_violations"]:
                st.markdown("**Parameter Violations:**")
                for v in res["param_violations"]:
                    st.markdown(f"- {v}")
            else:
                st.success("All parameter bounds within limits")

    # Export TXT report
    report = _build_report(results)
    st.download_button(
        "Download TXT Report",
        data=report.encode("utf-8"),
        file_name="fuel_systems_validation_report.txt",
        mime="text/plain",
        key="fs_dl_report",
    )

    # ── Cycle Visualization ───────────────────────────────────────────────────
    if not cycle_data:
        return

    st.markdown("### Cycle Visualization")

    cycle_names = [os.path.basename(d["filepath"]) for d in cycle_data]
    sel_cycle = st.select_slider(
        "Select Cycle",
        options=cycle_names,
        key="fs_cycle_slider",
    )
    viz_idx = cycle_names.index(sel_cycle)

    try:
        fig = _build_cycle_figure(cycle_data[viz_idx], viz_idx, len(cycle_data))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Visualization error: {e}")


def _build_param_limits(df: pd.DataFrame, tfuel_col: str):
    limits = {}
    for _, row in df.iterrows():
        if not row.get("Selected", False):
            continue
        param = row["Parameter"]
        lim = {}
        mn = row.get("Min")
        mx = row.get("Max")
        if mn is not None and not (isinstance(mn, float) and np.isnan(mn)):
            lim["min"] = float(mn)
        if mx is not None and not (isinstance(mx, float) and np.isnan(mx)):
            lim["max"] = float(mx)
        if lim:
            limits[param] = lim
    return limits


def _build_cycle_figure(cycle_info: dict, idx: int, total: int) -> go.Figure:
    filepath = cycle_info["filepath"]
    result   = cycle_info["result"]
    config   = cycle_info["config"]

    df = load_table_allow_duplicate_headers(filepath)

    time_col  = config["time_col"]
    tfuel_col = config["tfuel_col"]

    # Build time axis
    time = pd.to_numeric(df[time_col], errors="coerce")
    if time.isna().all():
        time = pd.to_datetime(df[time_col], errors="coerce")
        if not time.isna().all():
            time = (time - time.iloc[0]).dt.total_seconds()
        else:
            time = pd.Series(range(len(df)), dtype=float)
    else:
        t0 = time.iloc[0] if not pd.isna(time.iloc[0]) else 0.0
        time = time - t0

    start_idx = result["cycle_start_idx"]
    end_idx   = result["cycle_end_idx"]
    t_start   = float(time.iloc[start_idx]) if start_idx is not None else float(time.iloc[0])
    t_end     = float(time.iloc[end_idx])   if end_idx   is not None else float(time.iloc[-1])
    t_tfuel_w = t_start + config["tfuel_window"]

    fig = go.Figure()

    plot_cols = [c for c in df.columns if c != time_col]
    for i, col in enumerate(plot_cols):
        y = pd.to_numeric(df[col], errors="coerce")
        if y.isna().all():
            continue
        color = _LINE_COLORS[i % len(_LINE_COLORS)]
        fig.add_trace(go.Scatter(
            x=time, y=y,
            mode="lines",
            name=col,
            line=dict(color=color, width=1.2),
            opacity=0.85,
        ))

    # Cycle boundary vertical lines
    x_span = [t_start, t_start]
    fig.add_trace(go.Scatter(
        x=[t_start, t_start], y=[-200, 200],
        mode="lines", name="Fill start",
        line=dict(color="#00ff88", width=2),
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=[t_end, t_end], y=[-200, 200],
        mode="lines", name="Fill end",
        line=dict(color="#c084fc", width=2),
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=[t_tfuel_w, t_tfuel_w], y=[-200, 200],
        mode="lines", name=f"tfuel window ({config['tfuel_window']}s)",
        line=dict(color="#ffd93d", width=1.5, dash="dash"),
        showlegend=True,
    ))

    # tfuel target horizontal line
    tfuel_target = config["tfuel_target"]
    fig.add_trace(go.Scatter(
        x=[float(time.iloc[0]), float(time.iloc[-1])],
        y=[tfuel_target, tfuel_target],
        mode="lines", name=f"tfuel target ({tfuel_target}°C)",
        line=dict(color="#ff4d4d", width=1.5, dash="dot"),
        showlegend=True,
    ))

    status_color = "#00ff88" if result["status"] == "PASS" else "#ff4d4d"
    fig.update_layout(
        title=dict(
            text=f"Cycle {idx+1}/{total}: {os.path.basename(filepath)} — {result['status']}",
            font=dict(color=status_color, size=13),
        ),
        height=500,
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_PLOT_BG,
        font=dict(color=_TEXT_COLOR),
        xaxis=dict(
            title="Time from file start (s)",
            gridcolor=_GRID_COLOR,
            color=_TEXT_DIM,
        ),
        yaxis=dict(
            title="Value",
            gridcolor=_GRID_COLOR,
            color=_TEXT_DIM,
            range=[-95, 110],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(26,26,46,0.8)",
            bordercolor=_GRID_COLOR,
        ),
        hovermode="x unified",
        margin=dict(t=60, b=50, l=60, r=20),
    )

    return fig


def _build_report(results: list) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("            Jerry - HITT TEAM ANALYSIS TOOL")
    lines.append("             FUEL SYSTEMS VALIDATION REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("VALIDATION SUMMARY")
    lines.append("-" * 80)
    total   = len(results)
    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    errors  = sum(1 for r in results if r["status"] == "ERROR")
    lines.append(f"Total Files : {total}")
    lines.append(f"PASSED      : {passed}")
    lines.append(f"FAILED      : {failed}")
    lines.append(f"ERRORS      : {errors}")
    lines.append("=" * 80)
    lines.append("")

    for res in results:
        sym = "V" if res["status"] == "PASS" else "X"
        lines.append(f"[{sym}] {res['file']} - {res['status']}")
        lines.append(f"  Fill Points  : {res['cycle_points']} (of {res['total_points']} total)")
        lines.append(f"  tfuel Check  : {'PASS' if res['tfuel_check'] else 'FAIL'}")
        lines.append(f"    {res['tfuel_message']}")
        if res.get("soc_message"):
            lines.append(f"  SOC          : {res['soc_message']}")
        if res.get("ramp_message"):
            ramp_s = "PASS" if res.get("ramp_pass", True) else "FAIL"
            lines.append(f"  Ramp Rate    : {ramp_s}")
            lines.append(f"    {res['ramp_message']}")
        if res["param_violations"]:
            lines.append("  Param Bounds : VIOLATIONS")
            for v in res["param_violations"]:
                lines.append(f"    - {v}")
        else:
            lines.append("  Param Bounds : All within limits")
        lines.append("")

    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    return "\n".join(lines)
