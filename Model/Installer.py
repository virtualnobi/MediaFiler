# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import os.path
import shutil
## Contributed
## nobi
## Project
from Entry import Entry
from MediaClassHandler import MediaClassHandler



# Constants
InstallationPath = 'N:/project/MediaFiler'  # TODO: derive from installation data
ImageFolder = 'images'
LibraryFolder = 'lib'
LogoFilename = 'Logo.ico'
ClassFilename = 'classes.txt'
TrashFolder = 'trash'
ImportFolder = 'import'



def getImagePath(path):
    """Return the path to the image directory, given the root directory.
    """
    return(os.path.join(path, ImageFolder))


def getLibraryPath(path):
    """Return the path to the library directory, given the root directory.
    """
    return(os.path.join(path, LibraryFolder))


def getLogoPath(path):
    """Return the path to the logo icon, given the root directory.
    """
    return(os.path.join(getLibraryPath(path), LogoFilename))


def getClassFilePath(path):
    """Return the path to the class definition file, given the root dirctory.
    """
    return(os.path.join(getLibraryPath(path), ClassFilename))


def getTrashPath(path):
    """Return the path to the trash directory, given the root directory.
    """
    return(os.path.join(path, TrashFolder))


def getImportFolder(path):
    """Return the path to the default import directory, given the root directory.
    """
    return(os.path.join(path, ImportFolder))


def checkInstallation(path):
    """Determine whether the specified path contains all required files.
    
    String path
    Returns Boolean
    """
    if (not os.path.isdir(getImagePath(path))):
        return(False)
    if (not os.path.isdir(getLibraryPath(path))):
        return(False)
    if (not os.path.exists(getLogoPath(path))):
        return(False)
    for c in Entry.ProductTrader.getClasses():
        if (not os.path.exists(os.path.join(getLibraryPath(path), c.PreviewImageFilename))):
            print('No preview image for class %s exists.' % c)
            return(False)
    if (not os.path.exists(getClassFilePath(path))):
        return(False)
    if (not os.path.isdir(getTrashPath(path))):
        return(False)
    return(True)


def install(path):
    """Create required paths and files, keeping all existing settings.
    """
    if (not os.path.isdir(getImagePath(path))):
        os.makedirs(getImagePath(path))
    if (not os.path.isdir(getLibraryPath(path))):
        os.makedirs(getLibraryPath(path))
    if (not os.path.exists(getLogoPath(path))):
        shutil.copyfile(os.path.join(InstallationPath, LogoFilename), 
                        getLogoPath(path))
    for c in Entry.ProductTrader.getClasses():
        if (not os.path.exists(os.path.join(getLibraryPath(path), c.PreviewImageFilename))):
            shutil.copyfile(os.path.join(InstallationPath, 'images', c.PreviewImageFilename),
                            os.path.join(getLibraryPath(path), c.PreviewImageFilename))
    if (not os.path.exists(getClassFilePath(path))):
        with open(getClassFilePath(path), 'w') as cfile:
            cfile.write(MediaClassHandler.InitialFileContent)
    if (not os.path.isdir(getTrashPath(path))):
        os.makedirs(getTrashPath(path))
    
    

# Executable Script
if __name__ == "__main__":
    pass


