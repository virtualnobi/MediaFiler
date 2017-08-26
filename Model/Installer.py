# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import os.path
import shutil
import gettext
## Contributed
import wx
## nobi
from nobi import SecureConfigParser
## Project
import GlobalConfigurationOptions
from Entry import Entry
from MediaClassHandler import MediaClassHandler
import UI
from UI import GUIId



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
    print(e)
    def _(message): return message
else:
    _ = Translation.ugettext
def N_(message): return message



# Constants
InstallationPath = os.path.normpath(os.path.join(os.path.split(__file__)[0], '..')) 
CurrentPath = None
ImageFolder = u'images'
LibraryFolder = u'lib'
LogoFilename = u'Logo.ico'
ClassFilename = u'classes.txt'
ConfigurationFilename = (u'%s.ini' % GUIId.AppTitle)
NamesFilename = u'names.orig'
InitialFilename = u'initial.jpg'
LogFilename = u'log-%d.txt'
TrashFolder = u'trash'
ImportFolder = u'import'



def getImagePath():
    """Return the path to the image directory.
    """
    return(os.path.join(CurrentPath, ImageFolder))


def getLibraryPath():
    """Return the path to the library directory.
    """
    return(os.path.join(CurrentPath, LibraryFolder))


def getLogoPath():
    """Return the path to the logo icon.
    """
    return(os.path.join(getLibraryPath(), LogoFilename))


def getClassFilePath():
    """Return the path to the class definition file.
    """
    return(os.path.join(getLibraryPath(), ClassFilename))


def getConfigurationFilePath():
    """Return the path to the configuration (.INI) file.
    """
    return(os.path.join(getLibraryPath(), ConfigurationFilename))


def getNamesFilePath():
    """Return the path to the name list.
    """
    return(os.path.join(getLibraryPath(), NamesFilename))


def getInitialFilePath():
    """Return the path to the initial image to display on startup.
    """
    return(os.path.join(getLibraryPath(), InitialFilename))


def getLogFilePath():
    """Return the path to the log file. 
    
    Path includes a %d specifier to be replaced by the log number.
    """
    return(os.path.join(getLibraryPath(), LogFilename))


def getTrashPath():
    """Return the path to the trash directory.
    """
    return(os.path.join(CurrentPath, TrashFolder))


def getImportFolder():
    """Return the path to the default import directory.
    """
    return(os.path.join(CurrentPath, ImportFolder))


def checkInstallation():
    """Determine whether the specified path contains all required files.

    Returns Boolean indicating whether the installation is ok
    """
    print('Checking "%s"...' % CurrentPath)
    if (not os.path.isdir(getImagePath())):
        print('Image directory missing')
        return(False)
    if (not os.path.isdir(getLibraryPath())):
        return(False)
    if (not os.path.exists(getLogoPath())):
        return(False)
    if (not os.path.exists(getConfigurationFilePath())):
        return(False)
    for c in Entry.ProductTrader.getClasses():
        if (not os.path.exists(os.path.join(getLibraryPath(), c.PreviewImageFilename))):
            print('No preview image for class %s exists.' % c)
            return(False)
    if (not os.path.exists(getClassFilePath())):
        return(False)
    if (not os.path.isdir(getTrashPath())):
        return(False)
    print('Check passed')
    return(True)


def install():
    """Create required paths and files in global CurrentPath, keeping all existing settings.

    Return Boolean indicating installation succeeded
    """
    print('Installing MediaFiler at "%s"' % CurrentPath)
    try:
        if (not os.path.isdir(getImagePath())):
            os.makedirs(getImagePath())
        if (not os.path.isdir(getLibraryPath())):
            os.makedirs(getLibraryPath())
        if (not os.path.exists(getLogoPath())):
            shutil.copyfile(os.path.join(InstallationPath, ImageFolder, LogoFilename), 
                            getLogoPath())
        if (not os.path.exists(getConfigurationFilePath())):
            config = SecureConfigParser(getConfigurationFilePath())
            config.add_section(GUIId.AppTitle)
            config.set(GUIId.AppTitle, 
                       GlobalConfigurationOptions.TextEditor, 
                       ('notepad /W "%s"' % GlobalConfigurationOptions.Parameter))
        for c in Entry.ProductTrader.getClasses():
            if (not os.path.exists(os.path.join(getLibraryPath(), c.PreviewImageFilename))):
                shutil.copyfile(os.path.join(InstallationPath, ImageFolder, c.PreviewImageFilename),
                                os.path.join(getLibraryPath(), c.PreviewImageFilename))
        if (not os.path.exists(getClassFilePath())):
            with open(getClassFilePath(), 'w') as cfile:
                cfile.write(MediaClassHandler.InitialFileContent)
        if (not os.path.isdir(getTrashPath())):
            os.makedirs(getTrashPath())
        if (not os.path.isdir(getImportFolder())):
            os.makedirs(getImportFolder())
    except:
        print('Installation failed')
        return(False)
    print('Installation ok')
    return(True)


def ensureInstallationOk(window):
    """Ensure current working directory contains all required files.
    
    Check whether current working dir contains a valid installation. 
    Ask for directory if issues are found, and ensure installation is ok in new location.
    
    wx.Window frame to display Directory Dialog
    
    Return Boolean indicating a valid installation. 
    """
    global CurrentPath
    CurrentPath = os.getcwdu()
    if (not checkInstallation()):
        dlg = wx.DirDialog(window, 
                           _("The current working directory for this program is not a valid media directory. Choose a media directory:"), 
                           style=wx.DD_DEFAULT_STYLE)
        dlg.SetPath(CurrentPath)
        CurrentPath = None
        if (dlg.ShowModal() == wx.ID_OK):
            CurrentPath = dlg.GetPath()
            print('User selected "%s"' % CurrentPath)
            if (not checkInstallation()
                and not install()):
                CurrentPath = None
        else:
            print('Cancelled by user')
        dlg.Destroy()
    if (CurrentPath):
        print('Changing working directory to "%s"' % CurrentPath)
        os.chdir(CurrentPath)
        return(True)
    else:
        return(False)


# Executable Script
if __name__ == "__main__":
    pass


