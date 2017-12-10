"""
(c) by nobisoft 2015-
"""


# Imports
## Standard
import re
import os.path
import logging
import datetime
## Contributed
## nobi
from nobi.PausableObservable import PausableObservable
from nobi.wx.Menu import Menu
## Project
from UI import GUIId
import Installer
from Model.CachingController import CachingController



# Class 
class Entry(PausableObservable):
    """An Entry is an PausableObservable representing either an image or a group of the image tree. 
    A group can either be a folder (based on directory structure) or be based on special naming of image files.
    
    The filename of the entry consists of its path, its name, and its extension.
    The name of the entry consists of its identifier, its known elements, and its unknown elements.
    The identifier is the date (if the model is organized by date) 
    or the name (if the model is organized by name) (for singleton images, not contained in a Group) 
    or the scene and image number (for images contained in a Group).

    ObserverPattern aspects
    - name: The file name on disk has changed
    - remove: The entry is deleted
    - children: The children of an entry group have changed

    Pausing updates is used in batch commands like the deletion of doubles.
    """



# Constants
    SpecificationGroup = 'directory'  # Specification for ProductTrader, registering to handle directories
    NameSeparator = '.'  # character separating image elements in file name
    IdentifierSeparator = '-'  # character separating scene, day, month, year, number in file name
    RESeparatorsRecognized = ('[, _' + NameSeparator + IdentifierSeparator + ']')
    CachingLevelThumbnailBitmap = 0
    CachingLevelFullsizeBitmap = 1
    CachingLevelRawData = 2



# Class Variables    
# Class Methods
    @classmethod
    def isLegalExtension(self, extension):
        """Check whether extension denotes a file type which is handled by Entry or its subclasses.
        
        String extension is the file name extension (upper and lower case handled)
        
        Return a Boolean indicating whether extension is handled by Entry
        """
        try:
            Installer.getProductTrader().getClassFor(extension.lower())
        except:  # no class registered for this extension
            return(False)
        return(True)


    @classmethod
    def createInstance(self, model, path):
        """Return an instance of (a subclass of) Entry to represent the file at path, using model.

        BaseException when no subclass of Entry registered to handle the file type
        
        model imageFilerModel
        path String
        Returns an instance of (a subclass of) Entry 
        """
        clas = None
        # determine which class to instantiate
        if (os.path.isdir(path)):
            clas = Installer.getProductTrader().getClassFor(self.SpecificationGroup)
        else:
            (dummy, extension) = os.path.splitext(path) 
            extension = extension[1:].lower()  # remove leading '.'
            try:
                clas = Installer.getProductTrader().getClassFor(extension)
            except:  # probably extension has no class registered to handle it
                logging.error('Entry.createInstance(): No class registered to instantiate "%s" media "%s"!' % (extension, path))
                return(None)
        # instantiate
        return(clas(model, path))



# Lifecycle
    def __init__(self, model, path):
        """Create new Entry from path.
        
        If model is None, the Image's identifiers are not initialized.
        """
        #path = self.fixNumber(path)
        # inheritance
        super(Entry, self).__init__(['name', 'remove', 'children'])  # legal aspects to observe
        # internal state
        self.model = model  # store creator for later reference
        self.parentGroup = None  # not known yet
        self.filteredFlag = False  # initially, no entry is filtered
        self.treeItemID = None  # not inserted into MediaTreePane yet
        self.bitmap = None
        self.initFromPath(path)


    def initFromPath(self, path):
        """Initialize instance variables which depend on self's path, including self's MediaOrganization.
        """
        self.setPath(os.path.normpath(path))
        (directory, rest) = os.path.split(self.getPath())
        self.setDirectory(directory)
        (rest, extension) = os.path.splitext(rest)
        if (extension == ''):
            self.setExtension(extension)
        else:
            self.setExtension(extension[1:].lower())
        self.fileSize = self.getFileSize()
        if (self.isGroup() 
            and (self.getExtension() <> '')):
            print('Group "%s" should not use an extension' % self.getPath())
        self.setFilename(rest)
        elementStart = rest.find(self.NameSeparator)
        if (0 <= elementStart):
            elements = rest[elementStart:]
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
            pass
        self.treeItemID = treeItemID


    def setFilter(self, flag):
        """Set whether self is filtered
        
        Boolean flag
        """
        self.filteredFlag = flag


    def remove(self):
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
        count = 1  # TODO: re-use MediaOrganization function?
        while (os.path.exists(newName)):
            newName = os.path.join(self.model.rootDirectory,
                                   Installer.getTrashPath(),  # self.TrashDirectory,
                                   (self.getFilename() + '-' + str(count) + '.' + self.getExtension()))
            count = (count + 1)
        print ('Trashing "%s" (into "%s")' % (oldName, newName))
        try:
            os.rename(oldName, newName)
        except Exception as e: 
            print('Trashing failed: %s' % e)


    def renameTo(self, 
                 year=None, month=None, day=None, 
                 name=None, scene=None, 
                 number=None, makeUnique=False,
                 elements=None, removeIllegalElements=False):
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
        Return Boolean indicating success
        """
        if (str(year)
            or unicode(year)):
            print('Entry.renameTo(): Deprecated usage of String year!')
            year = int(year)
        if (str(month) 
            or unicode(month)):
            print('Entry.renameTo(): Deprecated usage of String month!')
            month = int(month)
        if (str(day) 
            or unicode(day)):
            print('Entry.renameTo(): Deprecated usage of String day!')
            day = int(day)
        if (str(scene) 
            or unicode(scene)):
            print('Entry.renameTo(): Deprecated usage of String scene!')
            scene = int(scene)
        if (str(number) 
            or unicode(number)):
            print('Entry.renameTo(): Deprecated usage of String number!')
            number = int(number)
        if (removeIllegalElements):
            elements = filter(self.model.getClassHandler().isLegalElement, elements)
#         if (removeClasses):
#             for clas in removeClasses
        kwargs = {'rootDir': self.model.rootDirectory,
                  'makeUnique': makeUnique,
                  'extension': self.getExtension(),
                  'elements': self.model.getClassHandler().elementsToString(elements),
                  'removeIllegalElements': removeIllegalElements}
        if (year): 
            kwargs['year'] = year
        if (month):
            kwargs['month'] = month
        if (day):
            kwargs['day'] = day
        if (name):
            kwargs['name'] = name
        if (scene):
            kwargs['scene'] = scene
        if (number): 
            kwargs['number'] = number
        newPath = self.organizer.constructPathForSelf(**kwargs) 
        return(self.renameToFilename(newPath))


    def renameToFilename(self, fname):
        """Rename self's file to an absolute filename, register self with new parent, 
        and register new move-to-location.
        
        String fname is the new absolute filename
        Return Boolean indicating success
        """
        print('Renaming "%s"\n      to "%s"' % (self.getPath(), fname))
        (newDirectory, dummy) = os.path.split(fname)  # @UnusedVariable
        try:
            if (not os.path.exists(newDirectory)):
                os.makedirs(newDirectory)
            os.rename(self.getPath(), fname) 
        except Exception as e:
            print('Renaming failed (exception follows)!\n%s' % e)
            return(False)
        else:
            # remove from current group, and add to new group
            (head, tail) = os.path.split(fname)  # @UnusedVariable
            newGroup = self.organizer.__class__.getGroupFromPath(head)
            if (newGroup <> self.getParentGroup()):
                self.setParentGroup(newGroup)
            self.initFromPath(fname)  # name must be changed last, otherwise the Group will not find its subentry
            self.changedAspect('name')
            self.organizer.__class__.registerMoveToLocation(fname)
            return(True)



# Getters
    def isGroup(self):
        """Return true if self represents a Group.
        """
        return(False)


    def isFiltered(self):
        """Check whether self is filtered, i.e. shall not be shown.
        
        Return Boolean indicating that self is filtered.
        """
        return(self.filteredFlag)

        
    def isIdentical(self, anEntry):
        """Check whether self and anEntry have the same content.
        
        Returns True iff self and anEntry are identical
        """
        #print('isIdentical(%s, %s)' % (self.getPath(), anEntry.getPath()))
        return(self == anEntry) 


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


    def getNumber(self):
        """Return the number of self.
        """
        return(self.organizer.getNumber())


    def getKnownElementsDictionary(self):
        """Return a Dictionary mapping class names to lists of elements.
        """
        return(self.knownElementsDictionary)


    def getKnownElements(self):
        """Return a Set containing the Strings of all known elements.
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


    def getElements(self):
        """Return a Set containing all elements of self.
        
        Returns Set of String
        """
        return(self.getKnownElements().union(self.getUnknownElements()))
    
    
    def getElementString (self):
        """Return a String containing all elements of self. 
        
        Contains a leading NameSeparator if non-empty.
        
        Returns a String
        """
        return(self.model.getClassHandler().elementsToString(self.getElements()))


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
        if (not self.treeItemID):
            pass
        return(self.treeItemID)


    def getNextEntry(self, entry=None):  # @UnusedVariable
        """Return the next entry following self.
        
        Return MediaFiler.Entry or None
        """
        if (entry == None):
            entry = self
        if (self.getParentGroup()):
            return(self.getParentGroup().getNextEntry(entry))
        else:
            return(None)


    def getPreviousEntry(self, entry=None): 
        """Return the previous entry preceeding self.
        
        Return MediaFiler.Entry or None
        """
        if (entry == None):
            entry = self
        if (self.getParentGroup()):
            return(self.getParentGroup().getPreviousEntry(entry))
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



## Getters for organization by name
    def getName(self):
        """Return the name.
        
        Returns a String
        """
        print('Entry.getName() deprecated!')
        return(self.organizer.getName())


    def getScene(self):
        """Return the scene, either a number or the new indicator.
        
        Return a String
        """
        print('Entry.getScene() deprecated!')
        return(self.organizer.getScene())


    def isSingleton(self):
        """Return whether self is a singleton, i.e., a named Single outside of named Group.
        
        Returns a Boolean
        """ 
        print('Entry.isSingleton() deprecated!')
        return(self.organizer.isSingleton())


## Getters for organization by date
    def getYear(self):
        """Return the year.
        
        Return a String
        """
        print('Entry.getYear() deprecated')
        return(self.organizer.getYear())


    def getMonth(self):
        """Return the month.
        
        Return a String
        """
        print('Entry.getMonth() deprecated')
        return(self.organizer.getMonth())


    def getDay(self):
        """Return the day.
        
        Return a String
        """
        print('Entry.getDay() deprecated')
        return(self.organizer.getDay())


    def getDate(self):
        """Return the date the media was captured.
        
        Return datetime.date
        """
        print('Entry.getDate() deprecated')
        return(datetime.date(int(self.getYear()), int(self.getMonth()), int(self.getDay())))



# Event Handlers
    def getContextMenu(self):
        """Create a menu containing all context menu functions.
        
        Return wx.Menu
        """
        menu = Menu()
        menu.currentEntry = self  # store current entry on menu, for access in menu event handlers
        # organization functions
        self.organizer.extendContextMenu(menu)
        # media functions
        menu.AppendSeparator()
        # view functions
        menu.AppendSeparator()
        menu.Append(GUIId.FilterIdentical, GUIId.FunctionNames[GUIId.FilterIdentical])
        menu.Append(GUIId.FilterSimilar, GUIId.FunctionNames[GUIId.FilterSimilar])
        # delete function
        menu.AppendSeparator()
        menu.Append(GUIId.DeleteImage, (GUIId.FunctionNames[GUIId.DeleteImage] % self.getIdentifier())) 
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """User selected menuId from context menu on self. Execute this function.

        Number menuId from GUIId function numbers
        wx.Window parentWindow to open dialogs on
        Return String to display as status
            or None
        """
        message = None
        logging.debug('Entry.runContextMenu(): Function %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.FilterIdentical):
            self.filterImages(True)
        elif (menuId == GUIId.FilterSimilar):
            self.filterImages(False)
        elif (menuId == GUIId.DeleteImage):
            self.remove()
        elif (menuId == GUIId.RemoveNew):
            self.removeNewIndicator()
        else: 
            message = self.organizer.runContextMenuItem(menuId, parentWindow)
        return(message)


##### messy
    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
#        raise NotImplementedError
        return('')


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


