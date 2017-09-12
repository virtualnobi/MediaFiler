# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import os.path
import shutil
import gettext
import logging
## Contributed
import wx
## nobi
from nobi import SecureConfigParser
from nobi import ProductTraderPattern
## Project
import GlobalConfigurationOptions
# from Entry import Entry
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



# Variables
ProductTrader = ProductTraderPattern.SimpleProductTrader()



# Setters
# Getters
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


def getProductTrader():
    """Return the ProductTrader which associates subclasses of Entry with file types.
    """ 
    return(ProductTrader)



# Other API Functions
def checkInstallation():
    """Determine whether the specified path contains all required files.

    Returns Boolean indicating whether the installation is ok
    """
    logging.debug('Installer.checkInstallation(): Checking folders at "%s"...' % CurrentPath)
    if (not os.path.isdir(getImagePath())):
        logging.debug('Installer.checkInstallation(): Image directory does not exist')
        return(False)
    if (not os.path.isdir(getLibraryPath())):
        logging.debug('Installer.checkInstallation(): Library directory does not exist')
        return(False)
    if (not os.path.exists(getLogoPath())):
        logging.debug('Installer.checkInstallation(): Logo image does not exist')
        return(False)
    if (not os.path.exists(getConfigurationFilePath())):
        logging.debug('Installer.checkInstallation(): Configuration file does not exist')
        return(False)
#     for c in Entry.ProductTrader.getClasses():
    for c in getProductTrader().getClasses():
        if (not os.path.exists(os.path.join(getLibraryPath(), c.PreviewImageFilename))):
            logging.debug('Installer.checkInstallation(): No preview image for class %s exists.' % c)
            print('No preview image for class %s exists.' % c)
            return(False)
    if (not os.path.exists(getClassFilePath())):
        logging.debug('Installer.checkInstallation(): Tag name file does not exist')
        return(False)
    if (not os.path.isdir(getTrashPath())):
        logging.debug('Installer.checkInstallation(): Trash directory does not exist')
        return(False)
    logging.debug('Installer.checkInstallation(): Folders at "%s" are ok' % CurrentPath)
    return(True)


def install():
    """Create required paths and files in global CurrentPath, keeping all existing settings.

    Return Boolean indicating installation succeeded
    """
    logging.debug('Installer.install(): Preparing folders at "%s"' % CurrentPath)
    try:
        if (not os.path.isdir(getImagePath())):
            os.makedirs(getImagePath())
            logging.debug('Installer.install(): Image folder created')
        if (not os.path.isdir(getLibraryPath())):
            os.makedirs(getLibraryPath())
            logging.debug('Installer.install(): Library folder created')
        if (not os.path.exists(getLogoPath())):
            shutil.copyfile(os.path.join(InstallationPath, ImageFolder, LogoFilename), 
                            getLogoPath())
            logging.debug('Installer.install(): Logo file copied')
        if (not os.path.exists(getConfigurationFilePath())):
            config = SecureConfigParser.SecureConfigParser(getConfigurationFilePath())
            config.add_section(GUIId.AppTitle)
            config.set(GUIId.AppTitle, 
                       GlobalConfigurationOptions.TextEditor, 
                       ('notepad /W "%s"' % GlobalConfigurationOptions.Parameter))
            logging.debug('Installer.install(): Configuration file created')
        for c in getProductTrader().getClasses():
            if (not os.path.exists(os.path.join(getLibraryPath(), c.PreviewImageFilename))):
                shutil.copyfile(os.path.join(InstallationPath, ImageFolder, c.PreviewImageFilename),
                                os.path.join(getLibraryPath(), c.PreviewImageFilename))
                logging.debug('Installer.install(): Preview image %s copied' % c.PreviewImageFilename)
        if (not os.path.exists(getClassFilePath())):
            with open(getClassFilePath(), 'w') as cfile:
                cfile.write(MediaClassHandler.InitialFileContent)
            logging.debug('Installer.install(): Tag file created')
        if (not os.path.isdir(getTrashPath())):
            os.makedirs(getTrashPath())
            logging.debug('Installer.install(): Trash folder created')
        if (not os.path.isdir(getImportFolder())):
            os.makedirs(getImportFolder())
            logging.debug('Installer.install(): Import folder created')
    except Exception as e:
        logging.critical('Installer.install(): Installation failed with exception:\n%s' % e)
        return(False)
    logging.debug('Installer.install(): Folders at "%s" are ok' % CurrentPath)
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
                           _('The current working directory for this program is not a valid media directory. Choose a media directory:'), 
                           style=wx.DD_DEFAULT_STYLE)
        dlg.SetPath(CurrentPath)
        CurrentPath = None
        if (dlg.ShowModal() == wx.ID_OK):
            CurrentPath = dlg.GetPath()
            if (not checkInstallation()
                and not install()):
                dlg = wx.MessageDialog(window, _('Creation of required folders and files failed.'), _('Error'), wx.CANCEL)
                dlg.ShowModal()
                dlg.Destroy()
                CurrentPath = None
        else:
            logging.debug('Installer.ensureInstallationOk(): Cancelled by user')
        dlg.Destroy()
    if (CurrentPath):
        logging.debug('Installer.ensureInstallationOk(): Changing working directory to "%s"' % CurrentPath)
        os.chdir(CurrentPath)
        return(True)
    else:
        return(False)


# Executable Script
if __name__ == "__main__":
    pass


