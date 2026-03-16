# ASR (Accelerated Stress Rupture) validation utilities
# Calculates cumulative time within temperature bands for tank testing

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np


def validate_asr_temperature(
    df: pd.DataFrame,
    time_col: str,
    temp_col: str,
    temp_min: float,
    temp_max: float,
    time_unit: str = "seconds"
) -> Tuple[Dict, pd.DataFrame]:
    """
    Validate ASR test data by calculating cumulative time within temperature band.

    ASR tests measure how long a tank sustains exposure to a target temperature range.
    Unlike cycle validation (pass/fail), ASR tracks cumulative duration within the band.

    Args:
        df: DataFrame with time series data
        time_col: Name of the time column
        temp_col: Name of the temperature column to validate
        temp_min: Minimum acceptable temperature (e.g., 83.0)
        temp_max: Maximum acceptable temperature (e.g., 87.0)
        time_unit: Unit of time in results ("seconds", "minutes", "hours")

    Returns:
        Tuple of (summary_dict, detail_df) where:
        - summary_dict contains: total_duration, time_in_band, time_out_band,
                                 percent_in_band, excursion_count, etc.
        - detail_df contains time series with in_band status for each point
    """
    # Ensure numeric types
    time_values = pd.to_numeric(df[time_col], errors='coerce')
    temp_values = pd.to_numeric(df[temp_col], errors='coerce')

    # Create detail dataframe
    detail_df = pd.DataFrame({
        'Time': time_values,
        'Temperature': temp_values,
    })

    # Calculate if each point is within the band
    detail_df['In_Band'] = (temp_values >= temp_min) & (temp_values <= temp_max)
    detail_df['Status'] = detail_df['In_Band'].apply(lambda x: 'IN BAND' if x else 'OUT OF BAND')

    # Calculate time deltas between consecutive points
    time_deltas = time_values.diff().fillna(0)

    # Handle potential negative time deltas (shouldn't happen, but safety check)
    time_deltas = time_deltas.clip(lower=0)

    detail_df['Time_Delta'] = time_deltas

    # Calculate cumulative time in band
    in_band_mask = detail_df['In_Band']
    time_in_band = time_deltas[in_band_mask].sum()
    time_out_band = time_deltas[~in_band_mask].sum()
    total_duration = time_deltas.sum()

    # If total duration is 0, use time span instead
    if total_duration == 0 and len(time_values) > 1:
        total_duration = time_values.iloc[-1] - time_values.iloc[0]
        # Estimate based on proportion
        n_in_band = in_band_mask.sum()
        n_total = len(in_band_mask)
        if n_total > 0:
            time_in_band = total_duration * (n_in_band / n_total)
            time_out_band = total_duration - time_in_band

    # Count excursions (transitions from in-band to out-of-band)
    in_band_shifted = detail_df['In_Band'].shift(1).fillna(True)
    excursion_starts = (~detail_df['In_Band']) & in_band_shifted
    excursion_count = excursion_starts.sum()

    # Find excursion details (when temperature went out of band)
    excursions = []
    in_excursion = False
    excursion_start_time = None
    excursion_start_idx = None

    for idx, row in detail_df.iterrows():
        if not row['In_Band'] and not in_excursion:
            # Start of excursion
            in_excursion = True
            excursion_start_time = row['Time']
            excursion_start_idx = idx
        elif row['In_Band'] and in_excursion:
            # End of excursion
            in_excursion = False
            excursion_duration = row['Time'] - excursion_start_time

            # Get temperature range during excursion
            excursion_temps = detail_df.loc[excursion_start_idx:idx-1, 'Temperature']

            excursions.append({
                'start_time': excursion_start_time,
                'end_time': row['Time'],
                'duration': excursion_duration,
                'min_temp': excursion_temps.min() if len(excursion_temps) > 0 else None,
                'max_temp': excursion_temps.max() if len(excursion_temps) > 0 else None,
            })

    # Handle case where data ends during an excursion
    if in_excursion and excursion_start_time is not None:
        last_time = detail_df['Time'].iloc[-1]
        excursion_temps = detail_df.loc[excursion_start_idx:, 'Temperature']
        excursions.append({
            'start_time': excursion_start_time,
            'end_time': last_time,
            'duration': last_time - excursion_start_time,
            'min_temp': excursion_temps.min() if len(excursion_temps) > 0 else None,
            'max_temp': excursion_temps.max() if len(excursion_temps) > 0 else None,
        })

    # Calculate statistics
    temp_stats = {
        'min': temp_values.min(),
        'max': temp_values.max(),
        'mean': temp_values.mean(),
        'std': temp_values.std(),
    }

    # Percentage in band
    percent_in_band = (time_in_band / total_duration * 100) if total_duration > 0 else 0

    # Convert time units if needed
    time_divisor = 1.0
    if time_unit == "minutes":
        time_divisor = 60.0
    elif time_unit == "hours":
        time_divisor = 3600.0

    summary = {
        'total_duration': total_duration / time_divisor,
        'time_in_band': time_in_band / time_divisor,
        'time_out_band': time_out_band / time_divisor,
        'percent_in_band': percent_in_band,
        'percent_out_band': 100 - percent_in_band,
        'excursion_count': int(excursion_count),
        'excursions': excursions,
        'temp_band': (temp_min, temp_max),
        'temp_stats': temp_stats,
        'time_unit': time_unit,
        'data_points': len(df),
    }

    return summary, detail_df


def format_duration(seconds: float, time_unit: str = "auto") -> str:
    """
    Format duration in human-readable form.

    Args:
        seconds: Duration in seconds
        time_unit: "auto", "seconds", "minutes", or "hours"

    Returns:
        Formatted string like "22h 15m 30s" or "1345.5 seconds"
    """
    if time_unit == "auto":
        if seconds >= 3600:
            time_unit = "hours"
        elif seconds >= 60:
            time_unit = "minutes"
        else:
            time_unit = "seconds"

    if time_unit == "hours":
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"
    elif time_unit == "minutes":
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        return f"{seconds:.2f}s"


def load_asr_data_from_file(filepath: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load ASR test data from TXT or CSV file.

    Args:
        filepath: Path to data file

    Returns:
        Tuple of (dataframe, column_names)
    """
    # Try to detect delimiter and skip header rows
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Find the header row (row with column names)
    header_row = 0
    for i, line in enumerate(lines):
        # Skip empty lines and common header text
        stripped = line.strip().lower()
        if not stripped:
            continue
        if 'powertech' in stripped or 'time step' in stripped or 'cycle test' in stripped:
            continue
        # Check if line looks like data headers
        if '\t' in line or ',' in line:
            header_row = i
            break

    # Determine delimiter
    delimiter = '\t' if '\t' in lines[header_row] else ','

    # Load data
    df = pd.read_csv(
        filepath,
        sep=delimiter,
        skiprows=header_row,
        encoding='utf-8',
        on_bad_lines='skip'
    )

    return df, list(df.columns)
