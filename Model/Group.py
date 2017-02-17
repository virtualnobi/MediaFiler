"""Class MediaFiler.Group

(c) by nobisoft 2015-
"""


# Imports
## standard
import copy
import os.path
## contributed
import wx
## nobi
## project
from .Entry import Entry
from UI import GUIId
#from symbol import except_clause
#import MediaFiler.Organization  



# Class 
class Group(Entry):
    """A Group is an Observable representing an image folder.
    
    Group registers with Entry.ProductTrader to handle directories.
    """



# Constants
    MessageDuplicatesDeleted = ('%d duplicate entries deleted')
    PreviewImageFilename = 'Group.jpg'



# Class Variables
# Class Methods
    @classmethod
    def createFromName(cls, model, name):
        """Create a new Group for name.
        
        model an imageFilerModel 
        name a String containing the path of the media file
        Returns a Group
        """
        if (model.organizedByDate):
            raise('Named Groups cannot be created when images are organized by date!')
        else:  # organized by name
            groupDirectory = os.path.join(model.rootDirectory, name[0:1], name)
            if (not os.path.exists(groupDirectory)):
                print('Creating new folder "%s"' % groupDirectory)
                os.makedirs(groupDirectory)
            newGroup = cls(model, groupDirectory)
            return(newGroup)



# Lifecycle
    def __init__(self, model, path):
        # inheritance
        super(Group, self).__init__(model, path)
        # internal state
        self.subEntries = []



# Setters
    def removeEntryFromGroup (self, entry):
        """Remove the photoFilerEntry entry from self's collection.
        """
        self.subEntries.remove(entry)
        self.changedAspect('children')
    
    
    def addEntryToGroup (self, entry):
        """Add photoFilerEntry entry to self's collection.
        """
        self.subEntries.append(entry)
        self.changedAspect('children')        



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
            result = []
            for entry in self.subEntries: 
                if (entry.isFiltered):
                    #print "%s filtered out" % entry.pathname
                    pass
                else:
                    result.append(entry)
        else:
            result = copy.copy(self.subEntries)
        result.sort(key=Entry.getPath)
        return(result)


    def getKnownElements (self):
        """Return a Set of all known elements of self.
           Returns Set of String.
        """
        result = set()
        for subEntry in self.subEntries:
            if (len(result) == 0):  # result empty = first iteration
                result = subEntry.getKnownElements()
            else:
                result.intersection_update(subEntry.getKnownElements())
        return(result)
    
    
    def getUnknownElements (self):
        """Return all unknown elements of self.
           Returns Set of String
        """
        result = set()
        for subEntry in self.subEntries:
            if (len(result) == 0):  # result empty = first iteration
                result = subEntry.getUnknownElements()
            else:
                result.intersection_update(subEntry.getUnknownElements())
        return(result)

    
    def getScenes(self): 
        """Return a sorted list of scenes.
        
        Return List of String
        """
        return(self.organizer.getScenes())


    def getSizeString(self):  # inherited from Entry
        """Return a String describing the size of self.
        
        Return a String
        """
        return('%d images' % len(self.subEntries))


    def getFirstEntry(self):
        """Return the first entry in self or its subgroups.
        
        Return MediaFiler.Single or None
        """
        result = self
        while (result.isGroup()):
            subEntries = result.getSubEntries(False)
            if (0 < len(subEntries)):
                result = subEntries[0]
            else:
                return(None)
        return(result)


    def getLastEntry(self):
        """Return the last entry in self or its subgroups.
        
        Return MediaFiler.Single or None
        """
        result = self
        while (result.isGroup()):
            subEntries = result.getSubEntries(False)
            if (0 < len(subEntries)):
                result = subEntries[-1]
            else:
                return(None)
        return(result)


        
# Event Handlers
# Inheritance - Entry
    def getNextEntry(self, entry):
        """Return the next entry following entry.
        
        Return MediaFiler.Entry or None
        """
        index = self.subEntries.index(entry)
        if (index < (len(self.subEntries) - 1)):
            nextEntry = self.subEntries[index + 1]
            if (nextEntry.isGroup()):
                nextEntry = nextEntry.getFirstEntry()
            return(nextEntry)
        else:
            return(super(Group, self).getNextEntry(self))


    def getPreviousEntry(self, entry):
        """Return the previous entry preceeding entry.
        
        Return MediaFiler.Entry or None
        """
        index = self.subEntries.index(entry)
        if (0 < index):
            prevEntry = self.subEntries[index - 1]
            if (prevEntry.isGroup()):
                prevEntry = prevEntry.getLastEntry()
            return(prevEntry)
        else:
            return(super(Group, self).getPreviousEntry(self))


    def getEntriesForDisplay (self):
        """Return all subentries to be displayed on the canvas. 

        If a subentry is a Group, choose a representative instead of returning all. 
        If filtering is on, return only unfiltered images.
        
        Returns Array of Entry.
        """
        result = []
        if (not self.isFiltered):
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
        menu.insertAfterId(GUIId.FilterSimilar, newText=GUIId.FunctionNames[GUIId.RemoveNew], newId=GUIId.RemoveNew)
        menu.insertAfterId(GUIId.FilterSimilar)
        menu.insertAfterId(GUIId.DeleteImage, newText=GUIId.FunctionNames[GUIId.DeleteDoubles], newId=GUIId.DeleteDoubles)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions from the context menu.

        Number menuId is one of the GUIId function numbers
        wx.Window parentWindow to open dialogs on
        Return String to display as status
            or None
        """
        print('Group.runContextMenu: %d on "%s"' % (menuId, self.getPath()))
        if (menuId == GUIId.DeleteDoubles):
            wx.BeginBusyCursor()
            deleted = self.deleteDoubles()
            wx.EndBusyCursor()
            return(self.MessageDuplicatesDeleted % deleted)
        else:
            return(super(Group, self).runContextMenuItem(menuId, parentWindow))



# Other API Functions
    def renameTo(self, year=None, month=None, day=None,  # @UnusedVariables
                       name=None, scene=None, 
                       number=None, elements=None, removeIllegalElements=False):
        """Rename self.
        """
        if (number
            and (number <> '')):
            print('Group.renameTo(): No number allowed!')
            return
        # TODO: reorganize to find new group (1) if existing, insert (2) if single exists, merge (3) if not existing, create
        if (self.model.organizedByDate):
            if (((year == None)
                 or (year == u'')
                 or (year == self.organizer.getYear()))
                and ((month == None)
                     or (month == u'')
                     or (month == self.organizer.getMonth()))
                and ((day == None)
                     or (day == u'')
                     or (day == self.organizer.getDay()))):
                for subEntry in self.subEntries:
                    newElements = subEntry.getElements().union(elements)
                    subEntry.renameTo(year=year, month=month, day=day, elements=newElements, removeIllegalElements=removeIllegalElements)
                return
            else:
                newGroup = self.model.getEntry(year=year, month=month, day=day)
                if (newGroup):
                    print('NYI: Group.renameTo() cannot move from date group to date group')
                else:
                    print('NYI: Group.renameTo() cannot create new groups')
        else:  # organized by name
            if (scene):
                print('Group.renameTo(): No scene allowed')
                return
            newGroup = self.model.getEntry(name=name) 
            if (newGroup):  # group with NAME exists
                print('Moving subentries from "%s"\n                     to "%s"\n' % (self.getPath(), newGroup.getPath()))
                # construct mapping from scenes in current group to scenes in existing target group
                sceneMap = {}
                nextFreeScene = (len(newGroup.getScenes()) + 1)  # TODO: ignore special '99' scene
                for scene in self.getScenes():
                    sceneMap[scene] = ('%02d' % nextFreeScene)  # TODO: refer to Organization 
                    nextFreeScene = (nextFreeScene + 1)
                print('   with scene mapping %s' % sceneMap)
                # move each subEntry
                print('   %d subentries' % len(self.subEntries))
                for subEntry in self.getSubEntries(False):  
                    newElements = subEntry.getElements()
                    if (elements):
                        newElements = (newElements.union(elements))
                    if (removeIllegalElements):
                        newElements.remove(self.model.getUnknownElements())
                    subEntry.renameTo(name=name, 
                                      scene=sceneMap[subEntry.getScene()], 
                                      number=subEntry.getNumber(), 
                                      elements=newElements, 
                                      removeIllegalElements=removeIllegalElements)
                if (self <> newGroup):
                    self.remove()
            else:  # group with NAME does not exist
                return(Entry.renameTo(self, name=name, elements=elements, removeIllegalElements=removeIllegalElements))       


    def deleteDoubles(self, mergeElements=True):
        """Remove double Singles contained in self. Recurse if self contains groups.
        
        Boolean mergeElements indicates that elements from both doubles shall be merged into remaining name
        Return Number indicating how many doubles were deleted. 
        """
        doubles = 0
        for entry1 in self.subEntries[:]:
            if (entry1.isGroup()):
                doubles = (doubles + entry1.deleteDoubles())
            else:
                for entry2 in self.subEntries[:]:
                    if (entry2.isGroup()):
                        pass
                    elif (entry1 == entry2):
                        break  # avoid checking pairs twice
                    elif (entry1.isIdentical(entry2)):
                        #print('Identical entries: "%s" and "%s"' % (entry1.getPath(), entry2.getPath()))
                        entry1.organizer.deleteDouble(entry2, mergeElements)
                        doubles = (doubles + 1)
        return(doubles)


    def removeNewIndicator(self):
        """Remove the new indicator on all subentries
        """
        for entry in self.subEntries:
            entry.removeNewIndicator()

    
    
# Class Initialization
Entry.ProductTrader.registerClassFor(Group, Entry.SpecificationGroup)  # register Group to handle directories
    
