# TDMS file conversion utilities

import os
from typing import List, Tuple, Dict, Optional
import pandas as pd
from nptdms import TdmsFile


def read_tdms_structure(filepath: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Read TDMS file structure and return groups and channels.

    Args:
        filepath: Path to TDMS file

    Returns:
        Tuple of (group_names, channel_dict) where channel_dict maps group -> list of channel names
    """
    tdms_file = TdmsFile.read(filepath)

    groups = []
    channels_dict = {}

    for group in tdms_file.groups():
        group_name = group.name
        groups.append(group_name)
        channels_dict[group_name] = [channel.name for channel in group.channels()]

    return groups, channels_dict


def get_cycle_column_values(filepath: str, group_name: str, cycle_channel: str) -> List:
    """
    Get unique cycle values from a cycle indicator channel.

    Args:
        filepath: Path to TDMS file
        group_name: Name of the group containing the cycle channel
        cycle_channel: Name of the channel that indicates cycle number

    Returns:
        Sorted list of unique cycle values
    """
    tdms_file = TdmsFile.read(filepath)
    group = tdms_file[group_name]
    channel = group[cycle_channel]
    data = channel[:]

    import numpy as np
    unique_cycles = sorted(np.unique(data))
    return unique_cycles


def convert_tdms_to_cycle_files(
    filepath: str,
    output_dir: str,
    group_name: str,
    cycle_channel: Optional[str] = None,
    time_channel: Optional[str] = None,
    progress_callback=None
) -> List[str]:
    """
    Convert TDMS file to individual cycle TXT files.

    Args:
        filepath: Path to TDMS file
        output_dir: Directory to save cycle TXT files
        group_name: Name of the group to extract data from
        cycle_channel: Name of channel that indicates cycle number (if None, treat whole file as one cycle)
        time_channel: Name of time/timestamp channel (optional)
        progress_callback: Optional callback function(current, total, message)

    Returns:
        List of created file paths
    """
    tdms_file = TdmsFile.read(filepath)
    group = tdms_file[group_name]

    # Get all channel names and data
    channel_names = [ch.name for ch in group.channels()]

    if not channel_names:
        raise RuntimeError(f"No channels found in group '{group_name}'")

    # Read all data into a DataFrame
    data_dict = {}
    for ch_name in channel_names:
        channel = group[ch_name]
        data_dict[ch_name] = channel[:]

    df = pd.DataFrame(data_dict)

    # Determine output file prefix
    base_name = os.path.splitext(os.path.basename(filepath))[0]

    created_files = []

    if cycle_channel and cycle_channel in df.columns:
        # Split by cycle column
        unique_cycles = sorted(df[cycle_channel].unique())
        total_cycles = len(unique_cycles)

        for idx, cycle_val in enumerate(unique_cycles, start=1):
            if progress_callback:
                progress_callback(idx, total_cycles, f"Processing cycle {int(cycle_val)}")

            cycle_df = df[df[cycle_channel] == cycle_val].copy()

            # Reorder columns: time first if specified, then others, cycle column last
            cols = list(cycle_df.columns)
            ordered_cols = []

            if time_channel and time_channel in cols:
                ordered_cols.append(time_channel)
                cols.remove(time_channel)

            # Add other columns except cycle column
            for col in cols:
                if col != cycle_channel:
                    ordered_cols.append(col)

            # Add cycle column at end
            ordered_cols.append(cycle_channel)

            cycle_df = cycle_df[ordered_cols]

            # Create output file
            out_filename = f"{base_name}_cycle{int(cycle_val)}.txt"
            out_path = os.path.join(output_dir, out_filename)

            # Write with Powertech header format
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("Powertech Test Log\n")
                f.write("Time step =0.10 s\n")
                f.write("\n")
                f.write("Cycle test\n")
                f.write("\t".join(ordered_cols) + "\n")
                cycle_df.to_csv(f, sep="\t", index=False, header=False, lineterminator="\n")

            created_files.append(out_path)

    else:
        # No cycle column - treat entire file as one cycle
        if progress_callback:
            progress_callback(1, 1, "Processing single cycle")

        # Reorder columns: time first if specified
        cols = list(df.columns)
        if time_channel and time_channel in cols:
            cols.remove(time_channel)
            cols.insert(0, time_channel)

        out_filename = f"{base_name}_cycle1.txt"
        out_path = os.path.join(output_dir, out_filename)

        # Write with Powertech header format
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("Powertech Test Log\n")
            f.write("Time step =0.10 s\n")
            f.write("\n")
            f.write("Cycle test\n")
            f.write("\t".join(cols) + "\n")
            df[cols].to_csv(f, sep="\t", index=False, header=False, lineterminator="\n")

        created_files.append(out_path)

    return created_files
