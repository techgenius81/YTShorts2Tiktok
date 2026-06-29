@echo off

python -m pip install -r requirements.txt

echo.
<nul set /p="Do you want to launch the tool? ("
<nul set /p="[92mY[0m"
<nul set /p="/"
<nul set /p="[91mN[0m"
<nul set /p="): "

choice /c YN /n

if errorlevel 2 exit
if errorlevel 1 call run.bat