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
import shlex
import sys
import subprocess
import logging
import hashlib
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
#from Model.MediaOrganization import MediaOrganization
from Model.CachingController import CachingController
from .MediaClassHandler import MediaClassHandler



# Package Variables
Logger = logging.getLogger(__name__)



class ImageBitmap(wx.StaticBitmap):
    """An extension to wx.StaticBitmap which remembers the Entry it displays. 
     
    This class is used as the bitmap to display on UI.MediaCanvasPane.MediaCanvas. 
    When a bitmap is clicked, the underlying Entry can be recovered via .getEntry()
    """



# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, parent, ident, entry, x, y, width, height):
        """Create bitmap and store entry for reference
        """
        # correct position (x, y) to place image in middle of frame
        bitmap = entry.getBitmap(width, height)
#         bitmap = wx.Bitmap.FromRGBA(width, height, red=255, green=0, blue=0, alpha=0)
        (w, h) = bitmap.GetSize()
        x = x + ((width - w) / 2)
        y = y + ((height - h) / 2)
        # inheritance
        wx.StaticBitmap.__init__(self, parent, ident, bitmap, pos=(x, y))
        # internal state
#         self.SetBitmap(entry.getBitmap(width, height))
        self.entry = entry
 
         
    def getEntry(self):
        return(self.entry)



# Class 
class Single(Entry):
    """An Entry representing a single media file.
    """



# Constants
    ConfigurationOptionEmailClient = 'editor-email'
    InputLengthForKey = (1024 * 8)



# Class Variables
# Class Methods
    @classmethod
    def getMediaTypeName(cls):
        """Return a translatable name for the subclasses of Single, for filter creation.
        """
        raise NotImplementedError


    @classmethod
    def getRawImageFromPath(cls, aMediaCollection, path):
        """Return a raw image to represent the media content of the given file.
        
        Model.MediaCollection aMediaCollection
        String path
        Return 
        """
#         raise NotImplementedError
        Logger.error('Single.getRawImageFromPath(): Subclass should implement this method!')
        return(None)



    @classmethod
    def getConfigurationOptionExternalViewer(self):
        """Return the configuration option to retrieve the command string for an external viewer of self.
        
        The string must contain the %1 spec which is replaced by the media file name.
        
        Return the external command string, or None if none given.
        """
        return(None)


    @classmethod
    def getKeyFromFile(self, path):
        """Calculate a key to be used in MediaMap, from a Single's file
        
        Return String
        """
#         # just use filesize
#         # use prefix of file content
#         with open(path, 'rb') as f:
#             key = f.read(MediaMap.KeyLength)
#         key = unicode(key, 'ascii', 'replace')
        # use hash of longer prefix of file content
        with open(path, 'rb') as f:
            prefix = f.read(Single.InputLengthForKey)
        algorithm = hashlib.md5()
        algorithm.update(prefix)
        key = algorithm.hexdigest()
        return(key)



# Lifecycle
    def __init__(self, model, path):
        """Create an Image from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        super(Single, self).__init__(model, path)
        # internal state
        self.rawImage = None
        # raw image size must be cached independently from raw image, 
        # to allow determination of fitted bitmap without reloading the raw image in getSizeFittedTo()
        self.rawImageWidth = 0
        self.rawImageHeight = 0
        self.bitmap = None
        self.duplicates = []



# Setters
    def renameTo(self, **kwargs):
        """Rename a Single entry. See Entry.renameTo(). 
       
        Set of String elements 
        Boolean removeIllegalElements
        dict kwargs
        Return Entry to be shown after renaming
        """
        return(self.getOrganizer().renameSingle(**kwargs))


    def setDuplicates(self, duplicates):
        """Store a list of Single instances which have identical content. 
        """
        self.duplicates = duplicates



# Getters
    def getKey(self):
        """Calculate a key for self to be used in MediaMap.
        
        Return String
        """
        return(Single.getKeyFromFile(self.getPath()))

    
    def getDuplicates(self):
        """Return the stored list of other Single instances which have identical content.
        
        Returns a List of Single
        """
        return(self.duplicates)



# Inheritance - Entry
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
        # media functions
        menu.Insert(0, 
                    GUIId.StartExternalViewer, 
                    GUIId.FunctionNames[GUIId.StartExternalViewer], 
                    "", 
                    wx.ITEM_NORMAL)
        if ((not self.__class__.getConfigurationOptionExternalViewer()) 
            or (not self.model.getConfiguration(self.__class__.getConfigurationOptionExternalViewer()))):
            menu.Enable(GUIId.StartExternalViewer, enable=False)
        menu.insertAfterId(GUIId.StartExternalViewer, 
                           newText=GUIId.FunctionNames[GUIId.SendMail], 
                           newId=GUIId.SendMail)
        if (not self.model.getConfiguration(Single.ConfigurationOptionEmailClient)):
            menu.Enable(GUIId.SendMail, enable=False)
        menu.insertAfterId(GUIId.SendMail,
                           newText=GUIId.FunctionNames[GUIId.ShowDuplicates],
                           newMenu=self.constructDuplicateMenu())
        # structure functions
        # group functions
        # delete functions
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions from the context menu.
        
        menuId Number from GUIId function numbers
        parentWindow wx.Window to open dialogs on
        Return String to display as status
            or None
        """
        message = None
        Logger.debug('Single.runContextMenu(): Function %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.StartExternalViewer):
            message = self.runExternalViewer(parentWindow)
        elif (menuId == GUIId.SendMail):
            message = self.sendMail()
        elif ((menuId <= GUIId.ShowDuplicates)
              and ((GUIId.ShowDuplicates + GUIId.MaxNumberDuplicates) <= menuId)):
            duplicateIndex = (menuId - GUIId.ShowDuplicates)
            duplicate = self.duplicates[duplicateIndex]
            self.getModel().setSelectedEntry(duplicate)
        else:
            message = super(Single, self).runContextMenuItem(menuId, parentWindow)
        return(message)


## Setters
    def removeNewIndicator(self):
        """Remove the new indicator on self's filename
        """
        if (MediaClassHandler.ElementNew in self.unknownElements):
            pathInfo = self.getOrganizer().getPathInfo()
            pathInfo['elements'] = (self.getUnknownElements() - set(MediaClassHandler.ElementNew))
            self.renameTo(**pathInfo)



# Getters
    def getFileSize(self):
        """Return the file size of self, in kilobytes.
        
        Do not load the image. 
        """
        try: 
            int(self.fileSize)  # check whether self.fileSize is an integer value
        except: 
            self.fileSize = (int(os.stat(self.getPath()).st_size / 1024) + 1)
        return(self.fileSize)
        

    def isIdenticalContent(self, anEntry):
        """Check whether self and anEntry have the same content.
        
        Subclasses have to check for content, but this provides a quick check based on class and filesize.
        
        Returns a Boolean indicating that self and anEntry are identical
        """
        return(super(Single, self).isIdenticalContent(anEntry) 
               and (self.getFileSize() == anEntry.getFileSize()))


    def getRawImage(self):
        """Retrieve raw data (JPG or PNG or GIF) for media.
        """
        if (self.rawImage):
            return(self.rawImage)
        encodedPath = self.getPath()  # .encode(sys.getfilesystemencoding())
        try:
            self.rawImage = self.__class__.getRawImageFromPath(self.model, encodedPath)
            self.rawImageHeight = self.rawImage.GetHeight()
            self.rawImageWidth = self.rawImage.GetWidth()
        except:  # getting here means even the default preview images are corrupt
            self.rawImage = wx.Image(10, 10)
        CachingController.allocateMemory(self, 
                                         self.getRawDataMemoryUsage(), 
                                         cachePriority=Entry.CachingLevelRawData)
        self.releaseCacheWithPriority(Entry.CachingLevelFullsizeBitmap)
        self.releaseCacheWithPriority(Entry.CachingLevelThumbnailBitmap)
        return(self.rawImage)


    def getRawImageWidth(self):
        if (self.rawImageWidth == 0):
            self.getRawImage()
        return(self.rawImageWidth)
    
    
    def getRawImageHeight(self):
        if (self.rawImageHeight == 0):
            self.getRawImage()
        return(self.rawImageHeight)


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
        if ((width == None)
            and (height == None)):  # return original size
            return(self.getRawImageWidth(), self.getRawImageHeight())
        elif ((width <> None) 
              and (height <> None)):  # fit to size given
            if (width < 1): 
                Logger.warning('Single.getSizeFittedTo(): Corrected width to 1 for "%s"', self.getPath())
                width = 1
            if (height < 1): 
                Logger.warning('Single.getSizeFittedTo(): Corrected height to 1 for "%s"', self.getPath())
                height = 1
            if ((self.getRawImageWidth() < width) 
                and (self.getRawImageHeight() < height)):  # pane larger than image, don't enlarge image
                width = self.getRawImageWidth()
                height = self.getRawImageHeight()
                Logger.debug('    image smaller than pane, using original size')
            else:
                imageRatio = (Decimal(self.getRawImageWidth()) / Decimal(self.getRawImageHeight()))  # aspect of image
                paneRatio = (Decimal(width) / Decimal(height))  # aspect of frame
                Logger.debug('Single.getSizeFittedTo(): Image %sx%s (ratio %s), Pane %sx%s (ratio %s)' % (self.getRawImageWidth(), 
                                                                                                          self.getRawImageHeight(), 
                                                                                                          imageRatio, 
                                                                                                          width, 
                                                                                                          height, 
                                                                                                          paneRatio))
                if (paneRatio < imageRatio): # image wider than pane, use full pane width
                    height = int(width / imageRatio)
                    Logger.debug('    changed height to %s' % height)
                else: # image taller than pane, use full pane height
                    width = int(height * imageRatio)
                    Logger.debug('    changed width to %s' % width)
            Logger.debug('    using size %sx%s for %s' % (width, height, self.getPath()))
            return(width, height)
        else:
            raise ValueError, ('Single.getSizeFittedTo(): Only one of width and height are given for %s!' % self.getPath())

    
    def getBitmap(self, width, height):
        """Return an MediaFiler.Single.ImageBitmap for self's image, resized to fit into given size.
        
        Number width
        Number height
        Boolean cacheAsThumbnail indicates whether width x height is fullsize or thumbnail
        Returns MediaFiler.Single.ImageBitmap
        """
        (w, h) = self.getSizeFittedTo(width, height)
        if ((self.bitmap == None)
            or (self.bitmapWidth <> w)
            or (self.bitmapHeight <> h)):
            self.releaseCacheWithPriority(Single.CachingLevelThumbnailBitmap)
            if (w == 0):
                w = 1
            if (h == 0):
                h = 1
            Logger.debug('Single.getBitmap(): Creating %dx%d bitmap' % (w, h))
            self.bitmap = self.getRawImage().Copy().Rescale(w, h).ConvertToBitmap()
            (self.bitmapWidth, self.bitmapHeight) = (w, h)
            self.registerCacheWithPriority(Single.CachingLevelThumbnailBitmap)
        return(self.bitmap)


#     def getRealBitmap(self, width, height, cacheAsThumbnail = True):
#         """Return a wx.StaticBitmap for self's image, resized to fit into given size.
#         
#         Number width
#         Number height
#         Boolean cacheAsThumbnail indicates whether width x height is fullsize or thumbnail
#         Returns MediaFiler.Single.ImageBitmap
#         """
#         (w, h) = self.getSizeFittedTo(width, height)
#         if (w == 0):
#             w = 1
#         if (h == 0):
#             h = 1
#         if ((self.bitmap == None)
#             or (self.bitmapWidth <> w)
#             or (self.bitmapHeight <> h)):
#             self.releaseCacheWithPriority(Single.CachingLevelThumbnailBitmap)
#             Logger.debug('Single.getBitmap(): Creating %dx%d bitmap' % (w, h))
#             self.bitmap = self.getRawImage().Copy().Rescale(w, h).ConvertToBitmap()
#             (self.bitmapWidth, self.bitmapHeight) = (w, h)
#             self.registerCacheWithPriority(Single.CachingLevelThumbnailBitmap)
# #             x = x + ((width - w) / 2)
# #             y = y + ((height - h) / 2)
# #             wx.StaticBitmap.__init__(self, parent, ident, bitmap, pos=(x, y))
#         return(self.bitmap)



# Other API Functions
# Internal
    def constructDuplicateMenu(self):
        """Return submenu containing all duplicates of self.
        
        Return wx.Menu
        """
        result = wx.Menu()
        duplicateId = GUIId.ShowDuplicates
        for duplicate in self.getDuplicates():
            result.Append(duplicateId, duplicate.getOrganizationIdentifier())
            duplicateId = (duplicateId + 1)
        return(result)



    def runExternalViewer(self, parentWindow):
        """Run an external viewer, as given in MediaFiler configuration, to view self's media.
        
        wx.Window parentWindow is the window on which to display an error dialog, if needed
        """
        option = self.__class__.getConfigurationOptionExternalViewer()
        Logger.debug('Single.runExternalViewer(): Looking for configuration of "%s"' % option)
        viewerName = self.model.getConfiguration(option)
        if (not viewerName):
            Logger.warn('Single.runExternalViewer(): No external program specified for option "%s"' % option)
            dlg = wx.MessageDialog(parentWindow,
                                   ('No external command specified with the\n"%s" option!' % option),
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        Logger.debug('Single.runExternalViewer(): Found external program "%s"' % viewerName)
        viewerName = viewerName.replace(GlobalConfigurationOptions.Parameter, self.getPath())
        viewerName = viewerName.encode(sys.getfilesystemencoding())
        commandArgs = shlex.split(viewerName)  # viewerName.split() will not respect quoting (for whitespace in file names)
        Logger.debug('Single.runExternalViewer(): Calling "%s"' % commandArgs)
        result = subprocess.call(commandArgs, shell=False, stderr=subprocess.STDOUT)  # err=OUT needed due to win_subprocess bug
        if (result <> 0):
            Logger.warn('Single.runExternalViewer(): External command "%s" failed with %s' % (commandArgs, result))
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
            subprocess.call(commandArgs, shell=False, stderr=subprocess.STDOUT)  # err=OUT needed due to win_subprocess bug


