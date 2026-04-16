"""
Cycle Viewer tab
Per-cycle and full-duration visualization with dual y-axes (pressure + temperature)
and spec sheet limit lines. Uses Plotly for interactive zoom/pan/hover.
"""

import io
import json
import os
import tempfile

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers, read_headers_only
from powertech_tools.utils.helpers import natural_sort_key

_ACCEPTED_TYPES = ["txt", "log", "dat", "csv", "tsv"]

# Data-series colours
_C = {
    "Ptank":  "#0066CC",
    "Tskin":  "#CC6600",
    "Tfluid": "#669900",
    "Tair":   "#00AAAA",
}
_LC = {
    "Phigh": "#CC0000",
    "Plow":  "#9900CC",
    "Thigh": "#FF6600",
    "Tlow":  "#006600",
}

_AUTO_MAP = {
    "ptank":   ["ptank",  "pressure", "p_tank"],
    "tskin":   ["tskin",  "t_skin",   "skintemp"],
    "tfluid":  ["tfluid", "t_fluid",  "tfuel",   "fluidtemp"],
    "tair":    ["tair",   "t_air",    "tamb",    "airtemp",  "ambient"],
    "time":    ["time",   "elapsed"],
    "cycle":   ["cycle"],
}


def _autodetect(cols: list, key: str) -> str:
    lower = {c.lower(): c for c in cols}
    for candidate in _AUTO_MAP.get(key, []):
        if candidate in lower:
            return lower[candidate]
    return ""


def render():
    st.subheader("Cycle Viewer")
    st.caption(
        "Per-cycle or full-duration view with Ptank (pressure, left axis) "
        "and temperatures (right axis). Spec-sheet limits shown as dashed lines."
    )

    # ── Step 1: Data source ───────────────────────────────────────────────────
    st.markdown("### Step 1: Load Data")
    mode = st.radio(
        "Input mode",
        ["Single file with Cycle column", "Multiple files (one per cycle)"],
        horizontal=True,
        key="cv_input_mode",
    )
    multi_mode = mode.startswith("Multiple")

    uploaded = st.file_uploader(
        "Choose file(s)",
        type=_ACCEPTED_TYPES,
        accept_multiple_files=multi_mode,
        key="cv_uploaded",
    )

    if not uploaded or (isinstance(uploaded, list) and len(uploaded) == 0):
        st.info("Upload a file to get started.")
        return

    uploaded_list = uploaded if isinstance(uploaded, list) else [uploaded]
    uploaded_list = sorted(uploaded_list, key=lambda f: natural_sort_key(f.name))
    current_names = [f.name for f in uploaded_list]

    if (
        st.session_state.get("cv_file_names") != current_names
        or st.session_state.get("cv_prev_multi") != multi_mode
    ):
        tmpdir = tempfile.mkdtemp()
        saved_paths = []
        for uf in uploaded_list:
            p = os.path.join(tmpdir, uf.name)
            with open(p, "wb") as fh:
                fh.write(uf.getbuffer())
            saved_paths.append(p)

        try:
            if multi_mode:
                headers, _, _, _ = read_headers_only(saved_paths[0])
                cv_df = None
                cycle_values = list(range(1, len(saved_paths) + 1))
            else:
                cv_df = load_table_allow_duplicate_headers(saved_paths[0])
                headers = list(cv_df.columns)
                cycle_values = []
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return

        st.session_state.update({
            "cv_file_names":   current_names,
            "cv_saved_paths":  saved_paths,
            "cv_prev_multi":   multi_mode,
            "cv_df":           cv_df,
            "cv_headers":      headers,
            "cv_cycle_values": cycle_values,
        })
        st.session_state.pop("cv_fig", None)

    headers:      list          = st.session_state["cv_headers"]
    saved_paths:  list          = st.session_state["cv_saved_paths"]
    cv_df:        pd.DataFrame  = st.session_state["cv_df"]
    cycle_values: list          = st.session_state["cv_cycle_values"]

    st.success(f"{len(uploaded_list)} file(s) — {len(headers)} columns")

    # ── Step 2: Column mapping ────────────────────────────────────────────────
    st.markdown("### Step 2: Column Mapping")

    col_opts = [""] + headers
    c1, c2 = st.columns(2)
    with c1:
        time_col  = st.selectbox("Time Column",  col_opts,
                                  index=col_opts.index(_autodetect(headers, "time"))  if _autodetect(headers, "time")  in col_opts else 0, key="cv_time_col")
        ptank_col = st.selectbox("Ptank",         col_opts,
                                  index=col_opts.index(_autodetect(headers, "ptank")) if _autodetect(headers, "ptank") in col_opts else 0, key="cv_ptank_col")
        tfluid_col= st.selectbox("Tfluid",        col_opts,
                                  index=col_opts.index(_autodetect(headers, "tfluid"))if _autodetect(headers, "tfluid")in col_opts else 0, key="cv_tfluid_col")

    with c2:
        if not multi_mode:
            cycle_col = st.selectbox("Cycle Column", col_opts,
                                      index=col_opts.index(_autodetect(headers, "cycle")) if _autodetect(headers, "cycle") in col_opts else 0, key="cv_cycle_col")
            # Update cycle list when cycle column changes
            if cv_df is not None and cycle_col and cycle_col in cv_df.columns:
                nums = pd.to_numeric(cv_df[cycle_col], errors="coerce").dropna().unique()
                cycle_values = sorted(int(c) for c in nums)
                st.session_state["cv_cycle_values"] = cycle_values
        else:
            cycle_col = ""

        tskin_col = st.selectbox("Tskin",  col_opts,
                                  index=col_opts.index(_autodetect(headers, "tskin")) if _autodetect(headers, "tskin") in col_opts else 0, key="cv_tskin_col")
        tair_col  = st.selectbox("Tair",   col_opts,
                                  index=col_opts.index(_autodetect(headers, "tair"))  if _autodetect(headers, "tair")  in col_opts else 0, key="cv_tair_col")

    graph_title = st.text_input("Graph Title", value=os.path.splitext(uploaded_list[0].name)[0],
                                 key="cv_graph_title")

    # ── Step 3: Spec limits + ticks ──────────────────────────────────────────
    st.markdown("### Step 3: Spec Sheet Limits")
    st.caption("Leave blank to skip. Pressure limits apply to left axis, temperature to right.")

    lc1, lc2, lc3, lc4 = st.columns(4)
    phigh_min = lc1.number_input("Phigh min", value=None, key="cv_phigh_min", format="%.2f")
    phigh_max = lc2.number_input("Phigh max", value=None, key="cv_phigh_max", format="%.2f")
    plow_min  = lc3.number_input("Plow min",  value=None, key="cv_plow_min",  format="%.2f")
    plow_max  = lc4.number_input("Plow max",  value=None, key="cv_plow_max",  format="%.2f")

    tc1, tc2, tc3, tc4 = st.columns(4)
    t_min   = tc1.number_input("T min",    value=None, key="cv_t_min",    format="%.2f")
    t_max   = tc2.number_input("T max",    value=None, key="cv_t_max",    format="%.2f")
    p_ticks = tc3.number_input("P Ticks",  value=None, key="cv_p_ticks",  format="%d", step=1)
    t_ticks = tc4.number_input("T Ticks",  value=None, key="cv_t_ticks",  format="%d", step=1)

    # Preset save/load
    with st.expander("Save / Load Presets (JSON)"):
        sp1, sp2 = st.columns(2)
        with sp1:
            pname = st.text_input("Preset name", key="cv_preset_name")
            if st.button("Save preset", key="cv_save_preset") and pname:
                preset = dict(
                    ptank_col=ptank_col, tskin_col=tskin_col,
                    tfluid_col=tfluid_col, tair_col=tair_col,
                    phigh_min=phigh_min, phigh_max=phigh_max,
                    plow_min=plow_min,   plow_max=plow_max,
                    t_min=t_min,         t_max=t_max,
                    p_ticks=p_ticks,     t_ticks=t_ticks,
                )
                st.download_button("Download preset JSON",
                                   data=json.dumps(preset, indent=2, default=str),
                                   file_name=f"{pname}.json", mime="application/json",
                                   key="cv_dl_preset")
        with sp2:
            pu = st.file_uploader("Load preset JSON", type=["json"], key="cv_preset_up")
            if pu:
                try:
                    p = json.loads(pu.read())
                    for k, v in p.items():
                        st.session_state[f"cv_{k}"] = v
                    st.success("Preset applied — scroll up and press Plot.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load preset: {e}")

    # ── Step 4: View mode + plot ──────────────────────────────────────────────
    st.markdown("### Step 4: View & Plot")
    view_mode = st.radio("View Mode", ["Per-Cycle", "Over Duration"],
                         horizontal=True, key="cv_view_mode")

    if view_mode == "Per-Cycle":
        if not cycle_values:
            st.warning("No cycles found. Check your Cycle Column selection.")
            return
        selected_cycle = st.select_slider(
            "Cycle", options=cycle_values, key="cv_selected_cycle"
        )
        plot_label = f"Cycle #{selected_cycle}"
    else:
        time_unit = st.selectbox("Time Unit", ["seconds", "minutes", "hours"],
                                  index=2, key="cv_time_unit")
        selected_cycle = None
        plot_label = "Full Duration"

    if st.button("PLOT", type="primary", key="cv_plot_btn"):
        try:
            # ── Assemble DataFrame ────────────────────────────────────────
            if view_mode == "Per-Cycle":
                if multi_mode:
                    idx = selected_cycle - 1
                    df = load_table_allow_duplicate_headers(saved_paths[idx])
                else:
                    df = cv_df[
                        pd.to_numeric(cv_df[cycle_col], errors="coerce") == selected_cycle
                    ].copy()
                    if df.empty:
                        st.error(f"No data for cycle {selected_cycle}.")
                        st.stop()

                if time_col and time_col in df.columns:
                    t = pd.to_numeric(df[time_col], errors="coerce").values
                    t = t - t[0]
                else:
                    t = np.arange(len(df))
                x_label = "Time [s]"

            else:  # Over Duration
                if multi_mode:
                    df = pd.concat(
                        [load_table_allow_duplicate_headers(p) for p in saved_paths],
                        ignore_index=True,
                    )
                else:
                    df = cv_df.copy()

                divisors = {"seconds": 1.0, "minutes": 60.0, "hours": 3600.0}
                div = divisors[time_unit]
                if time_col and time_col in df.columns:
                    t = pd.to_numeric(df[time_col], errors="coerce").values
                    t = (t - t[0]) / div
                else:
                    t = np.arange(len(df)) / div
                x_label = f"Time [{time_unit[0]}]"

            # ── Build Plotly figure ───────────────────────────────────────
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            def _add_series(col, name, color, secondary):
                if col and col in df.columns:
                    y = pd.to_numeric(df[col], errors="coerce").values
                    fig.add_trace(go.Scatter(
                        x=t, y=y, mode="lines",
                        line=dict(color=color, width=1.5),
                        name=name,
                        hovertemplate=f"<b>{name}</b><br>x: %{{x:.2f}}<br>y: %{{y:.4f}}<extra></extra>",
                    ), secondary_y=secondary)

            _add_series(ptank_col,  "Ptank",  _C["Ptank"],  False)
            _add_series(tskin_col,  "Tskin",  _C["Tskin"],  True)
            _add_series(tfluid_col, "Tfluid", _C["Tfluid"], True)
            _add_series(tair_col,   "Tair",   _C["Tair"],   True)

            # Limit lines as traces (so secondary_y is respected)
            x_span = [float(t[0]), float(t[-1])] if len(t) > 0 else [0, 1]

            def _limit_line(val, name, color, secondary, dash="dash"):
                if val is None:
                    return
                fig.add_trace(go.Scatter(
                    x=x_span, y=[val, val], mode="lines",
                    line=dict(color=color, dash=dash, width=1.2),
                    name=name, showlegend=True,
                    hovertemplate=f"<b>{name}</b>: {val}<extra></extra>",
                ), secondary_y=secondary)

            _limit_line(phigh_min, "Phigh_min", _LC["Phigh"], False)
            _limit_line(phigh_max, "Phigh_max", _LC["Phigh"], False)
            _limit_line(plow_min,  "Plow_min",  _LC["Plow"],  False)
            _limit_line(plow_max,  "Plow_max",  _LC["Plow"],  False)
            _limit_line(t_min,     "T_min",     _LC["Tlow"],  True)
            _limit_line(t_max,     "T_max",     _LC["Thigh"], True)

            # Axes labels
            fig.update_xaxes(title_text=x_label, gridcolor="rgba(0,0,0,0.08)")
            fig.update_yaxes(title_text="Pressure [MPa]", secondary_y=False,
                             title_font_color=_C["Ptank"],
                             tickfont_color=_C["Ptank"],
                             gridcolor="rgba(0,0,0,0.08)")
            fig.update_yaxes(title_text="Temperature [°C]", secondary_y=True,
                             title_font_color=_C["Tskin"],
                             tickfont_color=_C["Tskin"],
                             showgrid=False)

            # Tick overrides
            def _apply_ticks(n_ticks, secondary):
                if n_ticks and n_ticks > 1:
                    axis_key = "yaxis2" if secondary else "yaxis"
                    layout = fig.layout[axis_key]
                    lo = layout.range[0] if layout.range else None
                    hi = layout.range[1] if layout.range else None
                    if lo is not None and hi is not None:
                        vals = np.linspace(lo, hi, int(n_ticks)).tolist()
                        fig.update_layout(**{axis_key: dict(tickvals=vals)})

            _apply_ticks(p_ticks, False)
            _apply_ticks(t_ticks, True)

            fig.update_layout(
                title_text=f"{graph_title} — {plot_label}",
                height=520,
                plot_bgcolor="white",
                paper_bgcolor="white",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="top", y=-0.12,
                            xanchor="center", x=0.5),
                margin=dict(t=60, b=80, l=70, r=70),
            )

            st.session_state["cv_fig"] = fig

        except Exception as e:
            st.error(f"Plot failed: {e}")
            import traceback; traceback.print_exc()

    # ── Render ────────────────────────────────────────────────────────────────
    if "cv_fig" not in st.session_state:
        return

    fig = st.session_state["cv_fig"]
    st.plotly_chart(fig, use_container_width=True)

    ec1, ec2 = st.columns(2)
    with ec1:
        if st.button("Export PNG", key="cv_export_png"):
            try:
                png = fig.to_image(format="png", width=1400, height=600, scale=2)
                st.download_button("Download PNG", data=png,
                                   file_name="cycle_plot.png", mime="image/png",
                                   key="cv_dl_png")
            except Exception:
                html = fig.to_html(include_plotlyjs="cdn")
                st.download_button("Download HTML", data=html.encode(),
                                   file_name="cycle_plot.html", mime="text/html",
                                   key="cv_dl_html")
    with ec2:
        html_str = fig.to_html(include_plotlyjs="cdn")
        st.download_button("Download HTML (interactive)", data=html_str.encode(),
                           file_name="cycle_plot.html", mime="text/html",
                           key="cv_dl_html2")
