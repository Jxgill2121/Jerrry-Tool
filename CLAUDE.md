# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Jerry** is a professional data analysis web application for Powertech featuring:
- File merging and data consolidation
- Max/Min analysis
- Data plotting and visualization
- Cycle averages calculation
- Data validation (including ASR and fuel systems analysis)

Built with **FastAPI** backend and **React** frontend, both running from a single deployment.

## Running the Application

### Development

**API Server** (FastAPI, runs on `http://localhost:8000`)
```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Web Frontend** (React with Vite, runs on `http://localhost:5173`)
```bash
cd frontend
npm install
npm run dev
```

### Production

Both frontend and API are built into a single deployment:
```bash
# Build React app
cd frontend
npm run build

# API serves the built frontend via StaticFiles mount at `/`
# Run: uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Architecture Overview

### Two-Layer Design

**Data Processing Layer** (`powertech_tools/data/`)
- Core business logic: file parsing, data transformation, validation
- No UI dependencies—pure data functions
- `loader.py` - File reading and merging (CSV, Excel, TDMS formats)
- `processor.py` - Data transformations (Max/Min, averages, ramp analysis)
- `validator.py` - Data validation against specification limits
- `asr_validator.py` - Advanced ASR validation
- `fuel_systems_validator.py` - Fuel systems analysis
- `tdms_converter.py` - TDMS file conversion

**API Layer** (`api/`)
- FastAPI endpoints exposing data layer functions via HTTP
- Routes organized by feature:
  - `routers/merge.py` - File merging (`POST /api/merge`)
  - `routers/maxmin.py` - Max/Min analysis (`POST /api/maxmin`)
  - `routers/avg.py` - Cycle averages (`POST /api/avg`)
  - `routers/plot.py` - Plotting/graphing (`POST /api/plot`)
  - `routers/validation.py` - Data validation (`POST /api/validate`)
  - `routers/asr.py` - ASR validation (`POST /api/asr`)
  - `routers/fuel_systems.py` - Fuel analysis (`POST /api/fuel-systems`)
  - `routers/cycle_viewer.py` - Cycle visualization (`POST /api/cycle-viewer`)
- Serves built React frontend as static files at `/`

**Frontend Layer** (`frontend/`)
- React + TypeScript with Vite build tool
- Tailwind CSS for styling
- Axios for API calls
- Plotly.js for data visualization
- react-dropzone for file uploads

### Data Flow

**User uploads file** → 
- React component sends `POST /api/merge` with file
- `routers/merge.py` calls `loader.merge_selected_files()`
- Returns merged data as JSON
- Frontend displays in table

**User analyzes data** →
- React component calls API endpoint (e.g., `POST /api/maxmin`)
- Router calls corresponding processor function (e.g., `processor.compute_maxmin_template()`)
- Returns Plotly JSON for graphs or DataFrame as JSON for tables
- Frontend renders with Plotly.js or data table

## Adding New Features

### Adding a New Analysis Feature

1. **Add processing logic** to `powertech_tools/data/processor.py` or new validation file
   - Function takes processed data (pandas DataFrame) and returns results
   - Keep it pure—no API/UI concerns

2. **Add REST API endpoint**
   - Create new router in `api/routers/` (e.g., `export.py`)
   - Implement endpoint that accepts file upload and calls your processor function
   - Import and include router in `api/main.py` via `app.include_router()`

3. **Add to React Frontend**
   - Create React component in `frontend/src/`
   - Implement file upload + API call using axios
   - Add navigation/section to main layout
   - Use Plotly for graphs or HTML tables for data

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

**Data Processing & API:**
- `pandas` - Data manipulation
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload handling
- `plotly` - Graph generation
- `kaleido` - Graph export
- `openpyxl`, `npTDMS` - File format support
- `numpy` - Numerical operations
- `pillow` - Image handling

**Web Frontend:**
- `react`, `react-dom` - UI framework
- `vite` - Build tool
- `tailwindcss` - CSS framework
- `axios` - HTTP client
- `plotly.js` - Graph visualization
- `react-dropzone` - File upload UI

## Development Tips

- **Data processing changes** only affect API—no GUI to rebuild
- **API responses** are typically Plotly JSON for graphs or pandas DataFrames as JSON
- **Frontend builds** with `npm run build` and API serves from `public/` directory
- **File uploads** validated in both API layer and individual routers
- **Logs** written to `logs/jerry.log` with rotation at 10MB
- **CORS** enabled for all origins in development; restrict in production
