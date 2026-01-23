@echo off
REM Launch Pass-Fail Cleaner GUI
REM This batch file makes it easy to run the program

echo Starting Pass-Fail Cleaner...
echo.

REM Run the GUI script from the scripts subdirectory
python scripts\pass-fail_cleaner_gui.py

if errorlevel 1 (
    echo.
    echo Error: Could not start the program.
    echo.
    echo Make sure Python is installed on your computer.
    echo You can download it from: https://www.python.org/downloads/
    echo.
    pause
)
