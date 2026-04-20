=======================================================
 JERRY - Powertech Analysis Tools  |  Server Deployment
=======================================================

FIRST-TIME SETUP (run once as Administrator)
--------------------------------------------
1. Install Git, Python 3.11+, Node.js 18+ on the server
2. Clone the repo:
     git clone https://github.com/Jxgill2121/Jerrry-Tool.git
     cd Jerrry-Tool
     git checkout claude/convert-to-webapp-BR383

3. Create Python environment and install dependencies:
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r api/requirements-api.txt

4. Build the frontend:
     cd frontend
     npm install
     npm run build
     cd ..

5. Download NSSM from https://nssm.cc/download
   Place nssm.exe in C:\Windows\System32\ (or any folder on PATH)

6. Run the installer (as Administrator):
     deploy\1_install.bat

Jerry will now run on http://<server-ip>:8000 and restart
automatically when the server reboots.


DAY-TO-DAY MANAGEMENT
----------------------
Open a command prompt in the repo folder and use:

  deploy\2_manage.bat status    <- Is it running? Any errors?
  deploy\2_manage.bat logs      <- Watch live logs
  deploy\2_manage.bat errors    <- Watch error logs
  deploy\2_manage.bat restart   <- Restart after config change
  deploy\2_manage.bat update    <- Pull new code + rebuild + restart

Health check URL (open in browser):
  http://localhost:8000/api/health


LOGS LOCATION
-------------
  logs\jerry.log          <- All output (rotates at 10 MB, keeps 3 files)
  logs\jerry-error.log    <- Errors only (from NSSM stderr capture)


TROUBLESHOOTING
---------------
- "Service not found"  → Run 1_install.bat as Administrator first
- App loads but API errors → check logs\jerry-error.log
- Port 8000 in use → edit PORT= in 1_install.bat, then reinstall
- Code changes not showing → run: manage.bat update
