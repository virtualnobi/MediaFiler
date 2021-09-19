# This allows modules in the package to access the directory they were loaded from
PackagePath = __path__[0]

# Specifies that all locale categories shall use user-preferred settings
import locale
locale.setlocale(locale.LC_ALL, '')
