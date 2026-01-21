# Data loading and file merging utilities

import os
from typing import List

from powertech_tools.utils.helpers import natural_sort_key


def merge_selected_files(filepaths: List[str], out_path: str) -> str:
    """
    Merge multiple files into a single output file.

    Files are sorted naturally by basename before merging.
    Headers are detected and only written once from the first file.
    Subsequent files have their headers skipped to prevent duplication.

    Args:
        filepaths: List of file paths to merge
        out_path: Path for the merged output file

    Returns:
        The output file path

    Raises:
        RuntimeError: If no files are selected
    """
    if not filepaths:
        raise RuntimeError("No files selected.")
    filepaths = sorted(filepaths, key=lambda p: natural_sort_key(os.path.basename(p)))

    header_line = None

    with open(out_path, "w", encoding="utf-8", errors="ignore") as out:
        for idx, fp in enumerate(filepaths):
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            if not lines:
                continue

            # For the first file, detect and store the header
            if idx == 0:
                # Check if first line looks like a header (contains common header indicators)
                first_line = lines[0].strip()
                if _is_likely_header(first_line):
                    header_line = first_line
                # Write all lines from first file
                out.writelines(lines)
            else:
                # For subsequent files, skip the header if it matches
                start_idx = 0
                if header_line and lines:
                    first_line = lines[0].strip()
                    # Skip first line if it matches the header or looks like a header
                    if first_line == header_line or _is_likely_header(first_line):
                        start_idx = 1

                # Write remaining lines (skipping header)
                if start_idx < len(lines):
                    out.writelines(lines[start_idx:])

            # Ensure proper line breaks between files
            if lines and not lines[-1].endswith("\n"):
                out.write("\n")
            out.write("\n")

    return out_path


def _is_likely_header(line: str) -> bool:
    """
    Determine if a line is likely a header.

    Headers typically contain:
    - Column names with delimiters (tabs, commas, pipes)
    - Common header keywords
    - Multiple capitalized words

    Args:
        line: The line to check

    Returns:
        True if line appears to be a header
    """
    if not line:
        return False

    line_lower = line.lower()

    # Common header indicators
    header_keywords = [
        'time', 'date', 'timestamp', 'name', 'value', 'id', 'type',
        'status', 'level', 'message', 'data', 'temp', 'voltage',
        'current', 'power', 'frequency', 'sample', 'channel'
    ]

    # Check for delimiter patterns (tab, comma, pipe separated)
    has_delimiters = '\t' in line or ',' in line or '|' in line

    # Check if line contains header keywords
    has_keywords = any(keyword in line_lower for keyword in header_keywords)

    # Check for multiple capitalized words (common in headers)
    words = line.split()
    capitalized_count = sum(1 for w in words if w and w[0].isupper())
    has_capitals = capitalized_count >= 2

    # Line is likely a header if it has delimiters + keywords, or multiple capitals
    return (has_delimiters and has_keywords) or has_capitals
