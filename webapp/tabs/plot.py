"""
Data Visualization tab
Interactive Plotly charts for max/min values across cycles
Improvements over the desktop version:
  - Plotly replaces matplotlib: zoom, pan, hover tooltips, toggle series
  - st.data_editor with SelectboxColumn replaces the tkinter grid
  - JSON preset save/load replaces the PNG-metadata approach
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

from powertech_tools.utils.file_parser import load_maxmin_for_plot

_ACCEPTED_TYPES = ["txt", "log", "dat", "csv", "tsv"]
_COLOR_MIN   = "#0066CC"
_COLOR_MAX   = "#CC0000"
_COLOR_OTHER = "#2E86AB"

_EMPTY_GRAPH_ROW = {
    "Title": "", "Y Label": "Value",
    "Y1": "", "Y2": "",
    "Y Min": None, "Y Max": None, "Y Ticks": None,
    "Min Lower": None, "Min Upper": None,
    "Max Lower": None, "Max Upper": None,
}


def render():
    st.subheader("Data Visualization")
    st.caption("Interactive charts — zoom, pan, hover, toggle series in the legend")

    # --- Step 1: Upload file ---
    st.markdown("### Step 1: Load Max/Min File")
    uploaded_file = st.file_uploader(
        "Choose Max/Min File",
        type=_ACCEPTED_TYPES,
        accept_multiple_files=False,
        key="plot_uploaded_file",
    )

    if not uploaded_file:
        st.info("Upload a max/min file (output from the Max/Min Converter tab).")
        return

    if st.session_state.get("plot_file_name") != uploaded_file.name:
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, uploaded_file.name)
        with open(path, "wb") as fh:
            fh.write(uploaded_file.getbuffer())
        try:
            df, internal_cols, int_to_disp, int_kind = load_maxmin_for_plot(path)
        except Exception as e:
            st.error(f"Could not load file: {e}")
            return

        st.session_state.update({
            "plot_file_name":   uploaded_file.name,
            "plot_df":          df,
            "plot_int_cols":    internal_cols,
            "plot_int_to_disp": int_to_disp,
            "plot_int_kind":    int_kind,
        })
        st.session_state.pop("plot_fig", None)
        st.session_state.pop("plot_graph_config_df", None)

    df          = st.session_state["plot_df"]
    int_cols    = st.session_state["plot_int_cols"]
    int_to_disp = st.session_state["plot_int_to_disp"]
    int_kind    = st.session_state["plot_int_kind"]

    disp_names   = [int_to_disp[c] for c in int_cols]
    disp_to_int  = {v: k for k, v in int_to_disp.items()}

    # Y-variable options: only min/max parameter columns (exclude Cycle, Date Time)
    param_options = [""] + [
        int_to_disp[c] for c in int_cols
        if int_kind.get(c, "other") in ("min", "max")
    ]

    n_param_pairs = sum(1 for c in int_cols if int_kind.get(c) == "min")
    st.success(f"Loaded {len(df)} cycle(s) — {n_param_pairs} parameter pair(s)")

    # --- Step 2: Global settings ---
    st.markdown("### Step 2: Global Settings")
    col1, col2 = st.columns([3, 1])
    with col1:
        main_title = st.text_input("Main Title", placeholder="e.g. PL-006117", key="plot_main_title")
    with col2:
        cycle_options = [d for d in disp_names]
        default_cycle = "Cycle" if "Cycle" in disp_names else (disp_names[1] if len(disp_names) > 1 else disp_names[0])
        cycle_col_disp = st.selectbox(
            "Cycle Column",
            cycle_options,
            index=cycle_options.index(default_cycle) if default_cycle in cycle_options else 0,
            key="plot_cycle_col",
        )

    cx1, cx2 = st.columns(2)
    with cx1:
        x_min_val = st.number_input("X-Axis Min (cycles)", value=0, step=1, key="plot_x_min")
    with cx2:
        x_max_str = st.text_input("X-Axis Max (blank = auto)", value="", key="plot_x_max")
    x_max_val = float(x_max_str) if x_max_str.strip().lstrip("-").replace(".", "", 1).isdigit() else None

    # --- Step 3: Graph config table ---
    st.markdown("### Step 3: Configure Graphs")
    st.caption(
        "Each row = one subplot. Pick Y variables from the dropdowns — "
        "Min columns plot in blue, Max in red. Leave Y Min/Max blank for auto-scale."
    )

    n_graphs = st.number_input("Number of Graphs", min_value=1, max_value=10, value=2, step=1, key="plot_n_graphs")
    n_graphs = int(n_graphs)

    # Resize config table when n_graphs changes
    cfg = st.session_state.get("plot_graph_config_df")
    if cfg is None or len(cfg) != n_graphs:
        existing = cfg.to_dict("records") if cfg is not None else []
        rows = [existing[i] if i < len(existing) else dict(_EMPTY_GRAPH_ROW) for i in range(n_graphs)]
        st.session_state["plot_graph_config_df"] = pd.DataFrame(rows)
        cfg = st.session_state["plot_graph_config_df"]

    edited_cfg = st.data_editor(
        cfg,
        column_config={
            "Title":     st.column_config.TextColumn("Title"),
            "Y Label":   st.column_config.TextColumn("Y Label"),
            "Y1":        st.column_config.SelectboxColumn("Y1 Variable", options=param_options),
            "Y2":        st.column_config.SelectboxColumn("Y2 Variable (opt)", options=param_options),
            "Y Min":     st.column_config.NumberColumn("Y Min",     format="%.2f"),
            "Y Max":     st.column_config.NumberColumn("Y Max",     format="%.2f"),
            "Y Ticks":   st.column_config.NumberColumn("Y Ticks",   format="%d"),
            "Min Lower": st.column_config.NumberColumn("Min Lower", format="%.4f"),
            "Min Upper": st.column_config.NumberColumn("Min Upper", format="%.4f"),
            "Max Lower": st.column_config.NumberColumn("Max Lower", format="%.4f"),
            "Max Upper": st.column_config.NumberColumn("Max Upper", format="%.4f"),
        },
        use_container_width=True,
        hide_index=False,
        key="plot_cfg_editor",
        num_rows="fixed",
    )

    # --- Preset save / load ---
    with st.expander("Save / Load Presets (JSON)"):
        pc1, pc2 = st.columns(2)
        with pc1:
            preset_name = st.text_input("Preset name", key="plot_preset_name")
            if st.button("Save preset as JSON", key="plot_save_preset_btn") and preset_name:
                preset = {
                    "main_title": main_title,
                    "n_graphs":   n_graphs,
                    "x_min":      x_min_val,
                    "x_max":      x_max_str,
                    "graphs":     edited_cfg.to_dict("records"),
                }
                st.download_button(
                    "Download Preset",
                    data=json.dumps(preset, indent=2, default=str),
                    file_name=f"{preset_name}.json",
                    mime="application/json",
                    key="plot_dl_preset",
                )
        with pc2:
            preset_up = st.file_uploader("Upload preset JSON", type=["json"], key="plot_preset_up")
            if preset_up:
                try:
                    p = json.loads(preset_up.read())
                    loaded_rows = p.get("graphs", [])
                    loaded_n    = p.get("n_graphs", len(loaded_rows))
                    rows = [loaded_rows[i] if i < len(loaded_rows) else dict(_EMPTY_GRAPH_ROW)
                            for i in range(loaded_n)]
                    st.session_state["plot_graph_config_df"] = pd.DataFrame(rows)
                    st.session_state["plot_n_graphs_widget"] = loaded_n
                    st.success("Preset loaded — press Generate Plots.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load preset: {e}")

    # --- Generate ---
    st.markdown("### Step 4: Generate")
    if st.button("GENERATE PLOTS", type="primary", key="plot_gen_btn"):
        cycle_int = disp_to_int.get(cycle_col_disp)
        if not cycle_int or cycle_int not in df.columns:
            st.error("Invalid cycle column.")
        else:
            plot_df = df.copy()
            plot_df[cycle_int] = pd.to_numeric(plot_df[cycle_int], errors="coerce")
            plot_df = plot_df[plot_df[cycle_int].notna()].reset_index(drop=True)

            active = [r for _, r in edited_cfg.iterrows() if r.get("Y1") or r.get("Y2")]
            if not active:
                st.error("Select at least one Y variable in the table.")
            else:
                try:
                    fig = _build_figure(
                        plot_df, cycle_int, active,
                        disp_to_int, int_kind,
                        main_title, x_min_val, x_max_val,
                    )
                    st.session_state["plot_fig"] = fig
                except Exception as e:
                    st.error(f"Plot failed: {e}")

    # --- Render plot ---
    if "plot_fig" not in st.session_state:
        return

    fig = st.session_state["plot_fig"]
    st.plotly_chart(fig, use_container_width=True)

    # Export
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        if st.button("Export PNG", key="plot_export_png_btn"):
            try:
                png = fig.to_image(format="png", width=1600, height=300 * len(fig.data), scale=2)
                st.download_button("Download PNG", data=png, file_name="plot_export.png",
                                   mime="image/png", key="plot_dl_png")
            except Exception:
                html = fig.to_html(include_plotlyjs="cdn")
                st.download_button("Download HTML (interactive)", data=html.encode(),
                                   file_name="plot_export.html", mime="text/html", key="plot_dl_html")
    with ecol2:
        html_str = fig.to_html(include_plotlyjs="cdn")
        st.download_button("Download HTML (interactive)", data=html_str.encode(),
                           file_name="plot_export.html", mime="text/html", key="plot_dl_html2")


def _build_figure(df, cycle_col, active_graphs, disp_to_int, int_kind,
                  main_title, x_min, x_max):
    n = len(active_graphs)

    subplot_titles = [
        row.get("Title") or row.get("Y1") or f"Graph {i+1}"
        for i, row in enumerate(active_graphs)
    ]

    fig = make_subplots(
        rows=n, cols=1,
        shared_xaxes=True,
        subplot_titles=subplot_titles,
        vertical_spacing=max(0.03, 0.25 / n),
    )

    x = df[cycle_col]

    for i, row in enumerate(active_graphs, start=1):
        y_label   = row.get("Y Label") or "Value"
        y_min     = _to_float(row.get("Y Min"))
        y_max     = _to_float(row.get("Y Max"))
        y_ticks   = _to_int(row.get("Y Ticks"))
        min_lower = _to_float(row.get("Min Lower"))
        min_upper = _to_float(row.get("Min Upper"))
        max_lower = _to_float(row.get("Max Lower"))
        max_upper = _to_float(row.get("Max Upper"))

        for y_disp in [row.get("Y1", ""), row.get("Y2", "")]:
            if not y_disp:
                continue
            y_int = disp_to_int.get(y_disp)
            if not y_int or y_int not in df.columns:
                continue
            y     = pd.to_numeric(df[y_int], errors="coerce")
            kind  = int_kind.get(y_int, "other")
            color = _COLOR_MIN if kind == "min" else _COLOR_MAX if kind == "max" else _COLOR_OTHER

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="markers",
                marker=dict(color=color, size=4, opacity=0.75),
                name=y_disp,
                legendgroup=y_disp,
                hovertemplate=f"<b>{y_disp}</b><br>Cycle: %{{x}}<br>Value: %{{y:.4f}}<extra></extra>",
            ), row=i, col=1)

        # Limit lines — drawn as shapes so they don't clutter the legend
        for val, color, dash, label in [
            (min_lower, _COLOR_MIN, "dot",  "Min Lower"),
            (min_upper, _COLOR_MIN, "dot",  "Min Upper"),
            (max_lower, _COLOR_MAX, "dash", "Max Lower"),
            (max_upper, _COLOR_MAX, "dash", "Max Upper"),
        ]:
            if val is None:
                continue
            fig.add_hline(
                y=val, row=i, col=1,
                line=dict(color=color, dash=dash, width=1.5),
                annotation_text=f" {label}: {val}",
                annotation_font_size=10,
            )

        # Y-axis range + ticks
        y_axis_kwargs = dict(title_text=y_label, gridcolor="rgba(0,0,0,0.08)")
        if y_min is not None and y_max is not None:
            y_axis_kwargs["range"] = [y_min, y_max]
            if y_ticks is not None and y_ticks > 1:
                y_axis_kwargs["tickvals"] = np.linspace(y_min, y_max, y_ticks).tolist()
        fig.update_yaxes(**y_axis_kwargs, row=i, col=1)

    # X-axis
    x_range = None
    if x_min is not None or x_max is not None:
        x_range = [
            x_min if x_min is not None else float(x.min()),
            x_max if x_max is not None else float(x.max()),
        ]
    fig.update_xaxes(title_text="Cycle", gridcolor="rgba(0,0,0,0.08)",
                     range=x_range, row=n, col=1)

    fig.update_layout(
        title_text=main_title or None,
        height=max(350, 300 * n),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(t=80 if main_title else 40, b=40, l=60, r=40),
    )

    return fig


def _to_float(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _to_int(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) else int(f)
    except (TypeError, ValueError):
        return None
