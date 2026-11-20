@echo off
cd /d "%~dp0"
py -3 run_simulator.py
if errorlevel 1 (
  echo Install Python 3 with Tcl/Tk support, then try again.
  pause
)
