#!/usr/bin/env python3
"""
JERRY - Powertech Analysis Tools
Main entry point for the application

VERSION: 2026-01-16 v4.4 - Modular Architecture
Powertech – One Stop Tools (Surrey, BC)
"""

from powertech_tools.app import PowertechToolsApp


def main():
    """Launch the Powertech Tools application"""
    app = PowertechToolsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
