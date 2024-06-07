@echo off
SET venv_dir=venv
SET pyfile=setup.py
SET python=%venv_dir%\Scripts\python.exe

REM The first time you run this script it will take ~5 minutes to download all required files. 
REM Launching the application in the future will be done explicitly from this file. (step2)
REM Check if the virtual environment directory exists
IF EXIST "%venv_dir%\Scripts\activate.bat" (
    ECHO Virtual environment found. Activating...
    CALL %venv_dir%\Scripts\activate.bat
) ELSE (
    ECHO Creating virtual environment...
    python -m venv %venv_dir%
    CALL %venv_dir%\Scripts\activate.bat
)

REM Check if the virtual environment is activated
IF NOT "%VIRTUAL_ENV%" == "" (
    ECHO Virtual environment activated.
    ECHO Installing dependencies...
    %python% -m pip install --upgrade pip
    %python% -m pip install aTrain@git+https://github.com/JuergenFleiss/aTrain.git --extra-index-url https://download.pytorch.org/whl/cu118

    ECHO Dependencies installed. 
    :FoundPyFile
    REM Run the Python script
) ELSE (
    ECHO Failed to activate virtual environment.
)

:End
aTrain start        
REM Pause the command window
cmd /k 