"""Class MediaFiler.Group

(c) by nobisoft 2015-
"""


# Imports
## standard
import logging
import os
## contributed
import wx
from nobi.SortedCollection import SortedCollection 
## nobi
from nobi.ObserverPattern import Observer
## project
from Model import Installer
from Model.Entry import Entry
from UI import GUIId



# Package variables
Logger = logging.getLogger(__name__)


# Class 
class Group(Entry, Observer):
    """A Group is an Observable representing an image folder. 
    
    It also observes its children for name changes.
    Group registers with Installer.getProductTrader() to handle directories.
    """



# Constants
    PreviewImageFilename = 'Group.jpg'



# Class Variables
# Class Methods
    @classmethod
    def createAndPersist(cls, model, **pathInfo):
        """Create a new Group including its directory and link it to its parent.
        
        MediaCollection model
        Dictionary pathInfo either contains String path, or parameters for MediaOrganization.constructPath()
        Returns a Group
        """
        # TODO: turn MediaCollection into Singleton, and remove model parameter
        correctedPathInfo = pathInfo.copy()
        if ('elements' in correctedPathInfo):
            del correctedPathInfo['elements']
        if ('path' in correctedPathInfo):
            path = correctedPathInfo['path']
        else:
            path = model.organizationStrategy.constructPath(**correctedPathInfo)
        Logger.debug('Group.createAndPersist(): Creating group for "%s"' % path)
        newGroup = Group(model, path)
        parent = model.organizationStrategy.findParentForPath(path)
        Logger.debug('Group.createAndPersist(): Found parent "%s"' % parent.getPath())
        newGroup.setParentGroup(parent)
        Logger.debug('Group.createAndPersist(): Creating directory "%s"' % path)
        os.mkdir(path)
        return(newGroup)



# Lifecycle
    def __init__(self, model, path):
        # inheritance
        super(Group, self).__init__(model, path)
        super(Observer, self).__init__()
        # internal state
        self.subEntriesSorted = SortedCollection(key=Entry.getPath)
        # TODO: have subentries sorted with Entrys first, then Groups. 
        # depends on organization: by name wants groups and singles ordered as one.
        # - idea 1 - manage list with custom sort function
        # - idea 2 - keep SortedCollections for Entry and Group separately



# Setters
    def addEntryToGroup(self, entry):
        """Add photoFilerEntry entry to self's collection.
        """
        self.subEntriesSorted.insert(entry)
        entry.addObserverForAspect(self, 'name')
        self.changedAspect('children')


    def removeEntryFromGroup(self, entry, notifyObservers=True):
        """Remove an Entry from self.
        
        When removing an Entry, its parent Group will also change its children. 
        To avoid double changes, set notifyObservers to False.
        
        MediaFiler.Entry entry the subentry of self to remove. 
        Boolean notifyObservers indicates whether to notify self's Observers.
        """
        try:
            self.subEntriesSorted.remove(entry)
        except:
            # catch the case when entry has changed its path:
            # subEntriesSorted._keys is not updated and entry is not found
            Logger.warning('Group.removeEntryFromGroup(): Cannot find "%s" in subentries of "%s"' % (entry.getPath(), self.getPath()))
            index = self.subEntriesSorted._items.index(entry)
            del self.subEntriesSorted._items[index]
            del self.subEntriesSorted._keys[index]
        entry.removeObserver(self)
        if (notifyObservers):
            self.changedAspect('children')
    
    
    def remove(self):  # TODO: remove subentries individually for correct MediaCollection size
        """
        """
        parent = self.getParentGroup()  # parent is unlinked in superclass implementation
        super(Group, self).remove()
        # check if parent still has subentries
        if (0 == len(parent.getSubEntries())):
            parent.remove()



    def renameTo(self, processIndicator=None, **kwargs):
        """Rename a Group of Entrys. See Entry.renameTo()
        
        Will create new group if organizing name parts (such as name, scene, day, month, year) are changed. 
        Then renames subentries according to tag changes, possibly moving to new group.
        If remaining group (self) is empty after the move, it will be removed. 
        """
        return(self.getOrganizer().renameGroup(processIndicator=processIndicator, filtering=True, **kwargs))


# Getters
    def isGroup (self):
        """Indicates self represents a group of images.
        """ 
        return(True)

    
    def getSubEntries(self, filtering=True):
        """Return the list of all child entries.
        
        Boolean filtering if True, no filtered subentry is returned        
        Return List of Entry
        """
        if (filtering):
            result = [entry for entry in self.subEntriesSorted if (not entry.filteredFlag)]
        else:
            result = [entry for entry in self.subEntriesSorted]
        return(result)


    def getKnownTags (self, filtering=False):
        """Return a Set of all known elements of self.
        
        Return Set of String.
        """
        result = None
        for subEntry in self.getSubEntries(filtering=filtering):
            if (result == None):  # first iteration
                result = set(subEntry.getKnownTags(filtering=filtering))
            else:
                result.intersection_update(subEntry.getKnownTags(filtering=filtering))
        if (result == None):
            return(set())
        else:
            return(result)
    
    
    def getUnknownTags (self, filtering=False):
        """Return all unknown elements of self.
        
        Return Set of String
        """
        result = None
        for subEntry in self.getSubEntries(filtering=filtering):
            if (result == None):  # first iteration
                result = set(subEntry.getUnknownTags(filtering=filtering))
            else:
                result.intersection_update(subEntry.getUnknownTags(filtering=filtering))
        if (result == None):
            return(set())
        else:
            return(result)


    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        return(GUIId.TextGroupSizeString % self.getGroupSize())


    def isIdenticalContent(self, anEntry):
        """Check whether self and anEntry are identical.
        
        For Groups, do not check all subentries, just check object identity.
        
        Return Boolean indicating anEntry is identical to self.
        """
        return(self == anEntry)

    
    def getFirstEntry(self, filtering=False):
        """Return the first entry in self or its subgroups.
        
        Boolean filtering
        Return MediaFiler.Single or None
        """
        result = self
        while (result.isGroup()):
            subEntries = result.getSubEntries(filtering)
            if (0 < len(subEntries)):
                result = subEntries[0]
            else:
                return(None)
        return(result)


    def getLastEntry(self, filtering=False):
        """Return the last entry in self or its subgroups.
        
        Boolean filtering 
        Return MediaFiler.Single or None
        """
        result = self
        while (result.isGroup()):
            subEntries = result.getSubEntries(filtering)
            if (0 < len(subEntries)):
                result = subEntries[-1]
            else:
                return(None)
        return(result)


        
# Event Handlers
# Inheritance - Entry
    def getNextEntry(self, entry=None, filtering=False):
        """Return the next entry following entry.
        
        Return MediaFiler.Entry or None
        """
        if (entry):
            index = self.subEntriesSorted.index(entry)
            if (filtering):
                while ((self.subEntriesSorted[index].isFiltered()) 
                       and (index < (len(self.subEntriesSorted) - 1))):
                    index = (index + 1)
            if (index < (len(self.subEntriesSorted) - 1)):
                nextEntry = self.subEntriesSorted[index + 1]
                if (nextEntry.isGroup()):
                    nextEntry = nextEntry.getFirstEntry(filtering)
                return(nextEntry)
            else:
                return(super(Group, self).getNextEntry(self, filtering))
        else:
            return(super(Group, self).getNextEntry(self, filtering))


    def getPreviousEntry(self, entry=None, filtering=False):
        """Return the previous entry preceeding entry.
        
        Return MediaFiler.Entry or None
        """
        if (entry):
            index = (self.subEntriesSorted.index(entry) - 1)
            if (filtering):
                while ((0 < index)
                       and (self.subEntriesSorted[index].isFiltered())): 
                    index = (index - 1)
            if (0 <= index):  # previous entry is inside this group
                prevEntry = self.subEntriesSorted[index]
                if (prevEntry.isGroup()):
                    prevEntry = prevEntry.getLastEntry(filtering=filtering)
                return(prevEntry)
            else:  # previous entry is before this group
                return(super(Group, self).getPreviousEntry(self, filtering=filtering))
        else:
            return(super(Group, self).getPreviousEntry(self, filtering=filtering))


    def releaseCacheWithPriority(self, cachePriority):
        """Do nothing here as Groups do not cache data.
        """
        pass


    def registerCacheWithPriority(self, cachePriority):
        """Do nothing here as Groups do not cache data.
        """
        pass


    def getEntriesForDisplay (self):
        """Return all subentries to be displayed on the canvas. 

        If a subentry is a Group, choose a representative instead of returning all. 
        If filtering is on, return only unfiltered images.
        
        Returns Array of Entry.
        
        TODO: Change this to display the group representative on a folder background. 
        
        Can be done with Image:
        import urllib2

        from wand.image import Image
        from wand.display import display
        
        
        fg_url = 'http://i.stack.imgur.com/Mz9y0.jpg'
        bg_url = 'http://i.stack.imgur.com/TAcBA.jpg'
        
        bg = urllib2.urlopen(bg_url)
        with Image(file=bg) as bg_img:
            fg = urllib2.urlopen(fg_url)
            with Image(file=fg) as fg_img:
                bg_img.composite(fg_img, left=100, top=100)
            fg.close()
            display(bg_img)
        bg.close()
        """
        result = []
        if (not self.filteredFlag):
            # collect one entry from each subentry
            for subEntry in self.getSubEntries(True):
                subsubEntries = subEntry.getEntriesForDisplay()
                if (len(subsubEntries) > 0):
                    result.append(subsubEntries[0])
        return(result)


    def getContextMenu(self):
        """Return a MediaFiler.Menu containing all context menu functions for Singles.
        """
        menu = super(Group, self).getContextMenu()
        # media functions
        # structure functions
        # group functions
        # delete functions
        menu.insertAfterId(GUIId.DeleteImage, 
                           newText=GUIId.FunctionNames[GUIId.DeleteDoubles], 
                           newId=GUIId.DeleteDoubles)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions from the context menu.

        Number menuId is one of the GUIId function numbers
        wx.Window parentWindow to open dialogs on
        Return String to display as status
            or None
        """
        Logger.debug('Group.runContextMenu(): Running %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.DeleteDoubles):
            wx.GetApp().setInfoMessage('Removing duplicates...')  # _('Removing duplicates...')) # TODO: How to access translations from model classes?
            deleted = self.deleteDoubles(wx.GetApp().getProgressBar())
            return(GUIId.MessageDuplicatesDeleted % deleted)
        else:
            return(super(Group, self).runContextMenuItem(menuId, parentWindow))



# Inheritance: Observer
    def updateAspect(self, observable, aspect):  # @UnusedVariable
        """
        """
        if (aspect == 'name'):
            self.subEntriesSorted = SortedCollection(self.subEntriesSorted, key=Entry.getPath)



# Other API Functions
    def deleteDoubles(self, aProgressBar=None):
        """Remove double Singles contained in self. Recurse if self contains groups.
        
        nobi.wx.PhasedProgressBar aProgressBar displays progress if defined
        Return Number indicating how many doubles were deleted. 
        """
        deletionCount = 0
        subEntries1 = self.getSubEntries(filtering=False)
        if (aProgressBar):
            aProgressBar.beginPhase(len(subEntries1))
        for entry1 in subEntries1:
            if (aProgressBar):
                aProgressBar.beginStep()
            if (entry1.isGroup()):
                deletionCount = (deletionCount + entry1.deleteDoubles())
            else:
                subEntries2 = self.getSubEntries(filtering=False)
                for entry2 in subEntries2:
                    if (entry2.isGroup()):
                        pass  # entry1 is not a Group, so can't be a double
                    elif (entry1 == entry2):
                        break  # stop here to avoid checking pairs twice
                    elif (entry1.isIdenticalContent(entry2)):
                        #print('Identical entries: "%s" and "%s"' % (entry1.getPath(), entry2.getPath()))
                        if ((entry1.getParentGroup() == entry2.getParentGroup()) 
                            and (entry1.getOrganizer().getNumber() > entry2.getOrganizer().getNumber())):   
                            entry2.getOrganizer().deleteDouble(entry1)  # keep the entry with lower number
                        else:
                            entry1.getOrganizer().deleteDouble(entry2)
                        deletionCount = (deletionCount + 1)
        return(deletionCount)


    def removeNewIndicator(self):
        """Remove the new indicator on all subentries
        """
        for entry in self.getSubEntries():
            entry.removeNewIndicator()


    def renumberMedia(self, pairList):
        """Renumber media grouped in self according to pairList.
        
        List pairList contains pairs of numbers indicating the current and new number.
        """
        pass


# Internal - to change without notice
    def getGroupSize(self):
        """Return the number of media grouped in self.

        Return Number
        """
        result = 0
        for subEntry in self.getSubEntries(filtering=True):
            if (subEntry.__class__ == Group):
                result = (result + subEntry.getGroupSize())
            else:
                result = (result + 1) 
        return(result)



# Class Initialization
Installer.getProductTrader().registerClassFor(Group, Entry.SpecificationGroup)  # register Group to handle directories
