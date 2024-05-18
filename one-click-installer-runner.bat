@echo off
SET venv_dir=venv
SET pyfile=setup.py
SET python=%venv_dir%\Scripts\python.exe

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
    
    REM Check if the specified pyfile exists, if not, find the first .py file except __init__.py
    IF NOT EXIST "%pyfile%" (
        FOR /F "delims=" %%i IN ('DIR *.py /B /A:-D /O:N 2^>nul') DO (
            IF NOT "%%i" == "__init__.py" (
                SET "pyfile=%%i"
                GOTO FoundPyFile
            )
        )
        ECHO No suitable Python file found. Exiting...
        GOTO End
    )
    
    :FoundPyFile
    REM Run the Python script
) ELSE (
    ECHO Failed to activate virtual environment.
)

aTrain start        
:End
REM Pause the command window
cmd /k 