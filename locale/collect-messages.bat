echo off
del /F locale\MediaFiler.pot.old
ren locale\MediaFiler.pot MediaFiler.pot.old
"c:\Program Files\Python\2.7\Tools\i18n\pygettext.py" -k N_ -o locale\MediaFiler.pot *.py UI\*.py Model\*.py
