#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
from __future__ import print_function
## standard
from decimal import Decimal
import os
import glob
import shlex
import sys
import subprocess
import logging
#from collections import OrderedDict
## contributed
import wx
#from oset import oset 
## nobi
## project
import GlobalConfigurationOptions
from UI import GUIId
#from .MediaCollection import MediaCollection
from Model.Entry import Entry
#from Model.Group import Group
from Model.MediaOrganization import MediaOrganization
from Model.CachingController import CachingController



class ImageBitmap (wx.StaticBitmap):
    """An extension to wx.StaticBitmap which remembers the Entry it displays. 
     
    This class is used as the bitmap to display on UI.MediaCanvasPane.MediaCanvas. 
    When a bitmap is clicked, the underlying Entry can be recovered via .getEntry()
    """
## Lifecycle
    def __init__(self, parent, ident, entry, x, y, width, height):
        """Create bitmap and store entry for reference
        """
        # correct position (x, y) to place image in middle of frame
        (w, h) = entry.getSizeFittedTo(width, height)
        x = x + ((width - w) / 2)
        y = y + ((height - h) / 2)
        # inheritance
        wx.StaticBitmap.__init__(self, parent, ident, entry.getBitmap(width, height), pos=(x, y))
        # internal state
        self.entry = entry
 
         
    def getEntry(self):
        return(self.entry)



# Class 
class Single(Entry):
    """An Entry representing a single media file.
    """



# Constants
    ConfigurationOptionEmailClient = 'editor-email'



# Class Variables
# Class Methods
    @classmethod
    def getMediaTypeName(cls):
        """Return a translatable name for the subclasses of Single, for filter creation.
        """
        raise NotImplementedError


    @classmethod
    def getConfigurationOptionExternalViewer(self):
        """Return the configuration option to retrieve the command string for an external viewer of self.
        
        The string must contain the %1 spec which is replaced by the media file name.
        
        Return the external command string, or None if none given.
        """
        return(None)



# Lifecycle
    def __init__(self, model, path):
        """Create an Image from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        super(Single, self).__init__(model, path)
        # internal state
        self.rawImage = None
        self.bitmap = None



# Setters
    def renameTo(self, 
                 number=None, makeUnique=False, 
                 elements=None, removeIllegalElements=False,
                 **kwargs):
        """
        rootDir=None
        
        year=None
        month=None
        day=None 
        name=None
        scene=None
        """
        # possibly remove unknown tags/elements
        if (elements == None):  # no new elements, re-use existing ones
            elements = self.getElements()
        if (removeIllegalElements):  
            elements = [e for e in elements if self.model.getClassHandler().isLegalElement(e)]
        if (number): 
            kwargs['number'] = number
        kwargs['makeUnique'] = makeUnique
        if (elements):
            kwargs['elements'] = self.model.getClassHandler().elementsToString(elements)
        kwargs['removeIllegalElements'] = removeIllegalElements
        newPath = self.organizer.constructPathForSelf(**kwargs) 
        return(self.renameToFilename(newPath))



# Getters
## Inheritance - Entry
    def getEntriesForDisplay (self):
        """Return the list of entries to represent self in an image display.

        If self is filtered, return an empty Array.
        
        Returns Array of Entry. 
        """
        if (self.filteredFlag):
            return([])
        else:
            return([self])


    def getContextMenu(self):
        """Return a MediaFiler.Menu containing all context menu functions for Singles.

        Return wx.Menu
        """
        menu = super(Single, self).getContextMenu()
        # external viewer
        menu.insertAfterId(GUIId.FilterSimilar, newText=GUIId.FunctionNames[GUIId.StartExternalViewer], newId=GUIId.StartExternalViewer)
        if ((not self.__class__.getConfigurationOptionExternalViewer()) 
            or (not self.model.getConfiguration(self.__class__.getConfigurationOptionExternalViewer()))):
            menu.Enable(GUIId.StartExternalViewer, enable=False)
        # send email
        menu.Insert(0, GUIId.SendMail, GUIId.FunctionNames[GUIId.SendMail])
        if (not self.model.getConfiguration(Single.ConfigurationOptionEmailClient)):
            menu.Enable(GUIId.SendMail, enable=False)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions from the context menu.
        
        menuId Number from GUIId function numbers
        parentWindow wx.Window to open dialogs on
        Return String to display as status
            or None
        """
        message = None
        logging.debug('Single.runContextMenu(): Function %d on "%s"' % (menuId, self.getPath()))
        # TODO: move scene functions to OrganizationByName
        if (menuId == GUIId.StartExternalViewer):
            message = self.runExternalViewer(parentWindow)
        elif (menuId == GUIId.SendMail):
            message = self.sendMail()
        elif (menuId == GUIId.RandomConvertToSingle):
            pass
        elif (menuId == GUIId.ChooseConvertToSingle):
            pass
        else:
            message = super(Single, self).runContextMenuItem(menuId, parentWindow)
        return(message)


## Setters
    def removeNewIndicator(self):
        """Remove the new indicator on self's filename
        """
        if (MediaOrganization.NewIndicator in self.unknownElements):
            self.unknownElements.remove(MediaOrganization.NewIndicator)
            self.renameTo()


#     def convertToGroup(self):
#         """Convert the current Single to a Group with the same name.
#          
#         This function is only called on singletons organized by name.
#         """
#         # TODO: move to OrganizationByName
#         print('Single.convertToGroup() deprecated')
#         raise DeprecationWarning
#         print('Converting "%s" to a group' % self.getPath())
#         newGroup = Group.createFromName(self.model, self.getName())
#         self.setParentGroup(newGroup)
#         self.renameTo(scene='1', number='1')


    def changeScene (self, newScene):
        """Change the scene number of self.
        
        Returns True if successful, or False if failed (i.e., illegal NEWSCENE)
        """
        print('Single.changeScene() deprecated')
        raise DeprecationWarning
        pathNameOk = False
        if (self.model.organizedByDate):
            return(False)
        else:  # organized by name
            # change scene of self
            if (self.getScene() <> newScene):  # new scene, implies new number
                if (newScene == self.organizer.__class__.NewIndicator):
                    self.idScene = self.organizer.__class__.NewIndicator
                elif (int(newScene)):  # numeric scene
                    self.idScene = ('%02i' % int(newScene))
                else:  # illegal scene
                    return(False)
                # assign new number within scene
                self.idNumber = '001'
                # check for collisions of scene+number, incrementing number until no collisions
                while (not pathNameOk):
                    newPath = os.path.join (self.getDirectory(), 
                                            (self.getScene() + '-' + self.idNumber + '*'))  # only check for scene+number
                    pathNameOk = (len(glob.glob(newPath)) == 0)  # zero hits are required
                    if (not pathNameOk):
                        self.idNumber = ('%03i' % (int(self.number) + 1))  # increase number to check whether it's unused
            # construct element list
            elements = self.getElementString()
            # construct complete path with elements and extension
            newPath = os.path.join (self.getDirectory(), (self.getScene() + '-' + self.idNumber + elements + '.' + self.getExtension()))
            return(self.renameTo(newPath))


# Getters
    def isGroup (self):
        """Indicate that self is a single media.
        """
        return(False)


    def isIdentical(self, anEntry):
        """Check whether self and anEntry have the same content.
        
        Subclasses have to check for content, but this provides a quick check based on class and filesize.
        
        Returns a Boolean indicating that self and anEntry may be identical
        """
        super(Single, self).isIdentical(anEntry)  # ignore result, but do logging
        return((self.__class__ == anEntry.__class__) 
               and (self.getFileSize() == anEntry.getFileSize()))


    def getRawImage(self, debug=False):
        """Retrieve raw data (JPG or PNG or GIF) for media.
        """
        raise NotImplementedError


    def getRawDataMemoryUsage(self):
        """Return self's current memory usage for the raw image, in Bytes.
        
        Return Number
        """
        if (self.rawImage <> None):
            return(self.getRawImage().GetWidth() * self.getRawImage().GetHeight() * 3)  # taken from wx.Image.setData() documentation
        else:
            return(0)


    def releaseRawDataCache(self):
        """Release memory used for self's raw image.
        """
        self.rawImage = None
        CachingController.deallocateMemory(self, bitmap=False)



    def getSizeFittedTo(self, width=None, height=None):
        """Return the size of self fitted into the dimensions specified. 
        
        If neither width nor height are given, return the image's original size.

        Returns tuple of int (Number, Number)
        """
        rawWidth = self.getRawImage().GetWidth()
        rawHeight = self.getRawImage().GetHeight()
        assert (self.rawImage <> None), ('No raw image for "%s"!' % self.getPath())
        if ((width == None)
            and (height == None)):  # return original size
            return(rawWidth, rawHeight)
        elif ((width <> None) 
              and (height <> None)):  # fit to size given
            if (width < 1): 
                width = 1
            if (height < 1): 
                height = 1
            imageRatio = (Decimal(rawWidth) / Decimal(rawHeight))  # aspect of image
            paneRatio = (Decimal(width) / Decimal(height))  # aspect of frame
            logging.debug('Single.getSizeFittedTo(): Image %sx%s (ratio %s), Pane %sx%s (ratio %s)' % (rawWidth, rawHeight, imageRatio, width, height, paneRatio))
            if (paneRatio < imageRatio): # image wider than pane, use full pane width
                height = int(width / imageRatio)
                logging.debug('    changed height to %s' % height)
            else: # image taller than pane, use full pane height
                width = int(height * imageRatio)
                logging.debug('    changed width to %s' % width)
            if ((width > rawWidth) 
                and (height > rawHeight)):  # pane larger than image, don't enlarge image
                width = rawWidth
                height = rawHeight
                logging.debug('    using original size %sx%s' % (width, height))
            return(width, height)
        else:
            raise ValueError, 'Single.getSizeFittedTo(): Only one of width and height are given!'

    
    def getFileSize(self):
        """Return the file size of self, in kilobytes.
        
        Do not load the image. 
        """
        try: 
            int(self.fileSize)  # check whether self.fileSize is an integer value
        except: 
            self.fileSize = (int(os.stat(self.getPath()).st_size / 1024) + 1)
        return(self.fileSize)
        

    def getBitmap(self, width, height):
        """Return an MediaFiler.Single.ImageBitmap for self's image, resized to fit into given size.
        
        Number width
        Number height
        Returns MediaFiler.Single.ImageBitmap
        """
        # determine final size
        (w, h) = self.getSizeFittedTo(width, height)
        logging.debug('Single.getBitmap(%dx%d): Calculated size %dx%d for "%s"' % (width, height, w, h, self.getPath()))
        if (not ((0 < w) and (0 < h))):
            pass  # this will violate an assertion in Rescale()
        # load and resize bitmap if needed 
        if ((self.bitmap == None)  # no bitmap loaded
            or (self.bitmapWidth <> w)  # width differs
            or (self.bitmapHeight <> h)):  # height differs
            self.releaseBitmapCache()
            (self.bitmapWidth, self.bitmapHeight) = (w, h)
            logging.debug('Single.getBitmap(): Creating %dx%d bitmap' % (self.bitmapWidth, self.bitmapHeight))
            self.bitmap = self.getRawImage().Copy().Rescale(self.bitmapWidth, self.bitmapHeight).ConvertToBitmap()
        return(super(Single, self).getBitmap(width, height))



# Other API Functions
# Internal
    def runExternalViewer(self, parentWindow):
        """Run an external viewer, as given in MediaFiler configuration, to view self's media.
        
        wx.Window parentWindow is the window on which to display an error dialog, if needed
        """
        option = self.__class__.getConfigurationOptionExternalViewer()
        viewerName = self.model.getConfiguration(option)
        if (not viewerName):
            dlg = wx.MessageDialog(parentWindow,
                                   ('No external command specified with the\n"%s" option!' % option),
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        viewerName = viewerName.replace(GlobalConfigurationOptions.Parameter, self.getPath())
        viewerName = viewerName.encode(sys.getfilesystemencoding())
        commandArgs = shlex.split(viewerName)  # viewerName.split() will not respect quoting (for whitespace in file names)
        print('Calling %s' % commandArgs)
        result = subprocess.call(commandArgs, shell=False)
        if (result <> 0):
            dlg = wx.MessageDialog(parentWindow,
                                   ('External command\n"%s"\nfailed with error code %d!' % (viewerName, result)),
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()


    def sendMail(self):
        """Open the email client as listed in the configuration with self's media as attachment.
        """
        emailClient = self.model.getConfiguration(Single.ConfigurationOptionEmailClient)        
        if (emailClient):
            emailClient = emailClient.replace(GlobalConfigurationOptions.Parameter, self.getPath())
            commandArgs = shlex.split(emailClient)
            subprocess.call(commandArgs, shell=False)
