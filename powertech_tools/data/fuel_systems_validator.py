# Fuel Systems validation engine

import os
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from powertech_tools.data.loader import read_headers_only


def detect_cycle_boundaries(
    df: pd.DataFrame,
    time_col: str,
    ptank_col: str,
    threshold: float = 2.0
) -> Tuple[int, int, float]:
    """
    Detect cycle boundaries by finding Ptank peak and working backwards/forwards to threshold.

    Args:
        df: DataFrame with cycle data
        time_col: Name of time column
        ptank_col: Name of Ptank column
        threshold: Ptank threshold in MPa (default 2.0)

    Returns:
        Tuple of (start_idx, end_idx, peak_time)
    """
    # Convert to numeric
    ptank = pd.to_numeric(df[ptank_col], errors='coerce')
    time = pd.to_numeric(df[time_col], errors='coerce')

    # Find peak
    peak_idx = ptank.idxmax()
    peak_value = ptank.iloc[peak_idx]
    peak_time = time.iloc[peak_idx]

    if pd.isna(peak_value):
        raise ValueError("Could not find valid Ptank peak")

    # Walk backwards to threshold
    start_idx = peak_idx
    for i in range(peak_idx, -1, -1):
        if ptank.iloc[i] <= threshold:
            start_idx = i
            break

    # Walk forwards to threshold
    end_idx = peak_idx
    for i in range(peak_idx, len(df)):
        if ptank.iloc[i] <= threshold:
            end_idx = i
            break

    return start_idx, end_idx, peak_time


def validate_tfuel_timing(
    df: pd.DataFrame,
    time_col: str,
    tfuel_col: str,
    start_idx: int,
    target_temp: float = -30.0,
    time_window: float = 30.0
) -> Tuple[bool, Optional[float], str]:
    """
    Validate that tfuel reaches target temperature within time window from cycle start.

    Args:
        df: DataFrame with cycle data
        time_col: Name of time column
        tfuel_col: Name of tfuel column
        start_idx: Cycle start index
        target_temp: Target temperature (default -30)
        time_window: Time window in seconds (default 30)

    Returns:
        Tuple of (passed, time_to_target, message)
    """
    time = pd.to_numeric(df[time_col], errors='coerce')
    tfuel = pd.to_numeric(df[tfuel_col], errors='coerce')

    start_time = time.iloc[start_idx]

    # Find when tfuel reaches target
    for i in range(start_idx, len(df)):
        current_time = time.iloc[i]
        current_tfuel = tfuel.iloc[i]

        if pd.isna(current_tfuel):
            continue

        elapsed = current_time - start_time

        if current_tfuel <= target_temp:
            if elapsed <= time_window:
                return True, elapsed, f"tfuel reached {target_temp}°C at {elapsed:.2f}s (within {time_window}s window)"
            else:
                return False, elapsed, f"tfuel reached {target_temp}°C at {elapsed:.2f}s (exceeded {time_window}s window)"

        if elapsed > time_window:
            # Time window exceeded without reaching target
            return False, None, f"tfuel did not reach {target_temp}°C within {time_window}s window (min value: {tfuel.iloc[start_idx:i].min():.2f}°C)"

    return False, None, f"tfuel never reached {target_temp}°C"


def validate_parameter_bounds(
    df: pd.DataFrame,
    start_idx: int,
    end_idx: int,
    param_limits: Dict[str, Dict[str, float]]
) -> List[str]:
    """
    Validate that parameters stay within min/max bounds during cycle.

    Args:
        df: DataFrame with cycle data
        start_idx: Cycle start index
        end_idx: Cycle end index
        param_limits: Dict mapping param name to {'min': value, 'max': value}

    Returns:
        List of violation messages
    """
    violations = []
    cycle_df = df.iloc[start_idx:end_idx+1]

    for param, limits in param_limits.items():
        if param not in df.columns:
            violations.append(f"{param}: Column not found")
            continue

        values = pd.to_numeric(cycle_df[param], errors='coerce')

        if values.isna().all():
            violations.append(f"{param}: No valid data")
            continue

        param_min = values.min()
        param_max = values.max()

        min_limit = limits.get('min')
        max_limit = limits.get('max')

        if min_limit is not None and param_min < min_limit:
            violations.append(f"{param}: Min {param_min:.2f} < {min_limit:.2f}")

        if max_limit is not None and param_max > max_limit:
            violations.append(f"{param}: Max {param_max:.2f} > {max_limit:.2f}")

    return violations


def validate_fuel_system_file(
    filepath: str,
    time_col: str,
    ptank_col: str,
    tfuel_col: str,
    param_limits: Dict[str, Dict[str, float]],
    ptank_threshold: float = 2.0,
    tfuel_target: float = -30.0,
    tfuel_window: float = 30.0
) -> Dict:
    """
    Validate a single fuel system cycle file.

    Args:
        filepath: Path to cycle TXT file
        time_col: Name of time column
        ptank_col: Name of Ptank column
        tfuel_col: Name of tfuel column
        param_limits: Parameter bounds to validate
        ptank_threshold: Ptank threshold for cycle detection (MPa)
        tfuel_target: Target tfuel temperature
        tfuel_window: Time window for tfuel check (seconds)

    Returns:
        Dict with validation results
    """
    from powertech_tools.data.loader import load_table_allow_duplicate_headers

    try:
        # Load file
        df = load_table_allow_duplicate_headers(filepath)

        # Check required columns exist
        for col in [time_col, ptank_col, tfuel_col]:
            if col not in df.columns:
                return {
                    'file': os.path.basename(filepath),
                    'status': 'ERROR',
                    'tfuel_check': False,
                    'tfuel_message': f"Column '{col}' not found",
                    'param_violations': [],
                    'cycle_start_idx': None,
                    'cycle_end_idx': None,
                    'total_points': len(df),
                    'cycle_points': 0
                }

        # Detect cycle boundaries
        start_idx, end_idx, peak_time = detect_cycle_boundaries(
            df, time_col, ptank_col, ptank_threshold
        )

        # Validate tfuel timing
        tfuel_pass, tfuel_time, tfuel_msg = validate_tfuel_timing(
            df, time_col, tfuel_col, start_idx, tfuel_target, tfuel_window
        )

        # Validate parameter bounds
        param_violations = validate_parameter_bounds(
            df, start_idx, end_idx, param_limits
        )

        # Overall status
        if tfuel_pass and len(param_violations) == 0:
            status = 'PASS'
        else:
            status = 'FAIL'

        return {
            'file': os.path.basename(filepath),
            'status': status,
            'tfuel_check': tfuel_pass,
            'tfuel_message': tfuel_msg,
            'param_violations': param_violations,
            'cycle_start_idx': start_idx,
            'cycle_end_idx': end_idx,
            'total_points': len(df),
            'cycle_points': end_idx - start_idx + 1
        }

    except Exception as e:
        return {
            'file': os.path.basename(filepath),
            'status': 'ERROR',
            'tfuel_check': False,
            'tfuel_message': str(e),
            'param_violations': [],
            'cycle_start_idx': None,
            'cycle_end_idx': None,
            'total_points': 0,
            'cycle_points': 0
        }
