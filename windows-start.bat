@echo off
SET VENV_NAME=myenv
SET REQUIREMENTS=flask requests python-magic

:: Check if the virtual environment folder exists
IF EXIST %VENV_NAME% (
    echo Virtual environment '%VENV_NAME%' already exists. Activating...
    call %VENV_NAME%\Scripts\activate
) ELSE (
    echo Creating virtual environment '%VENV_NAME%'...
    python -m venv %VENV_NAME%
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    echo Activating virtual environment...
    call %VENV_NAME%\Scripts\activate
    echo Installing required packages: %REQUIREMENTS%...
    pip install %REQUIREMENTS%
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to install packages.
        pause
        exit /b 1
    )
    echo Virtual environment created and packages installed successfully.
)

echo Virtual environment is now active. Use 'windows-stop.bat' to deactivate.
pause
