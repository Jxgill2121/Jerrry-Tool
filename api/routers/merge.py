"""
TDMS to Cycle Files router
"""

import io
import os
import tempfile
import zipfile
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from api.utils import save_uploads, zip_response
from powertech_tools.data.tdms_converter import read_tdms_structure, convert_tdms_files_to_cycles

router = APIRouter()


@router.post("/structure")
async def get_structure(files: List[UploadFile] = File(...)):
    """Upload TDMS files and return their group/channel structure."""
    tmpdir = tempfile.mkdtemp(prefix="jerry_merge_")
    try:
        paths = await save_uploads(files, tmpdir)
        if not paths:
            raise HTTPException(400, "No files uploaded")

        groups, channels = read_tdms_structure(paths[0])
        return {
            "file_count": len(paths),
            "filenames": [os.path.basename(p) for p in paths],
            "groups": groups,
            "channels": channels,
            "session_tmpdir": tmpdir,
            "session_paths": paths,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/convert")
async def convert(
    files: List[UploadFile] = File(...),
    group_name: str = Form(...),
    selected_channels: str = Form(...),   # JSON array string
    add_time_column: bool = Form(True),
    time_step: float = Form(0.10),
    add_datetime_column: bool = Form(True),
):
    """Convert TDMS files to cycle TXT files and return as ZIP."""
    import json

    tmpdir = tempfile.mkdtemp(prefix="jerry_merge_")
    out_dir = os.path.join(tmpdir, "cycles")
    os.makedirs(out_dir, exist_ok=True)

    try:
        paths = await save_uploads(files, tmpdir)
        channels = json.loads(selected_channels)

        created = convert_tdms_files_to_cycles(
            filepaths=paths,
            output_dir=out_dir,
            group_name=group_name,
            selected_channels=channels,
            add_time_column=add_time_column,
            time_step=time_step,
            add_datetime_column=add_datetime_column,
        )

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in created:
                zf.write(fp, os.path.basename(fp))

        return zip_response(buf, "cycle_files.zip")

    except Exception as e:
        raise HTTPException(500, str(e))
