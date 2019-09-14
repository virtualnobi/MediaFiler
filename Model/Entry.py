"""
(c) by nobisoft 2015-
"""


# Imports
## Standard
#import sys
import re
import os.path
import logging
#import datetime
## Contributed
## nobi
from nobi.ObserverPattern import Observable
from nobi.wx.Menu import Menu
#from nobi.logging import profiledOnLogger
from nobi.os import makeUnique
## Project
from UI import GUIId
import Installer
from Model.MediaClassHandler import MediaClassHandler
from Model.CachingController import CachingController



# Package Variables
Logger = logging.getLogger(__name__)



# Class 
class Entry(Observable):
    """An Entry is an Observable representing a (group of) media in the directory tree. 
    A group can either be a folder (based on directory structure) or be based on special naming of image files.
    
    The filename of the entry consists of its path, its name, and its extension.
    The name of the entry consists of its identifier, its number, its known elements, and its unknown elements.
    The identifier is the date (if the model is organized by date) 
    or the name (if the model is organized by name) (for singleton images, not contained in a Group) 
    or the name and the scene (for images contained in a Group).

    ObserverPattern aspects
    - name: The file name on disk has changed
    - remove: The entry is deleted
    - children: The children of an entry group have changed
    Pausing updates is used in batch commands like the deletion of doubles.
    """



# Constants
    SpecificationGroup = 'directory'  # Specification for ProductTrader, registering to handle directories
    CachingLevelThumbnailBitmap = 0
    CachingLevelFullsizeBitmap = 1
    CachingLevelRawData = 2



# Class Variables    
# Class Methods
    @classmethod
    def isLegalExtension(self, extension):
        """Check whether extension denotes a file type which is handled by Entry or its subclasses.
        
        String extension is the file name extension (without '.', upper and lower case handled)
        Return Boolean indicating whether extension is handled by Entry
        """
        try:
            Installer.getProductTrader().getClassFor(extension.lower())
        except:  # no class registered for this extension
            return(False)
        return(True)


    @classmethod
    def getSubclassForPath(self, path):
        """Return the subclass of Entry to create an entry for the specified file.

        path String
        Returns a subclass of Entry 
        """
        if (os.path.isdir(path)):
            clas = Installer.getProductTrader().getClassFor(self.SpecificationGroup)
        else:
            (dummy, extension) = os.path.splitext(path) 
            extension = extension[1:].lower()  # remove leading '.'
            try:
                clas = Installer.getProductTrader().getClassFor(extension)
            except:  
                Logger.error('Entry.getSubclassForPath(): No class registered to instantiate "%s" media "%s"!' % (extension, path))
                return(None)
        return(clas)


    @classmethod
    def createInstance(self, model, path):
        """Return an instance of (a subclass of) Entry to represent the given media file.

        model imageFilerModel
        path String
        Returns an instance of (a subclass of) Entry 
        """
        subclass = self.getSubclassForPath(path)
        if (subclass):
            return(subclass(model, path))
        else:
            return(None)



# Lifecycle
    def __init__(self, model, path):
        """Create new Entry from path.
        
        If model is None, the Image's identifiers are not initialized.
        """
        # inheritance
        super(Entry, self).__init__(['name', 'remove', 'children'])  # legal aspects to observe
        # internal state
        self.model = model  
        self.parentGroup = None  
        self.filteredFlag = False  # initially, no entry is filtered
        self.treeItemID = None  # not inserted into MediaTreePane yet
        self.bitmap = None
        #path = self.fixNumber(path)
        self.initFromPath(path)
        Logger.debug('Entry(): Created %s' % self)


    def initFromPath(self, path):
        """Initialize instance variables which depend on self's path, including self's MediaOrganization.
        """
        self.setPath(os.path.normpath(path))
        (directory, rest) = os.path.split(self.getPath())
        self.setDirectory(directory)
        (fname, extension) = os.path.splitext(rest)
        self.setFilename(fname)
        if (extension == ''):
            self.setExtension(extension)
        else:
            self.setExtension(extension[1:].lower())
        self.fileSize = self.getFileSize()
        if (self.isGroup() 
            and (self.getExtension() <> '')):
            print('Group "%s" should not use an extension' % self.getPath())
        elementStart = fname.find(MediaClassHandler.TagSeparator)
        if (0 <= elementStart):
            elements = fname[elementStart:]
            (known, unknown) = self.model.getClassHandler().stringToKnownAndUnknownElements(elements)
            self.setKnownElementsDictionary(known)
            self.setUnknownElements(unknown)
        else: 
            self.setKnownElementsDictionary({})
            self.setUnknownElements(set())
        self.organizer = self.model.organizationStrategy(self, path)



# Setters
    def setPath(self, path):
        self.filePath = unicode(path)


    def setDirectory(self, directory):
        self.fileDirectory = directory


    def setFilename(self, filename):
        self.fileFilename = filename


    def setExtension(self, extension):
        self.fileExtension = extension


    def setKnownElementsDictionary(self, aDictionary):
        self.knownElementsDictionary = aDictionary


    def setUnknownElements(self, aSet):
        self.unknownElements = aSet


    def setParentGroup(self, group, notifyObserversOfRemoval=True):
        """Add self to a Group. 
        
        Does also remove self from current parent and adds it to new group.
        If an Entry is removed, the current parent is notified via the 'remove' aspect. 
        To avoid double notifications, set notifyObserversOfRemoval to False.
        
        MediaFiler.Group group is the new parent of self
        Boolean notifyObserversOfRemoval indicates whether to notify observers of current parent about removal of self
        """
        if (self.parentGroup <> group):
            if (self.parentGroup <> None):
                self.parentGroup.removeEntryFromGroup(self, notifyObserversOfRemoval)
            self.parentGroup = group
            if (group <> None):
                group.addEntryToGroup(self)


    def setTreeItemID(self, treeItemID):
        if (not treeItemID):
            print('Entry.setTreeItemId(): Setting tree item ID to None for %s!' % self.getPath())
        self.treeItemID = treeItemID


    def setFilter(self, flag):
        """Set whether self is filtered
        
        Boolean flag
        """
        self.filteredFlag = flag


    def remove(self):  # TODO: inform MediaOrganization as well, to release names
        """Remove self from the image set. 
        
        Move the image file into the trash directory.
        """
        self.changedAspect('remove')
        self.setParentGroup(None)
        self.releaseCacheWithPriority(self.__class__.CachingLevelRawData)
        self.releaseCacheWithPriority(self.__class__.CachingLevelFullsizeBitmap)
        self.releaseCacheWithPriority(self.__class__.CachingLevelThumbnailBitmap)
        # move to trash
        oldName = self.getPath()
        newName = os.path.join(self.model.rootDirectory, 
                               Installer.getTrashPath(), 
                               (self.getFilename() + '.' + self.getExtension()))
        newName = makeUnique(newName)
        Logger.debug('Trashing "%s" (into "%s")' % (oldName, newName))
        try:
            os.rename(oldName, newName)
        except Exception as e: 
            Logger.error('Trashing "%s" failed:\n%s' % (oldName, e))


# Getters
    def __repr__(self):
        return('<%s from %s>' % (self.__class__.__name__, self.getPath()))


    def getModel(self):
        return(self.model)


    def isGroup(self):
        """Return true if self represents a Group.
        """
        return(False)


    def isFiltered(self):
        """Check whether self is filtered, i.e. shall not be shown.
        
        Return Boolean indicating that self is filtered.
        """
        return(self.filteredFlag)

        
    def isIdentical(self, anEntry):  # TODO: rename, as it's about content equality, not about identity
        """Check whether self and anEntry have the same content.
        
        Returns True iff self and anEntry are identical
        """
        return(self.__class__ == anEntry.__class__)


    def getPath(self):
        """Return the media's file path
        
        Returns a String
        """
        return(self.filePath)


    def getFilename(self):
        """Return the media's file name, without extension
        """
        return(self.fileFilename)
    

    def getDirectory(self):
        """Return the media's directory
        """
        return(self.fileDirectory)


    def getExtension(self):
        """Return the media's file extension, without '.'
        
        In no extension exists, the empty string is returned.
        
        Returns a String
        """
        return(self.fileExtension)


    def getFileSize(self):
        """Return the size of self's file, or 0 if no file associated.
        
        Return Number
        """
        return(0)


    def getOrganizer(self):
        """Return the MediaOrganization instance associated with self.
        
        Return MediaOrganization
        """
        return(self.organizer)


    def getOrganizationIdentifier(self):
        """Return the part of self's path which contains identifiers relevant for MediaOrganization.

        Removes the model root directory from the beginning and the final (non-directory) elements from the file path.
        
        Returns a String
        """
        pathRest = self.getPath()[(len(self.model.rootDirectory) + 1):]  # remove root directory, including slash
        if (0 < len(self.getExtension())):
            pathRest = pathRest[:-(1 + len(self.getExtension()))]  # remove extension (including .), if any
        match = re.search(r'''(\.[^\\]*)$     # from 1st dot in last file component to end of line
                          ''', 
                          pathRest, 
                          re.VERBOSE)
        if (match):
            return(pathRest[:-len(match.group(1))])  # remove matched part, containing elements
        else:
            return(pathRest)


    def getIdentifier (self):
        """Return a short identifier of self for use on the UI
        
        Returns a String 
        """
        elementStart = self.getFilename().find('.')
        if (0 <= elementStart):
            return(self.getFilename()[:elementStart])
        else:
            return(self.getFilename())


    def getKnownElementsDictionary(self):
        """Return a Dictionary mapping class names to lists of elements.
        """
        return(self.knownElementsDictionary)


    def getKnownElements(self, filtering=False):
        """Return a Set containing the Strings of all known elements.
        
        filtering is required as parameter as the subclass Group requires it. It has no significance here.
        
        Boolean filtering specifies whether to ignore filtered entries (in Group)
        """
        elements = set()
        classMap = self.getKnownElementsDictionary()
        for classname in classMap:
            elements.update(classMap[classname])
        return(elements)


    def getUnknownElements (self):
        """Return a Set containing the Strings of all unknown elements.
        """
        return(set(self.unknownElements))


    def getElements(self, filtering=False):
        """Return a Set containing all elements of self.
        
        filtering is required as parameter as the subclass Group requires it. It has no significance here.
        
        Boolean filtering specifies whether to ignore filtered entries (in Group)
        Returns Set of String
        """
        return(self.getKnownElements().union(self.getUnknownElements()))
    
    
    def getElementString (self, filtering=False):
        """Return a String containing all elements of self. 

        Boolean filtering specifies whether to ignore filtered entries (in Group)
        Return String
        """
        return(self.model.getClassHandler().elementsToString(self.getElements(filtering)))


    def getEntriesForDisplay (self):
        """Return the list of entries to represent self in an image display.
        If self is filtered, return an empty Array.
        
        Returns Array of Entry. 
        """
        raise NotImplementedError


    def getParentGroup(self):
        """
        """
        return(self.parentGroup)


    def getTreeItemID(self):
        """Return the wx.TreeItemID of self.
        """
        return(self.treeItemID)


    def getNextEntry(self, entry=None, filtering=False):  # @UnusedVariable
        """Return the next entry following self.
        
        Return MediaFiler.Entry or None
        """
        if (entry == None):
            entry = self
        if (self.getParentGroup()):
            return(self.getParentGroup().getNextEntry(entry, filtering))
        else:
            return(None)


    def getPreviousEntry(self, entry=None, filtering=False): 
        """Return the previous entry preceeding self.
        
        Return MediaFiler.Entry or None
        """
        if (entry == None):
            entry = self
        if (self.getParentGroup()):
            return(self.getParentGroup().getPreviousEntry(entry, filtering))
        else:
            return(None)


    def releaseCacheWithPriority(self, cachePriority):
        """
        """
        if (cachePriority == self.__class__.CachingLevelThumbnailBitmap):
            self.releaseBitmapCache()
        elif (cachePriority == self.__class__.CachingLevelFullsizeBitmap):
            pass
        elif (cachePriority == 2):
            self.releaseRawDataCache()


    def registerCacheWithPriority(self, cachePriority):
        """
        """
        if (cachePriority == self.__class__.CachingLevelThumbnailBitmap):
            CachingController.allocateMemory(self, self.getBitmapMemoryUsage(), cachePriority=cachePriority)
        elif (cachePriority == self.__class__.CachingLevelFullsizeBitmap):
            pass
        elif (cachePriority == 2):
            pass
            

    def getBitmap(self, width, height):  # @UnusedVariable
        """
        """
        print('Entry.getBitmap() deprecated')
        CachingController.allocateMemory(self, self.getBitmapMemoryUsage(), bitmap=True)
        return(self.bitmap)


    def getBitmapMemoryUsage(self):
        """Return self's current memory usage for the bitmap.
        
        Return Number of bytes used
        """
        if (self.bitmap <> None):
            return(self.bitmapWidth * self.bitmapHeight * 3)  # assumption
        else:
            return(0)


    def registerBitmapCache(self):
        """Register memory usage for self's bitmap.
        
        Boolean cacheAsThumbnail indicates 
        """
        CachingController.allocateMemory(self, self.getBitmapMemoryUsage(), bitmap=True)
    

    def releaseBitmapCache(self):
        """Release the memory alllocated for self's bitmap.
        """
        if (self.bitmap):
            logging.debug('Entry.releaseBitmapCache(): Discarding %dx%d bitmap' % (self.bitmapWidth, self.bitmapHeight))
            self.bitmap = None 
            self.bitmapWidth = 0
            self.bitmapHeight = 0
            CachingController.deallocateMemory(self, bitmap=True)



# Other API methods
    # @profiledOnLogger(Logger, sort='cumulative')
    def renameTo(self, **pathInfo):
        """Rename self's file, replacing the components as specified. 
       
        If a parameter is None or not given in pathInfo, leave it unchanged. 
        If makeUnique is True, find another number to ensure a unique filename.
        
        Dictionary pathInfo may contain the following keys:
            <organization-specific keys>
                String year, month, day 
                String name, scene 
            Number number 
            Boolean makeUnique 
            Set of String elements 
            Boolean removeIllegalElements
            Set of String classesToRemove contains the names of classes whose tags shall be removed
        Return the Entry to be shown after renaming
        """
        raise NotImplementedError
#         return(self.getOrganizer().renameSingle(elements=elements, removeIllegalElements=removeIllegalElements, **kwargs))


    def renameToFilename(self, fname):
        """Rename self's file to an absolute filename, register self with new parent, 
        and register new move-to-location.
        
        String fname is the new absolute filename
        Return Boolean indicating success
        
        Throws OSError if the file cannot be renamed.
        """
        Logger.debug('Entry.renameToFilename(): Renaming "%s"\n      to "%s"' % (self.getPath(), fname))
        (newDirectory, dummy) = os.path.split(fname)  # @UnusedVariable
        try:
            if (not os.path.exists(newDirectory)):
                os.makedirs(newDirectory)
            os.rename(self.getPath(), fname) 
        except Exception as e:
            Logger.error('Entry.renameToFilename(): Renaming "%s"\n      to "%s" failed (exception follows)!\n%s' % (self.getPath(), fname, e))
            raise e
        # remove from current group, and add to new group
        (head, tail) = os.path.split(fname)  # @UnusedVariable
        newGroup = self.getOrganizer().__class__.getGroupFromPath(head)
        self.initFromPath(fname)  # change name before changing parent: If parent group is shown, image needs to be retrieved
        if (newGroup <> self.getParentGroup()):
            self.setParentGroup(newGroup)
        self.changedAspect('name')
#         self.getOrganizer().__class__.registerMoveToLocation(fname)
        return(True)



# Event Handlers
    def getContextMenu(self):
        """Create a menu containing all context menu functions.
        
        SelectMoveTo is added here, but handled in MediaOrganization.runContextMenu()
        
        Return wx.Menu
        """
        menu = Menu()
        menu.currentEntry = self  # store current entry on menu, for access in menu event handlers
        # media functions
        menu.Append(GUIId.FilterIdentical, GUIId.FunctionNames[GUIId.FilterIdentical])
        menu.Append(GUIId.FilterSimilar, GUIId.FunctionNames[GUIId.FilterSimilar])
        # structure functions
        menu.AppendSeparator()
        moveToMenu = self.getOrganizer().__class__.constructMoveToMenu()
        menu.AppendMenu(GUIId.SelectMoveTo, 
                        GUIId.FunctionNames[GUIId.SelectMoveTo],
                        moveToMenu)
        if ((0 == moveToMenu.GetMenuItemCount())
            and (not self.isGroup())):
            menu.Enable(GUIId.SelectMoveTo, False)
        # group functions
        # delete functions
        menu.AppendSeparator()
        menu.Append(GUIId.DeleteImage, (GUIId.FunctionNames[GUIId.DeleteImage] % self.getIdentifier())) 
        # organization functions
        self.organizer.extendContextMenu(menu)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """User selected menuId from context menu on self. Execute this function.

        Number menuId from GUIId function numbers
        wx.Window parentWindow to open dialogs on
        Return String to display as status
            or None
        """
        message = None
        Logger.debug('Entry.runContextMenu(): Function %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.FilterIdentical):
            self.filterImages(True)
        elif (menuId == GUIId.FilterSimilar):
            self.filterImages(False)
        elif (menuId == GUIId.DeleteImage):
            self.remove()
        else: 
            message = self.getOrganizer().runContextMenuItem(menuId, parentWindow)
        return(message)


##### messy
    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        raise NotImplementedError


## Context Menu Functions
    def filterImages(self, identical):
        """Set the filter so that only images are visible which have the elements that self has. 
        Boolean IDENTICAL controls whether the filter shall exclude all elements not shared with self. 
        """
        print('Entry.filterImages(%s)' % identical)
        required = set()
        prohibited = set()
        unknown=False
        # for each element of self, require it
        for className in self.model.getClassHandler().getClassNames():
            classCovered = False  # no element of this class required yet
            for element in self.model.getClassHandler().getElementsOfClassByName(className):
                if element in self.getKnownElements():
                    required.add(element)
                    classCovered = True  # element of this class is required
            if (identical  
                and (not classCovered)):  # no element of this class is required, so prohibit the class
                prohibited.add(className)
        # for identical filtering, check unknown elements as well
        if (identical
            and (len(self.getUnknownElements()) > 0)):
            unknown = True
        # turn on filter
        print('(Identical=%s) Filtering required %s, prohibited %s, unknown %s)' % (identical, required, prohibited, unknown))
        self.model.getFilter().setConditions(active=True,
                                             required=required, 
                                             prohibited=prohibited, 
                                             unknownRequired=unknown)


    def removeNewIndicator(self):
        """Remove the new indicator from self's filename.
        """
        raise NotImplementedError


