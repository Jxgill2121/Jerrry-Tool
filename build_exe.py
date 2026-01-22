"""
Build script for creating Windows executable using PyInstaller
Run: python build_exe.py
"""

import os
import sys
import subprocess

def build_executable():
    """Build the executable with PyInstaller"""

    # PyInstaller command with all necessary options
    cmd = [
        "pyinstaller",
        "--name=JERRY-Powertech-Tools",
        "--windowed",  # No console window
        "--onefile",   # Single executable file
        "--icon=powertech_tools/assets/icon.ico" if os.path.exists("powertech_tools/assets/icon.ico") else "",

        # Hidden imports (in case PyInstaller misses them)
        "--hidden-import=nptdms",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=matplotlib",
        "--hidden-import=PIL",

        # Include data files
        "--add-data=powertech_tools;powertech_tools",

        # Main entry point
        "main.py"
    ]

    # Remove empty strings from command
    cmd = [c for c in cmd if c]

    print("Building executable...")
    print(" ".join(cmd))
    print()

    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Build complete! Executable is in the 'dist' folder")
        print("  Location: dist/JERRY-Powertech-Tools.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ PyInstaller not found!")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
