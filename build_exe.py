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
        sys.executable,  # Use the same Python interpreter
        "-m",
        "PyInstaller",
        "--name=JERRY-Powertech-Tools",
        "--windowed",  # No console window
        "--onefile",   # Single executable file
    ]
    
    # Add icon if it exists
    if os.path.exists("powertech_tools/assets/icon.ico"):
        cmd.append("--icon=powertech_tools/assets/icon.ico")

    # Hidden imports (in case PyInstaller misses them)
    cmd.extend([
        "--hidden-import=nptdms",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=matplotlib",
        "--hidden-import=PIL",
    ])

    # Include data files
    cmd.append("--add-data=powertech_tools;powertech_tools")

    # Main entry point
    cmd.append("main.py")

    print("Building executable...")
    print(" ".join(cmd))
    print()

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("\n✓ Build complete! Executable is in the 'dist' folder")
        print("  Location: dist/JERRY-Powertech-Tools.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed!")
        print(f"Error output:\n{e.stderr}")
        print(f"Standard output:\n{e.stdout}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ PyInstaller module not found!")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    # Check if main.py exists
    if not os.path.exists("main.py"):
        print("✗ Error: main.py not found in current directory!")
        print(f"Current directory: {os.getcwd()}")
        sys.exit(1)
    
    build_executable()