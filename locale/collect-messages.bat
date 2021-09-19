REM echo off
%~d0
cd %~p0
del /F MediaFiler.pot.old
ren MediaFiler.pot MediaFiler.pot.old
"C:\Program Files\Python\3.8\Tools\i18n\pygettext.py" -k N_ -o MediaFiler.pot ..\*.pyw ..\*.py ..\UI\*.py ..\Model\*.py ..\Model\MediaOrganization\*.py
C:\OpenSourcePrograms\Poedit\Poedit.exe
pause
