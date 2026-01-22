# Building JERRY Powertech Tools as an Executable

This guide explains how to build the application as a standalone Windows executable (.exe) that includes all dependencies (including npTDMS).

## Prerequisites

1. **Python 3.11 or higher** installed
2. **All dependencies installed**:
   ```powershell
   pip install -r requirements.txt
   ```

## Building the Executable

### Option 1: Using the Build Script (Recommended)

Simply run:
```powershell
python build_exe.py
```

The executable will be created in the `dist` folder as `JERRY-Powertech-Tools.exe`

### Option 2: Using the Spec File

If you want more control, use the PyInstaller spec file:
```powershell
pyinstaller JERRY-Powertech-Tools.spec
```

### Option 3: Manual PyInstaller Command

```powershell
pyinstaller --name=JERRY-Powertech-Tools --windowed --onefile --hidden-import=nptdms --hidden-import=pandas --hidden-import=numpy --add-data="powertech_tools;powertech_tools" main.py
```

## What Gets Bundled?

The executable will include:
- ✅ Python interpreter
- ✅ All Python libraries (pandas, numpy, matplotlib, PIL, **npTDMS**)
- ✅ Your application code
- ✅ All dependencies

The resulting `.exe` file can be distributed to any Windows computer **without requiring Python or any libraries to be installed**.

## Distribution

Once built, you can distribute just the `.exe` file to users. They can:
1. Double-click `JERRY-Powertech-Tools.exe` to run the application
2. No Python installation needed
3. No pip install needed
4. Everything is bundled inside!

## File Size

The executable will be approximately:
- **Single-file EXE**: ~100-200 MB (includes Python + all libraries)
- **Directory mode**: ~150 MB (split into multiple files)

## Testing the Executable

After building:
1. Navigate to the `dist` folder
2. Double-click `JERRY-Powertech-Tools.exe`
3. The application should launch with all functionality working

## Troubleshooting

### Missing Module Errors
If you get "ModuleNotFoundError" when running the exe, add the missing module to the `hiddenimports` list in `JERRY-Powertech-Tools.spec`:
```python
hiddenimports=[
    'nptdms',
    'your_missing_module_here',
],
```

### DLL Errors
If you get DLL errors on other computers, try building with:
```powershell
pyinstaller --onedir JERRY-Powertech-Tools.spec
```
This creates a folder with the exe and all DLLs, instead of a single file.

## Notes

- The first launch of the built exe may be slow (a few seconds) as PyInstaller extracts files
- Subsequent launches will be faster
- Antivirus software may flag PyInstaller executables - this is a false positive
- The exe will work on Windows 10/11 without any dependencies
