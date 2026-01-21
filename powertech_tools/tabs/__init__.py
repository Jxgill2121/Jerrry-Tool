# Tab modules for Powertech Tools application

from powertech_tools.tabs.merge_tab import build_tab as build_merge_tab
from powertech_tools.tabs.maxmin_tab import build_tab as build_maxmin_tab
from powertech_tools.tabs.plot_tab import build_tab as build_plot_tab
from powertech_tools.tabs.avg_tab import build_tab as build_avg_tab
from powertech_tools.tabs.validation_tab import build_tab as build_validation_tab

__all__ = [
    'build_merge_tab',
    'build_maxmin_tab',
    'build_plot_tab',
    'build_avg_tab',
    'build_validation_tab',
]