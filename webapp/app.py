"""
Jerry - Powertech Analysis Tools
Streamlit Web Application Entry Point
"""

import sys
import os

# Ensure the project root and webapp dir are on the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_webapp = os.path.dirname(os.path.abspath(__file__))
for _p in [_root, _webapp]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

st.set_page_config(
    page_title="Jerry - Powertech Analysis Tools",
    layout="wide",
)

st.title("Jerry - HITT Team Analysis Tool")
st.caption("Powertech – One Stop Tools (Surrey, BC)")

st.divider()

from tabs import merge, maxmin

TABS = {
    "TDMS to Cycle Files": merge.render,
    "Max/Min Converter":   maxmin.render,
}

tab_objects = st.tabs(list(TABS.keys()))
for tab_obj, (_, render_fn) in zip(tab_objects, TABS.items()):
    with tab_obj:
        render_fn()
