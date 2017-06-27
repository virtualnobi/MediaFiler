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
## contributed
import wx
#from oset import oset 
## nobi
## project
from UI import GUIId
from MediaCollection import MediaCollection
from .Entry import Entry
from .Group import Group
from collections import OrderedDict
from .Organization import OrganizationByName, MediaOrganization



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
        (w, h) = entry.getSize(width, height)
        x = x + ((width - w) / 2)
        y = y + ((height - h) / 2)
        # inheritance
        wx.StaticBitmap.__init__(self, parent, ident, entry.getBitmap(width, height), pos=(x, y))
        # internal state
        self.entry = entry
 
         
    def getEntry(self):
        return(self.entry)



# Class
class MRUOrderedDict(OrderedDict):
    """Stores items in the order the keys were last added
    
    This class is used to register the memory consumption of Single media. 
    If too much memory is used, the least recently used Singles are requested to free memory. 
    """
    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)



# Class 
class Single(Entry):
    """An Entry representing a single media file.
    """



# Constants
    MemoryMaximum = 8000000000  # fictional memory maximum to be used for Singles
    ConfigurationOptionEmailClient = 'editor-email'



# Class Variables
    MemoryUsed = 0  # current memory consumption in subclasses
    MemoryUsageList = MRUOrderedDict()



# Class Methods
    @classmethod
    def registerMemoryConsumption(cls, entry, imageSize):
        """Stores the memory consumed by entry, and releases memory of other images if overall consumption is too high.
        
        MediaFiler.Entry entry is the media being displayed
        Number imageSize is the number of bytes consumed by entry
        """
        logging.debug('%dKB free, consuming %dKB for "%s"' % (((cls.MemoryMaximumm - cls.MemoryUsed) / 1024), (imageSize / 1024), entry.getPath()))
        cls.MemoryUsed = (cls.MemoryUsed + imageSize)
        cls.MemoryUsageList[entry] = imageSize
        while (cls.MemoryMaximum < cls.MemoryUsed):
            (oldEntry, oldSize) = cls.MemoryUsageList.popitem(last=False)
            print('\treleasing %dKB from "%s"' % ((oldSize / 1024), oldEntry.getPath()))
            cls.MemoryUsed = (cls.MemoryUsed - oldSize)
            oldEntry.releaseMemory()



# Lifecycle
    def __init__ (self, model, path):
        """Create an Image from the file at PATH, based on imageFilerModel MODEL. 
        """
        # inheritance
        Entry.__init__(self, model, path)
        # internal state
        self.fileSize = None
        return(None)



# Setters
    def renameTo(self, 
                 year=None, month=None, day=None, 
                 name=None, scene=None, 
                 number=None, makeUnique=False, 
                 elements=None, removeIllegalElements=False):
        """Override of Entry.renameTo()
        """
        if (self.model.organizedByDate):
            pass
        else:  # organized by name
            if (self.organizer.isSingleton()
                and name
                and (name <> self.organizer.getName())):
                newEntry = self.model.getEntry(name=name, group=True)
                if (newEntry):
                    scene = MediaOrganization.NewIndicator
                    makeUnique = True
                else:
                    newEntry = self.model.getEntry(name=name, group=False)
                    if (newEntry):
                        print('Single.renameTo(): Merging of singletons into a group NYI!')  # TODO:
                        return
                    else:  # name does not yet exist
                        pass
            else:  # part of a named Group(); assume parameters are correctly set by invoking group
                pass
        return(super(Single, self).renameTo(year=year, month=month, day=day,
                                            name=name, scene=scene, 
                                            number=number, makeUnique=makeUnique, 
                                            elements=elements, removeIllegalElements=removeIllegalElements))



# Getters
    def getConfigurationOptionExternalViewer(self):
        """Return the configuration option to retrieve the command string for an external viewer of self.
        
        The string must contain the %1 spec which is replaced by the media file name.
        
        Return the external command string, or None if none given.
        """
        return(None)



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

        GUIId.StartExternalViewer is handled in subclasses Image and Movie.
        """
        menu = super(Single, self).getContextMenu()
        menu.Insert(0, GUIId.StartExternalViewer, GUIId.FunctionNames[GUIId.StartExternalViewer])
        if ((not self.getConfigurationOptionExternalViewer()) 
            or (not self.model.getConfiguration(self.getConfigurationOptionExternalViewer()))):
            menu.Enable(GUIId.StartExternalViewer, enable=False)
        menu.Append(GUIId.SendMail, GUIId.FunctionNames[GUIId.SendMail])
        if (not self.model.getConfiguration(Single.ConfigurationOptionEmailClient)):
            menu.Enable(GUIId.SendMail, enable=False)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions from the context menu.
        
        GUIId.StartExternalViewer is handled in subclasses Image and Movie.
        
        menuId Number from GUIId function numbers
        parentWindow wx.Window to open dialogs on
        Return String to display as status
            or None
        """
        #print('Single.runContextMenu: %d on "%s"' % (menuId, self.getPath()))
        # TODO: move scene functions to OrganizationByName
        if ((GUIId.SelectScene <= menuId)
            and (menuId < (GUIId.SelectScene + GUIId.MaxNumberScenes))):  # function "change to scene..."
            newScene = self.getParentGroup().getScenes()[menuId - GUIId.SelectScene]
            #print('Changing scene of "%s" to %s' % (self.organizer.getPath(), newScene))
            self.renameTo(makeUnique=True, scene=newScene)
        elif (menuId == GUIId.RelabelScene):
            newScene = self.askNewScene(parentWindow)
            if (newScene):
                self.organizer.relabelToScene(newScene)
        elif (menuId == GUIId.RandomConvertToSingle):
            pass
        elif (menuId == GUIId.ChooseConvertToSingle):
            pass
        elif (menuId == GUIId.ConvertToGroup):  # turn single media into a group
            self.convertToGroup()
        elif (menuId == GUIId.StartExternalViewer):
            self.runExternalViewer(parentWindow)
        elif (menuId == GUIId.SendMail):
            return(self.sendMail())
        else:
            return(super(Single, self).runContextMenuItem(menuId, parentWindow))


## Setters
    def removeBitmap(self):
        """Remove self's bitmap because it must be resized.
        """
        if (self.bitmap):
            self.registerMemoryConsumption(self, -self.getBitmapMemoryUsage())
            self.bitmap = None 
            self.bitmapWidth = None
            self.bitmapHeight = None


    def releaseMemory(self):
        """Release memory used for self's raw image
        """
        raise('Subclass must implement releaseMemory()')


    def removeNewIndicator(self):
        """Remove the new indicator on self's filename
        """
        if ('new' in self.unknownElements):
            self.unknownElements.remove('new')
            self.renameTo()


    def convertToGroup(self):
        """Convert the current Single to a Group with the same name.
        
        This function is only called on singletons organized by name.
        """
        print('Single.convertToGroup() deprecated')
        print('Converting "%s" to a group' % self.getPath())
        newGroup = Group.createFromName(self.model, self.getName())
        self.setParentGroup(newGroup)
        self.renameTo(name=self.getName(), scene='01', number='001')

    
    def changeScene (self, newScene):
        """Change the scene number of self.
        
        Returns True if successful, or False if failed (i.e., illegal NEWSCENE)
        """
        print('Single.changeScene() deprecated')
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


## Getters
    def isGroup (self):
        """Indicate that self is a single media.
        """
        return(False)


    def isSingleton(self):
        """Indicate whether self is the only media for its name. 
        
        If organized by date, return False.
        """
        return(self.organizer.isSingleton())


    def isIdentical(self, anEntry):
        """Check whether self and anEntry have the same content.
        
        Subclasses have to check for content, but this provides a quick check based on class and filesize.
        
        Returns a Boolean indicating that self and anEntry may be identical
        """
        super(Single, self).isIdentical(anEntry)  # ignore result, but do logging
        return((self.__class__ == anEntry.__class__) 
               and (self.getFileSize() == anEntry.getFileSize()))


    def getRawImage(self, debug=False):
        """Retrieve raw data (JPG or PNG or GIF) for image.
        """
        raise NotImplementedError


    def getSize(self, width=None, height=None):
        """Return the size of self. If width and height are given, return the size after fitting self to the parameters.
        
        Returns (w, h)
        """
        rawImage = self.getRawImage()  # get image in original size
        if (rawImage == None):
            print('Raw image of "%s" doesn\'t exist' % self.getPath())
            rawImage = self.getRawImage(True)  # TODO: add debugging flag
        if ((width == None) 
            and (height == None)):  # return original size
            return(rawImage.Width, rawImage.Height)
        elif ((width <> None) 
              and (height <> None)):  # fit to size given
            if (width < 1): 
                width = 1
            if (height < 1): 
                height = 1
            imageRatio = (Decimal(rawImage.Width) / Decimal(rawImage.Height))  # aspect of image
            paneRatio = (Decimal(width) / Decimal(height))  # aspect of frame
            #print ("Image %sx%s (ratio %s), Pane %sx%s (ratio %s)" % (self.rawWidth, self.rawHeight, imageRatio, width, height, paneRatio))
            if (paneRatio < imageRatio): # image wider than pane, use full pane width
                height = int(width / imageRatio)
                #print ("    changed height to %s" % height)
            else: # image taller than pane, use full pane height
                width = int(height * imageRatio)
                #print ("    changed width to %s" % width)
            if ((width > rawImage.Width) 
                and (height > rawImage.Height)):  # pane larger than image, don't enlarge image
                width = rawImage.Width
                height = rawImage.Height
            return(width, height)
        else:  # illegal parameters
            raise('Illegal Parameters to Single.getSize() - only one of width and height are given')
        

    def getFileSize(self):
        """Return the file size of self, in kilobytes.
        
        Do not load the image. 
        """
        if (self.fileSize == None):
            self.fileSize = (int(os.stat(self.getPath()).st_size / 1024) + 1)
        return(self.fileSize)
        

    def getBitmap(self, width, height):
        """Return an MediaFiler.Single.ImageBitmap for self's image, resized to fit into given size.
        
        Number width
        Number height
        Returns a MediaFiler.Single.ImageBitmap fitted into (width x height)
        """
        print('Single.getBitMap(%dx%d) for "%s"' % (width, height, self.getPath()))
        # determine final size
        (w, h) = self.getSize(width, height)
        print('  final size (%dx%d)' % (width, height))
        if (not ((0 < w) and (0 < h))):
            pass  # this will violate an assertion in Rescale()
        # load and resize bitmap if needed 
        if ((self.bitmap == None)  # no bitmap loaded
            or (self.bitmapWidth <> w)  # width differs
            or (self.bitmapHeight <> h)):  # height differs
            if (self.bitmap):
                #print('    bitmap of %dx%d' % (self.bitmapWidth, self.bitmapHeight))
                self.registerMemoryConsumption(self, -self.getBitmapMemoryUsage())
            (self.bitmapWidth, self.bitmapHeight) = (w, h)
            self.bitmap = self.getRawImage().Copy().Rescale(self.bitmapWidth, self.bitmapHeight).ConvertToBitmap()
            #print('    resized to %dx%d' % (self.bitmapWidth, self.bitmapHeight))
            self.registerMemoryConsumption(self, self.getBitmapMemoryUsage())
        return(self.bitmap)


    def getBitmapMemoryUsage(self):
        """Return self's current memory usage for the bitmap, in Bytes.
        """
        if (self.bitmap <> None):
            return(self.bitmapWidth * self.bitmapHeight * 3)  # assumption
        else:
            return(0)



# Internal
    def askNewScene(self, parentWindow):
        """User wants to relabel a scene (organized by name). Ask for new scene. 
        
        Returns String containing new name, or None if user cancelled. 
        """
        dialog = wx.TextEntryDialog(parentWindow, 'Enter New Scene', 'Relabel Scene', '')
        ok = True
        newScene = -1
        newSceneString = None
        while (ok 
               and ((newScene < 0) or (99 < newScene))):
            ok = (dialog.ShowModal() == wx.ID_OK)
            if (ok):
                newSceneString = dialog.GetValue()
                try: 
                    newScene = int(newSceneString)
                except: 
                    newScene = -1
                if ((newScene < 0) or (999 < newScene)):
                    dialog.SetValue('%s is not a legal name' % newSceneString)
                else:
                    newSceneString = (OrganizationByName.FormatScene % newScene)
            else:
                newSceneString = None
        dialog.Destroy()
        return (newSceneString)


    def runExternalViewer(self, parentWindow):
        """Run an external viewer, as given in MediaFiler configuration, to view self's media.
        
        wx.Window parentWindow is the window on which to display an error dialog, if needed
        """
        option = self.getConfigurationOptionExternalViewer()
        viewerName = self.model.getConfiguration(option)
        if (not viewerName):
            dlg = wx.MessageDialog(parentWindow,
                                   ('No external command specified with the\n"%s" option!' % option),
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        viewerName = viewerName.replace(MediaCollection.ConfigurationOptionParameter, self.getPath())
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
            emailClient = emailClient.replace(MediaCollection.ConfigurationOptionParameter, self.getPath())
            commandArgs = shlex.split(emailClient)
            subprocess.call(commandArgs, shell=False)
