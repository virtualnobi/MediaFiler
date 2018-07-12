"""Class MediaFiler.Group

(c) by nobisoft 2015-
"""


# Imports
## standard
import logging
import os
import copy
## contributed
import wx
from nobi.SortedCollection import SortedCollection 
## nobi
from nobi.PausableObservable import PausableObservable
from nobi.ObserverPattern import Observer
## project
import Installer
from .Entry import Entry
from UI import GUIId



# Class 
class Group(Entry, Observer):
    """A Group is an Observable representing an image folder. 
    
    It also observes its children for name changes.
    Group registers with Installer.getProductTrader() to handle directories.
    """



# Constants
    Logger = logging.getLogger(__name__)
    PreviewImageFilename = 'Group.jpg'



# Class Variables
# Class Methods
    @classmethod
    def createAndPersist(cls, model, **kwargs):
        """Create a new Group including its directory and link it to its parent.
        
        MediaCollection model
        Dictionary kwargs either contains String path, or parameters for MediaOrganization.constructPath()
        Returns a Group
        """
        if ('path' in kwargs):
            path = kwargs['path']
        else:
            path = model.organizationStrategy.constructPath(kwargs)
        cls.Logger.debug('Group.createAndPersist(): New group for "%s"' % path)
        newGroup = Group(model, path)
        parent = model.organizationStrategy.findParentForPath(path)
        cls.Logger.debug('Group.createAndPersist(): Parent found at "%s"' % parent.getPath())
        newGroup.setParent(parent)
        cls.Logger.debug('Group.createAndPersist(): Creating directory "%s"' % path)
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
            logging.warning('Group.removeEntryFromGroup(): Cannot find "%s" in subentries of "%s"' % (entry.getPath(), self.getPath()))
            index = self.subEntriesSorted._items.index(entry)
            del self.subEntriesSorted._items[index]
            del self.subEntriesSorted._keys[index]
        entry.removeObserver(self)
        if (notifyObservers):
            self.changedAspect('children')
    
    
    def remove(self):  # TODO: remove subentries individually for correct MediaCollection size
        # TODO: inform MediaOrganization as well, to release names
        """
        """
        super(Group, self).remove()



    def renameTo(self, **kwargs):
        """Rename a Group of Entrys. See Entry.renameTo()
        
        Will create new group if organizing name parts (such as name, scene, day, month, year) are changed. 
        Then renames subentries according to tag changes, possibly moving to new group.
        If remaining group, self, is empty after the move, it will be removed. 
        """
        if ('number' in kwargs):
            if (kwargs['number']):
                raise ValueError, 'Group.renameTo(): No number parameter allowed!'
            del kwargs['number']
        tagParameters = set(['elements', 'removeIllegalElements', 'classesToRemove'])  # kwargs keys which affect tags of subentries
        if (0 < len(set(kwargs.keys()).difference(tagParameters))):  # more to change than only tags, rename group
            newSelection = self.getOrganizer().renameGroup(**kwargs)
            if (0 == len(self.getSubEntries(filtering=False))):  # remove self
                if (self.model.getSelectedEntry() == self):
                    self.model.setSelectedEntry(entry=newSelection)
                self.remove()
        else:  # change only tags of subentries
            for entry in self.getSubEntries(filtering=True):
                newKwargs = copy.copy(kwargs)
                if (('elements' in kwargs)
                    and (kwargs['elements'])):
                    newElements = entry.getElements().union(kwargs['elements'])
                    newKwargs['elements'] = newElements
                entry.renameTo(**newKwargs)
        return(True)
        # old stuff
#         result = True
#         selfToBeDeleted = False
#         removeIllegalElements = (kwargs['removeIllegalElements'] if 'removeIllegalElements' in kwargs else None)
#         classesToRemove = (kwargs['classesToRemove'] if 'classesToRemove' in kwargs else set())
#         if (self.model.organizedByDate):  # TODO: move to OrganizationByDate
#             newSelection = self.getOrganizer().renameGroup(**kwargs)
# #             # ensure new group exists
# #             year = (kwargs['year'] if 'year' in kwargs else None)
# #             month = (kwargs['month'] if 'month' in kwargs else None)
# #             day = (kwargs['day'] if 'day' in kwargs else None)
# #             if ((year <> self.organizer.getYear())
# #                 or (month <> self.organizer.getMonth())
# #                 or (day <> self.organizer.getDay())):
# #                 selfToBeDeleted = True
# #                 if (not self.model.getEntry(year=year, month=month, day=day)):
# #                     newPath = self.model.organizationStrategy.constructPath(**kwargs)
# #                     newParent = Group(self.model, newPath)
# #                     if (not newParent):
# #                         logging.error('Group.renameTo(): Cannot create new Group "%s"' % newPath)
# #                         return(False)
# #             # move subentries to new group
# #             for subEntry in self.getSubEntries(filtering=True):
# #                 newElements = subEntry.getElements().union(elements)
# #                 result = (result 
# #                           and subEntry.renameTo(classesToRemove=classesToRemove, 
# #                                                 elements=newElements, 
# #                                                 **kwargs))
#         else:  # organized by name  TODO: move to OrganizationByName
#             if (('name' in kwargs)
#                 and (kwargs['name'] <> self.organizer.getName())):
#                 name = kwargs['name']
#                 existingEntry = self.model.getEntry(name=name)
#                 if (existingEntry == None):
#                     if ('elements' in kwargs):
#                         elements = kwargs['elements']
#                     else: 
#                         elements = ''
#                     print('No entry "%s" exists, renaming "%s" (ignoring elements "%s")' % (name, self.organizer.getName(), elements))
#                     return(super(Group, self).renameTo(classesToRemove=classesToRemove,
#                                                        name=name, 
#                                                        removeIllegalElements=removeIllegalElements))
#                 elif (existingEntry.isGroup()):
#                     print('Group "%s" exists' % name)
#                     newParent = existingEntry
#                     selfToBeDeleted = True
#                 else:  # existingEntry is a Single
#                     print('Single "%s" exists' % name)
#                     newParent = Group.createAndPersist(self.model, name=name)
#                     existingEntry.renameTo(classesToRemove=classesToRemove,
#                                            name=name, 
#                                            scene='1', 
#                                            makeUnique=True)
#                     selfToBeDeleted = True
#                 print('Moving subentries from "%s"\n                     to "%s"' % (self.getPath(), newParent.getPath()))
#                 # construct mapping from scenes in current group to scenes in existing target group
#                 sceneMap = {}
#                 nextFreeScene = (len(newParent.getOrganizer().getScenes()) + 1)
#                 if ('99' in newParent.getOrganizer().getScenes()):
#                     nextFreeScene = (nextFreeScene - 1)
#                 if (MediaClassHandler.ElementNew in newParent.getOrganizer().getScenes()):
#                     nextFreeScene = (nextFreeScene - 1)
#                 for scene in self.getOrganizer().getScenes():
#                     if (scene == MediaClassHandler.ElementNew):
#                         sceneMap[MediaClassHandler.ElementNew] = MediaClassHandler.ElementNew
#                     else:
#                         sceneMap[scene] = ('%02d' % nextFreeScene) 
#                         nextFreeScene = (nextFreeScene + 1)
#             else:
#                 print('Renaming subentries of "%s" (name unchanged)' % self.getPath())
#                 if ('name' in kwargs):
#                     del kwargs['name']
#                 # construct an identity scene map
#                 sceneMap = {}
#                 for scene in self.getOrganizer().getScenes():
#                     sceneMap[scene] = scene
#             print('   with scene mapping %s' % sceneMap)
#             # move each subEntry
#             print('   %d subentries' % len(self.subEntriesSorted))
#             for subEntry in self.getSubEntries(filtering=False):  
#                 newElements = subEntry.getElements()
#                 if (('elements' in kwargs)
#                     and (kwargs['elements'])):
#                     newElements = (newElements.union(kwargs['elements']))
#                 if (removeIllegalElements):
#                     newElements.remove(subEntry.getUnknownElements())
#                 kwargs2 = kwargs.copy()
#                 kwargs2['elements'] = newElements
#                 kwargs2['scene'] = sceneMap[subEntry.getOrganizer().getScene()]
#                 kwargs2['removeIllegalElements'] = removeIllegalElements
#                 kwargs2['number'] = subEntry.getOrganizer().getNumber()
#                 kwargs2['classesToRemove'] = classesToRemove
#                 newParent = subEntry.renameTo(**kwargs2)
#             newSelection = newParent
#         assert (selfToBeDeleted == (0 == len(self.getSubEntries(filtering=False)))), 'Group.renameTo(): Mismatch between subentry and deletion flag!'
#         if (0 == len(self.getSubEntries(filtering=False))):
#             if (self.model.getSelectedEntry() == self):
#                 self.model.setSelectedEntry(entry=newSelection)
#             self.remove()
#         return(result)


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


    def getKnownElements (self):
        """Return a Set of all known elements of self.
        
        Return Set of String.
        """
        result = None
        for subEntry in self.getSubEntries(filtering=False):
            if (result == None):  # first iteration
                result = set(subEntry.getKnownElements())
            else:
                result.intersection_update(subEntry.getKnownElements())
        if (result == None):
            return(set())
        else:
            return(result)
    
    
    def getUnknownElements (self):
        """Return all unknown elements of self.
        
        Return Set of String
        """
        result = None
        for subEntry in self.getSubEntries(filtering=False):
            if (result == None):  # first iteration
                result = set(subEntry.getUnknownElements())
            else:
                result.intersection_update(subEntry.getUnknownElements())
        if (result == None):
            return(set())
        else:
            return(result)


    def getScenes(self):  # TODO: remove
        """Return a sorted list of scenes.
        
        Return List of String
        """
        print('Group.getScenes() deprecated!')
        return(self.getOrganizer().getScenes())


    def getSizeString(self):
        """Return a String describing the size of self.
        
        Return a String
        """
        return(GUIId.TextGroupSizeString % self.getGroupedMedia())


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
            index = self.subEntriesSorted.index(entry)
            if (filtering):
                while ((self.subEntriesSorted[index].isFiltered()) 
                       and (0 < index)): 
                    index = (index - 1)
            if (0 < index):
                prevEntry = self.subEntriesSorted[index - 1]
                if (prevEntry.isGroup()):
                    prevEntry = prevEntry.getLastEntry(filtering)
                return(prevEntry)
            else:
                return(super(Group, self).getPreviousEntry(self, filtering))
        else:
            return(super(Group, self).getPreviousEntry(self, filtering))


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
        menu.Insert(4, GUIId.RemoveNew, GUIId.FunctionNames[GUIId.RemoveNew])
        # delete functions
        menu.insertAfterId(GUIId.DeleteImage, newText=GUIId.FunctionNames[GUIId.DeleteDoubles], newId=GUIId.DeleteDoubles)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions from the context menu.

        Number menuId is one of the GUIId function numbers
        wx.Window parentWindow to open dialogs on
        Return String to display as status
            or None
        """
        print('Group.runContextMenu(): %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.DeleteDoubles):
            wx.BeginBusyCursor()
            deleted = self.deleteDoubles()
            wx.EndBusyCursor()
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
    def deleteDoubles(self, mergeElements=True):
        """Remove double Singles contained in self. Recurse if self contains groups.
        
        Boolean mergeElements indicates that elements from both doubles shall be merged into remaining name
        Return Number indicating how many doubles were deleted. 
        """
        PausableObservable.pauseUpdates(Entry, 'name', None)
        doubles = 0
        for entry1 in self.subEntriesSorted[:]:
            if (entry1.isGroup()):
                doubles = (doubles + entry1.deleteDoubles())
            else:
                for entry2 in self.subEntriesSorted[:]:
                    if (entry2.isGroup()):
                        pass
                    elif (entry1 == entry2):
                        break  # avoid checking pairs twice
                    elif (entry1.isIdentical(entry2)):
                        #print('Identical entries: "%s" and "%s"' % (entry1.getPath(), entry2.getPath()))
                        entry1.getOrganizer().deleteDouble(entry2, mergeElements)
                        doubles = (doubles + 1)
        PausableObservable.resumeUpdates(Entry, 'name', None)
        #TODO: if self was selected, reselect to make changes visible
        return(doubles)


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
    def getGroupedMedia(self):
        """Return the number of media grouped in self.

        Return Number
        """
        result = 0
        for subEntry in self.getSubEntries(filtering=True):
            if (subEntry.__class__ == Group):
                result = (result + subEntry.getGroupedMedia())
            else:
                result = (result + 1) 
        return(result)



# Class Initialization
Installer.getProductTrader().registerClassFor(Group, Entry.SpecificationGroup)  # register Group to handle directories
