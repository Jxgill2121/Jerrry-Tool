# Data loading and file merging utilities

import os
from typing import List

from powertech_tools.utils.helpers import natural_sort_key


def merge_selected_files(filepaths: List[str], out_path: str) -> str:
    """
    Merge multiple files into a single output file.

    Files are sorted naturally by basename before merging.
    Each file's content is written to the output, ensuring proper line breaks.

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

    with open(out_path, "w", encoding="utf-8", errors="ignore") as out:
        for fp in filepaths:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("\n")
    return out_path
