REM echo off
%~d0
cd %~p0
del /F MediaFiler.pot.old
ren MediaFiler.pot MediaFiler.pot.old
"c:\Program Files\Python\2.7\Tools\i18n\pygettext.py" -k N_ -o MediaFiler.pot ..\*.pyw ..\*.py ..\UI\*.py ..\Model\*.py ..\Model\MediaOrganization\*.py
poedit
pause
