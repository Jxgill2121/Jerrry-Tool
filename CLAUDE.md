# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Jerry** is a professional data analysis tool for Powertech with three client interfaces sharing a common backend:

1. **Desktop GUI** (`powertech_tools/`) - tkinter-based desktop application with tabbed interface
2. **REST API** (`api/`) - FastAPI backend with HTTP endpoints
3. **Web Frontend** (`frontend/`) - React + TypeScript web UI with Vite

All three interfaces share the same data processing logic in `powertech_tools/data/`.

## Running the Application

### Desktop GUI (tkinter)
```bash
# Main entry point - launches the Desktop GUI application
# (No main.py at root; run via Python module discovery)
python -m powertech_tools.app
```

### REST API Server
```bash
# Start FastAPI development server
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### React Web Frontend
```bash
# Start Vite dev server (runs on http://localhost:5173)
cd frontend
npm install
npm run dev

# Build for production
npm run build
```

## Architecture Overview

### Three-Layer Design

**Data Processing Layer** (`powertech_tools/data/`)
- Core business logic: file parsing, data transformation, validation
- Used by all three frontends (no UI dependencies)
- `loader.py` - File reading and merging (CSV, Excel, TDMS formats)
- `processor.py` - Data transformations (Max/Min, averages, ramp analysis)
- `validator.py` - Data validation against specification limits
- `asr_validator.py` - Advanced ASR validation
- `fuel_systems_validator.py` - Fuel systems analysis
- `tdms_converter.py` - TDMS file conversion

**Desktop GUI Layer** (`powertech_tools/`)
- tkinter-based interface organized by category tabs
- Categories: "File Conversion", "Report Graphs", "Validation"
- Each tab has a corresponding builder function (e.g., `build_merge_tab()`)
- `app.py` - Main application window, category switching, notebook management

**API Layer** (`api/`)
- FastAPI endpoints that expose data layer functions via HTTP
- Routers mirror GUI functionality:
  - `routers/merge.py` - File merging
  - `routers/maxmin.py` - Max/Min analysis
  - `routers/avg.py` - Cycle averages
  - `routers/plot.py` - Plotting/graphing
  - `routers/validation.py`, `asr.py`, `fuel_systems.py` - Validation
  - `routers/cycle_viewer.py` - Cycle visualization

**Web Frontend** (`frontend/`)
- React + TypeScript with Vite build tool
- Tailwind CSS for styling
- Axios for API calls
- Plotly.js for data visualization
- react-dropzone for file uploads

### Category Organization

The GUI and API organize features by category:
1. **File Conversion** - TDMS conversion, MaxMin conversion, cycle averages
2. **Report Graphs** - MaxMin grapher, cycle plotter
3. **Validation** - Data validation, ASR validation, fuel systems

### File References and Data Flow

**User uploads file** → 
- **Desktop GUI**: `merge_tab.py` calls `loader.merge_selected_files()` → displays in tab
- **API**: `/api/merge` endpoint receives file → `routers/merge.py` calls same `loader.merge_selected_files()` → returns JSON
- **Web UI**: React component calls `/api/merge` → processes response → renders

**User analyzes data** →
- **Desktop GUI**: `plot_tab.py` calls `processor.compute_maxmin_template()` → displays matplotlib/tkinter canvas
- **API**: `/api/maxmin` endpoint → `routers/maxmin.py` → calls processor → returns plotly JSON
- **Web UI**: React component calls `/api/maxmin` → receives plotly JSON → renders with plotly.js

## Configuration and Theming

Theme management is centralized in `powertech_tools/config/theme.py`:
- `PowertechTheme` class defines all colors, fonts, and styling
- To change theme: edit colors in `PowertechTheme`
- To add company logo: edit `POWERTECH_LOGO_BASE64`

GUI theme is applied in `app.py` via `apply_powertech_theme(self)`

## Adding New Features

### Adding a New Analysis Feature

1. **Add processing logic** to `powertech_tools/data/processor.py`
   - Implement your analysis function
   - Function should take processed data (pandas DataFrame) and return results

2. **Add to Desktop GUI**
   - Create new tab file in `powertech_tools/tabs/` (e.g., `export_tab.py`)
   - Implement `build_export_tab(parent, app)` function
   - Import in `powertech_tools/tabs/__init__.py`
   - Add to appropriate category notebook in `app.py` under `_create_all_notebooks()`

3. **Add to REST API**
   - Create new router file in `api/routers/` (e.g., `export.py`)
   - Implement endpoint that calls your processor function
   - Import and include router in `api/main.py` via `app.include_router()`

4. **Add to Web Frontend**
   - Create React component in `frontend/src/` 
   - Implement file upload + API call to new endpoint
   - Add navigation/tab to main layout

## Utility Modules

**`powertech_tools/utils/helpers.py`**
- `natural_sort_key()` - Sorting with numeric awareness
- `safe_float()`, `safe_int()` - Type conversions with defaults
- `make_unique_names()` - Handling duplicate column names

**`powertech_tools/utils/file_parser.py`**
- `load_table_allow_duplicate_headers()` - Load CSV/Excel with duplicate headers
- `read_headers_only()` - Extract header row without full parse
- `detect_delimiter()` - Auto-detect CSV delimiter

## Dependencies

**GUI & Data Processing:**
- `pandas` - Data manipulation
- `matplotlib` - Plotting (GUI)
- `pillow` - Image handling
- `tkinter` - GUI framework (usually built-in)
- `openpyxl`, `npTDMS` - File format support

**API Server:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload handling
- `plotly` - Interactive graphing
- `kaleido` - Graph export

**Web Frontend:**
- `react`, `react-dom` - UI framework
- `vite` - Build tool
- `tailwindcss` - CSS framework
- `axios` - HTTP client
- `plotly.js` - Graphing library

## Development Tips

- **Data processing changes** affect all three frontends - test thoroughly
- **API responses** are typically Plotly JSON objects for graphs or pandas-serialized DataFrames
- **File uploads** are handled by both `/api/merge` and individual validation endpoints
- **Frontend builds** with `npm run build` and API serves static files via `StaticFiles` mount
- Logs are written to `logs/jerry.log` with rotation at 10MB
