@echo off
setlocal
cd /d "%~dp0"
rem Prefer the Windows Python launcher so a WindowsApps Store alias is never mistaken for Python.
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
  if not defined PYTHON_CMD (
    py -3.11 -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
  )
)
rem Without py.exe, search python.exe candidates and ignore the Microsoft Store execution alias.
if not defined PYTHON_CMD (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    echo %%P | findstr /i /c:"\WindowsApps" >nul
    if errorlevel 1 (
      "%%P" -c "import sys; assert sys.version_info[:2] in ((3,12),(3,11))" >nul 2>nul
      if not errorlevel 1 set "PYTHON_CMD="%%P""
    )
  )
)
if not defined PYTHON_CMD (
  for /f "delims=" %%P in ('where python3 2^>nul') do (
    echo %%P | findstr /i /c:"\WindowsApps" >nul
    if errorlevel 1 (
      "%%P" -c "import sys; assert sys.version_info[:2] in ((3,12),(3,11))" >nul 2>nul
      if not errorlevel 1 set "PYTHON_CMD="%%P""
    )
  )
)
if not defined PYTHON_CMD (
  echo Python 3.12 or 3.11 was not found. The WindowsApps alias is not a Python installation.
  echo Install Python 3.12 64-bit from https://www.python.org/downloads/windows/ and enable the py launcher.
  pause
  exit /b 1
)
echo Using %PYTHON_CMD%
set "VENV_DIR=.venv"
set "REBUILD_VENV=0"
if not exist .venv\Scripts\python.exe set "REBUILD_VENV=1"
if not exist .venv\pyvenv.cfg set "REBUILD_VENV=1"
if exist .venv\pyvenv.cfg (
  rem Read pyvenv.cfg with the selected interpreter. Calling a quoted venv executable
  rem inside FOR /F causes CMD to split the quoted path and falsely report a mismatch.
  %PYTHON_CMD% -c "import os,sys,pathlib; p=pathlib.Path('.venv/pyvenv.cfg'); h=next((x.split('=',1)[1].strip() for x in p.read_text().splitlines() if x.strip().startswith('home')), ''); raise SystemExit(0 if os.path.normcase(os.path.abspath(h))==os.path.normcase(os.path.abspath(sys.base_prefix)) else 1)"
  if errorlevel 1 set "REBUILD_VENV=1"
)
if "%REBUILD_VENV%"=="0" (
  ".venv\Scripts\python.exe" -c "import chromadb, sentence_transformers, streamlit, pymupdf, pytest" >nul 2>nul
  if errorlevel 1 (
    echo Existing virtual environment is incomplete; preparing a staged replacement.
    set "REBUILD_VENV=1"
  )
)
if "%REBUILD_VENV%"=="1" (
  set "VENV_DIR=.venv.rebuild"
  if exist .venv.rebuild\Scripts\python.exe (
    %PYTHON_CMD% -c "import os,sys,pathlib; p=pathlib.Path('.venv.rebuild/pyvenv.cfg'); h=next((x.split('=',1)[1].strip() for x in p.read_text().splitlines() if x.strip().startswith('home')), ''); raise SystemExit(0 if os.path.normcase(os.path.abspath(h))==os.path.normcase(os.path.abspath(sys.base_prefix)) else 1)"
    if errorlevel 1 (
      echo .venv.rebuild belongs to another Python installation and will not be overwritten.
      echo Close processes using it, then remove only .venv.rebuild and run this script again.
      exit /b 1
    )
    echo Resuming the staged virtual environment for %PYTHON_CMD%.
  ) else (
    if exist .venv.rebuild\NUL (
      echo A partial .venv.rebuild folder exists and will not be deleted automatically.
      echo Close Python or Streamlit processes using it, then remove only .venv.rebuild and run this script again.
      exit /b 1
    )
    echo Creating a staged virtual environment with %PYTHON_CMD%...
    %PYTHON_CMD% -m venv .venv.rebuild
    if errorlevel 1 exit /b 1
  )
) else (
  echo Using the existing virtual environment.
)
echo Installing or updating Python dependencies. First install may take several minutes.
%VENV_DIR%\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
%VENV_DIR%\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo Checking educational sample PDFs...
%VENV_DIR%\Scripts\python.exe scripts\generate_samples.py
if errorlevel 1 exit /b 1
if "%REBUILD_VENV%"=="1" (
  if exist .venv.previous\NUL (
    echo .venv.previous already exists; refusing to overwrite this recovery copy.
    echo Move or rename .venv.previous manually after verifying its contents, then rerun.
    exit /b 1
  )
  if exist .venv\NUL (
    echo Preserving the current environment as .venv.previous...
    move .venv .venv.previous >nul
    if errorlevel 1 (
      echo Could not move the current .venv. It may be in use or contain a locked .pyd file.
      echo Close Streamlit, project terminals, IDE Python kernels, and Python processes using this folder.
      echo The current .venv and staged .venv.rebuild were left in place. Rerun .\run.bat after closing them.
      exit /b 1
    )
  )
  move .venv.rebuild .venv >nul
  if errorlevel 1 (
    echo Could not activate .venv.rebuild. Attempting to restore the previous environment once.
    if exist .venv.previous\pyvenv.cfg move .venv.previous .venv >nul
    echo Inspect .venv and .venv.rebuild before retrying; no files outside these environments were changed.
    exit /b 1
  )
  set "VENV_DIR=.venv"
)
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama not detected. Streamlit will run with offline retrieval fallback.
  echo Optional: install Ollama, review model size in README, then run ollama pull llama3.2:3b.
) else (
  echo Ollama command found. The app will check the local service and model status.
)
echo Starting ForensicLLM-inspired demo...
%VENV_DIR%\Scripts\python.exe -m streamlit run app.py
exit /b %errorlevel%
