# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
import datetime
import re
import os.path
import glob
import shutil
from io import StringIO
import copy
from collections import OrderedDict
import logging
import gettext
import itertools
## Contributed 
import wx
## nobi
from nobi.LastUpdateOrderedDict import LastUpdateOrderedDict
from nobi.wx.Menu import Menu
from nobi.wx.Validator import TextCtrlIsIntValidator
## Project
import Model.Installer
from ..Entry import Entry
from ..Group import Group
from ..MediaNameHandler import MediaNameHandler
from ..MediaClassHandler import MediaClassHandler
import UI  # to access UI.PackagePath
from UI import GUIId



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at "%s"; using originals instead of locale %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
    _ = Translation.gettext
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)


class MediaOrganization(object):
    """Defines two organizations for media, by name and by date.

    A variation of the Strategy pattern: The two organization classes define different behavior 
    as Strategy does, but they are instantiated to carry data specific to each media. 

    For example, the OrganizationByName instances keep name and scene, while OrganizationByDate 
    instances keep year, month, day for their media context. 
    """


# Constants
    IdentifierSeparator = '-'  # to separate identifier parts such as number, name, scene, year, month, day
    FormatNumber = u'%03d'  # format string for number ensuring uniqueness of pathname



# Class Variables
    ImageFilerModel = None  # to access legal names 
    MoveToLocations = LastUpdateOrderedDict()  # last move-to locations for repeated moving; no concurrent usage of subclasses!



# Class Methods
    @classmethod
    def setModel(self, model):
        """Set up the MediaOrganization for use with model.
        """
        self.ImageFilerModel = model


    @classmethod
    def getModel(self):
        """"""
        return(self.ImageFilerModel)


    @classmethod
    def getDescription(cls):
        """Return a description of the organization. 
        """
        raise NotImplementedError


    @classmethod
    def constructPath(cls, **pathInfo):  # TODO: turn elements key into a set, not a string
        """Construct a pathname, given the parameters from pathInfo.
        
        If a parameter is not contained in pathInfo, it is derived from self's settings. # TODO: There's no self, as it's a class method!
        If a parameter is contained in pathInfo, but None, it will not be used to construct a path (e.g., scene).
        If a parameter is contained in pathInfo, other than None, it will be used instead of self's setting.

        If either makeUnique or number is given, the resulting pathname contains a number. 
        makeUnique takes precedence over the number parameter.

        Number number contains the new number of the media (in date or name group)
        Boolean makeUnique requests to create a unique new pathname (takes precedence over number)
        set of String elements
        String extension contains the media's extension

        Return a String containing the path
        """
        if (('rootDir' in pathInfo)
            and pathInfo['rootDir']):
            result = pathInfo['rootDir']
        else:
            result = cls.ImageFilerModel.getRootDirectory()
        result = os.path.join(result, cls.constructOrganizationPath(**pathInfo))
        number = None
        if (('number' in pathInfo)
              and pathInfo['number']):
            number = pathInfo['number']        
        if ((('makeUnique' in pathInfo)
             and pathInfo['makeUnique'])):
            number = 1
            while (0 < len(glob.glob(result + cls.IdentifierSeparator + (cls.FormatNumber % number) + '*'))):
                number = (number + 1)
        if (number):
            if (isinstance(number, str)):
                Logger.warning('MediaOrganization.constructPath(): Deprecated use of non-numeric number!')
                number = int(number)
            result = (result + cls.IdentifierSeparator + (cls.FormatNumber % number))
        if (('elements' in pathInfo)
            and pathInfo['elements']):
            tagSpec = pathInfo['elements']
            if (isinstance(tagSpec, str)):
                Logger.warning('Organization.constructPath(): Deprecated usage of string parameter for elements!')
                tagSpec = cls.ImageFilerModel.getClassHandler().stringToElements(tagSpec)
            if (('classesToRemove' in pathInfo)
                and pathInfo['classesToRemove']):
                for tagClass in pathInfo['classesToRemove']:
                    for tag in cls.ImageFilerModel.getClassHandler().getElementsOfClassByName(tagClass):
                        tagSpec.discard(tag)
            result = (result + cls.ImageFilerModel.getClassHandler().elementsToString(tagSpec))
        if (('extension' in pathInfo)
            and pathInfo['extension']):
            result = (result + '.' + pathInfo['extension'])
        return(result)


    @classmethod
    def constructOrganizationPath(cls, **kwargs):
        """Construct the organization-specific part of a media pathname, between root directory and number.
        """
        raise NotImplementedError


    @classmethod
    def pathInfoForImport(cls, importParameters, sourcePath, level, oldName, pathInfo):  # @UnusedVariable
        """Collect information about media from source path.
        
        Importing.ImportParameters importParameters
        str sourcePath indicates the media's current file path
        int level
        str oldName
        dict pathInfo contains whatever information is already known (must contain "root" key)
        Returns dict or None 
        """
        result = copy.copy(pathInfo)
        return(result)

        
    @classmethod
    def constructPathFromImport(cls, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):
        """Construct a pathname to import media at sourcePath. 
        
        Importing.ImportParameterObject importParameters
        String sourcePath is the pathname of the image
        Number level counts the embedding from the initial import directory
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir is the pathname of the directory to import into
        Dictionary targetPathInfo contains information about the target path
        Dictionary illegalElements collects a mapping of illegal elements to source pathnames
        
        Return a String containing the new absolute pathname
        """
        raise NotImplementedError


    @classmethod
    def getGroupFromPath(cls, path):  # @UnusedVariable
        """Retrieve the group into which media at path shall be included.
        
        String path contains the media's file path
        Returns a MediaFiler.Group instance
        """
        raise NotImplementedError


    @classmethod
    def findParentForPath(cls, path):
        """Find or create the Group which is the parent of the Group representing the given path.
        
        String path
        Return MediaFiler.Group
        """
        (head, dummy) = os.path.split(path)
        group = cls.ImageFilerModel.getEntry(group=True, path=head)
        if (not group):
            group = Group.createAndPersist(cls.ImageFilerModel, path=head)
        return(group)
     
        
    @classmethod
    def importMedia(cls, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):
        """Import image at sourcePath, i.e. move to new location in model's directory.        

        TODO: when importing a folder with a given name, ensure a single with this name is converted to a group first
        
        Importing.ImportParameterObject importParameters
        String sourcePath is the pathname of the image
        Number level counts the embedding from the initial import directory
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir is the pathname of the directory to import into  # TODO: remove
        Dictionary targetPathInfo contains information about the target path
        Dictionary illegalElements collects a mapping of illegal elements to source pathnames
        """
        if (targetDir != targetPathInfo['rootDir']):
            raise ValueError('targetDir "%s" does not match target path info "%s"!' % (targetDir, targetPathInfo['rootDir']))
        newPath = cls.constructPathFromImport(importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements)
        importParameters.logString('Importing "%s"\n  as "%s"' % (sourcePath, newPath))
        if (not importParameters.getTestRun()):
            try:
                (head, tail) = os.path.split(newPath)  # @UnusedVariable
                if (not os.path.exists(head)):
                    os.makedirs(head)
                shutil.copy2(sourcePath, newPath)
            except WindowsError as e: 
                if (e.winerror == 5):
                    importParameters.logString('Cannot access "%s" (Windows error 5)' % newPath)
                    importParameters.logString('%s' % e)
            except Exception as e:
                Logger.error('MediaOrganisation.importMedia(): Error importing "%s" to "%s" (%s)' % (sourcePath, newPath, e))
                importParameters.logString('Error importing "%s"\n  to "%s":\n%s' % (sourcePath, newPath, e))


    @classmethod
    def registerMoveToLocation(cls, pathInfo):
        """Store information where media was moved to.
        
        This information is used to create a submenu to move media to previously used locations.
        """
        Logger.debug('MediaOrganization.registerMoveToLoation(): Adding %s' % pathInfo)
        menuItem = cls.menuItemFromPathInfo(pathInfo)
        cls.MoveToLocations[menuItem] = pathInfo
        if (GUIId.MaxNumberMoveToLocations < len(cls.MoveToLocations)):
            cls.MoveToLocations.popitem(last=False)
        Logger.debug('MediaOrganization.registerMoveToLoation(): Move-to-locations are %s' % cls.MoveToLocations)


    @classmethod
    def menuItemFromPathInfo(cls, pathInfo):
        result = u''
        for key in pathInfo.keys():
            result = ('%s%s%s' % (result, pathInfo[key], MediaOrganization.IdentifierSeparator))
        if (result != u''):
            result = result[:-1]
        return(result)


    @classmethod
    def constructMoveToMenu(cls):
        """Return a wx.Menu representing the last locations media was moved to.
        """
        result = Menu()
        moveToId = GUIId.SelectMoveTo
        for menuItem in reversed(cls.MoveToLocations.keys()):
            result.Append(moveToId, menuItem)
            moveToId = (moveToId + 1)
        return(result)


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        """
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.IdentifierSeparator), 
                                      flag=(wx.ALIGN_CENTER_VERTICAL))
        aMediaNamePane.numberInput = wx.TextCtrl(aMediaNamePane, 
                                                 size=wx.Size(60,-1), 
                                                 style=wx.TE_PROCESS_ENTER,
                                                 validator=TextCtrlIsIntValidator(label=_('Media Number'), 
                                                                                  minimum=1, 
                                                                                  maximum=999,
                                                                                  emptyAllowed=True))
        aMediaNamePane.numberInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))


    @classmethod
    def initFilterPane(cls, aMediaFilterPane):
        """Add controls to aMediaFilterPane to filter according to the organization.
        """
        pass



# Lifecycle
    def __init__(self, anEntry, aPath):
        """Create a MediaOrganization instance to go with anEntry.
        
        MediaFiler.Entry anEntry is the group or single media to be organized
        String aPath contains the path for anEntry
        Returns a MediaFiler.MediaOrganization instance
        """
        # internal state
        self.context = anEntry
        self.path = os.path.normpath(aPath)
        self.number = ''
        unconsumed = self.setIdentifiersFromPath(self.context.getOrganizationIdentifier())
        if (unconsumed == self.context.getOrganizationIdentifier()):
            Logger.warning('MediaOrganization(): "%s" may contain illegal identifier' % aPath)
        unconsumed = self.setNumberFromPath(unconsumed)
        return(None)



    def setIdentifiersFromPath(self, path):
        """Extract identifiers relevant for the organization from path & return unconsumed part of path. 
        
        Trailing number will be recovered later and should not be extracted.
        
        Return String
        """
        raise NotImplementedError


    def setNumberFromPath(self, pathRest):
        """Check whether pathRest begins with a 3-digit number, store it if so, and return the unconsumed rest.
        
        Assumes that Entry.IdentifierSeparator introduces the number.
        
        Returns a String
        """
        match = re.match(r'''-(\d\d\d)           # three-digit image number = \1
                             (.*)                # the rest = \2
                           ''', 
                          pathRest,
                          flags=re.VERBOSE)  
#                         pathRest)
        if (match):  # number found  
            self.number = match.group(1)
            return(match.group(2))
        else:  # no number found
            self.number = ''
            return(pathRest)



# Setters
# Getters
    def __repr__(self):
        return('for %s' % self.getContext().getPath())

    
    def getContext(self):
        """Return the Entry which is organized by self.
        """
        return(self.context)


    def getPath(self):
        return(self.path)


    def getNumber(self):
        if (self.number):
            return(int(self.number))
        else:
            return(None)


    def getNumberString(self):
        return(self.number)


    def getNumbersInGroup(self):
        """Return the (ascending) list of Numbers in self's group.
         
        TODO: Remove this when OrganizationByName uses embedded Groups for the scene, and let the Group
        list the numbers.
        
        Return Sequence of Numbers (empty if self is not a Group) 
        """
        return([e.getOrganizer().getNumber() 
                for e in self.getContext().getParentGroup().getSubEntries(filtering=False) 
                if (not e.isGroup())])


    def isUnknown(self):
        """Return whether self is incompletely specified.

        Return Boolean
        """
        raise NotImplementedError


    def matches(self, **kwargs):
        """Checks whether self matches organization-specific conditions given in kwargs.
        
        Return Boolean indicating self matches the conditions
        """
        return(True)


#     def isFilteredBy(self, aFilter):
#         """Return whether self is being filtered.
#         
#         MediaFilter aFilter
#         Return Boolean
#         """
#         raise NotImplementedError


    def getPathInfo(self, filtering=False):
        """Return dictionary containing organization-specific identifiers.
        
        Boolean filtering specifies whether to include all entries (in a group) or only filtered ones
        """
        result = {}
        result['elements'] = self.getContext().getTags(filtering)
        if (not self.getContext().isGroup()):
            result['number'] = self.getNumber()
            result['extension'] = self.getContext().getExtension()
        return(result)


    def requiresUniqueNumbering(self):
        """By default, all Single media require a number to ensure uniqueness.
        """
        return(True)


    def extendContextMenu(self, menu):
        """
        The AssignNumber function will be added in subclasses, as it's not applicable to singletons organized by name.
        """
        raise BaseException('MediaOrganization.extendContextMenu(): Deprecated')
        pass


# Other API functions
    def deriveRenumberSubMenu(self):
        """Return the wx.Menu containing the renumber possibilities (GUIId.AssignNumber).

        Run through the list of numbers used in self's parent group, 
        - if there's a gap between two neighbor numbers, use the smallest number in the gap.
        - if the neighbor numbers are successive (i.e., only +1 apart), use the higher number.
        """
        renumberList = []
        groupNumbers = self.getNumbersInGroup()  # TODO: get rid of this as soon as OrganizationByName scenes have their own group
        lastNumber = 0
        for currentNumber in groupNumbers:
            renumberList.append(lastNumber + 1)
            if (len(renumberList) == GUIId.MaxNumberNumbers):
                break
            if (currentNumber != None):
                lastNumber = currentNumber
        renumberList.append(lastNumber + 1)
        assignNumberMenu = wx.Menu()
        for i in renumberList:
            assignNumberMenu.Append((GUIId.AssignNumber + i), (MediaOrganization.FormatNumber % i))
            if (i == self.getNumber()):
                assignNumberMenu.Enable((GUIId.AssignNumber + i), False)
        return(assignNumberMenu)


    def runContextMenuItem(self, menuId, parentWindow):  # @UnusedVariable
        """
        AssignNumber is added by subclasses, as it's not applicable to singletons organized by name
        SelectMoveTo is added by Entry but handled here, as it uses this class' state
        
        Number menuId
        wx.Window parentWindow to display messages
        Return String describing execution status
        """
        if ((GUIId.AssignNumber <= menuId)
            and (menuId <= (GUIId.AssignNumber + GUIId.MaxNumberNumbers))):
            number = (menuId - GUIId.AssignNumber)
            Logger.debug('MediaOrganization.runContextMenu(): Renaming to number %d' % number)
            wx.GetApp().setInfoMessage(_('Renumbering...'))
            result = self.renumberTo(number, wx.GetApp().getProgressBar())
            return(result)
        elif ((GUIId.SelectMoveTo <= menuId)
              and (menuId <= (GUIId.SelectMoveTo + GUIId.MaxNumberMoveToLocations))):
            number = (menuId - GUIId.SelectMoveTo)
            items = list(reversed(self.__class__.MoveToLocations.items()))
            newPathInfo = items[number][1]
            Logger.debug('MediaOrganization.runContextMenu(): Moving to %d-th move-to-location %s' % (number, newPathInfo))
            currentPathInfo = self.getPathInfo()
            if ('number' in currentPathInfo):
                del currentPathInfo['number']
            currentPathInfo['makeUnique'] = True
            for key in newPathInfo.keys():
                currentPathInfo[key] = newPathInfo[key]
            Logger.debug('MediaOrganization.runContextMenu(): Renaming to %s' % currentPathInfo)
            wx.GetApp().setInfoMessage('Moving...')
            if (self.getContext().isGroup()):
                self.renameGroup(**currentPathInfo)
            else:  # must be a Single
                self.renameSingle(**currentPathInfo)
        else:
            Logger.error('MediaOrganization.runContextMenu(): Unhandled function %d on "%s"!' % (menuId, self.getContext().getPath()))
    


    def deleteDouble(self, otherEntry):
        """Remove otherEntry, but rename self to keep its information.         

        self and otherEntry have already been determined to have identical content.

        MediaFiler.Entry otherEntry
        """
        selfElements = self.getContext().getTags()
        otherElements = otherEntry.getTags()
        newElements = selfElements.union(otherElements)
        if ((not MediaClassHandler.ElementNew in selfElements)
            or (not MediaClassHandler.ElementNew in otherElements)):
            newElements.discard(MediaClassHandler.ElementNew)
        if (newElements != selfElements):
            Logger.debug('MediaOrganization.deleteDouble(): Adding tags %s to "%s"' % (newElements, self.context))
            pathInfo = self.getPathInfo()
            pathInfo['elements'] = newElements
            self.getContext().renameTo(**pathInfo)
        Logger.debug('MediaOrganization.deleteDouble(): Removing "%s"', otherEntry)
        otherEntry.remove()
        try:
            self.getContext().getDuplicates().remove(otherEntry)  # remove duplicate
        except ValueError as e:  
            pass  # don't care if otherEntry was not found in list


    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        aMediaNamePane.numberInput.SetValue(self.getNumberString())
        aMediaNamePane.numberInput.Enable(not self.context.isGroup())


    def getValuesFromNamePane(self, aMediaNamePane):
        """Return the organization-specific fields in aMediaNamePane as a dictionary
        
        UI.MediaNamePane aMediaNamePane
        Return Dictionary
            or None if field values are illegal
        """
        result = {}
        if (not self.getContext().isGroup()):
            number = aMediaNamePane.numberInput.GetValue()
            number = number.strip()
            if (number != u''):
                try:
                    result['number'] = int(number)
                except:
                    return(None) # TODO: add error dialog
            else:
                result['makeUnique'] = True
        return(result)


    def renameSingle(self, filtering=False, elements=None, removeIllegalElements=False, **pathInfo):
        """Rename self's media context, which is a Single, according to the parameters given. 

        Boolean filtering is irrelevant for Singles, see renameGroup()
        Set elements specifies the new tags (or None)
        Boolean removeIllegalElements specifies that unknown tags shall be removed
        dict pathInfo contains organization-specific attributes
        Return the Entry to select after renaming 
        """
        if (self.getContext().isGroup()):
            raise ValueError('MediaOrganization.renameSingle(): Called on a Group!')
        currentPathInfo = self.getPathInfo(filtering)
        for key in pathInfo:
            currentPathInfo[key] = pathInfo[key]
        # change elements as required
        if (elements 
            or removeIllegalElements):
            if (elements):
                newElements = elements
            else:
                newElements = self.getContext().getTags()
            newElements2 = self.getModel().getClassHandler().combineTagsWithPriority(self.getContext().getTags(), elements)
            if (newElements != newElements2):
                print('MediaOrganization.renameSingle(): Different resulting tag sets (old: %s, new: %s)' % (newElements, newElements2))
            if (removeIllegalElements):
                newElements = set(filter(self.__class__.ImageFilerModel.getClassHandler().isLegalElement, newElements))
            currentPathInfo['elements'] = newElements
        # rename 
        oldParent = self.getContext().getParentGroup()
        Logger.debug('MediaOrganization.renameSingle(): Path info is %s' % currentPathInfo)
        newName = self.constructPath(**currentPathInfo)
        Logger.debug('MediaOrganization.renameSingle(): New name is %s' % newName)
        self.getContext().renameToFilename(newName)
        # check whether old group still has subentries
        if (len(oldParent.getSubEntries(filtering=False)) == 0):
            oldParent.remove()
        self.__class__.registerMoveToLocation(currentPathInfo)
        return(self.getContext())


    def renameGroup(self, processIndicator=None, filtering=False, **pathInfo):
        """Rename self's media context, which is a group, according to the parameters.
        
        If filtering, only rename the subentries not filtered. 
        If no subentries remain in the group after renaming, remove the group.
        
        processIndicator 
        Boolean filtering determines whether filtered subentries are renamed as well
        dict pathInfo
        Return the Entry to select after renaming 
        """
        if (not self.getContext().isGroup()):
            raise ValueError('MediaOrganization.renameGroup(): Called on a Single!')
        if (('number' in pathInfo)
            and (pathInfo['number'])):
            raise ValueError('MediaOrganization.renameGroup(): Number %s specified when renaming group "%s"' % (pathInfo['number'], self.getContext()))
        newParent = self.findGroupFor(**pathInfo)
        # rename subentries
        renameList = self.getRenameList(newParent, pathInfo, filtering=filtering)
        if (processIndicator):
            processIndicator.beginPhase(len(renameList))
        for (entry, pathInfo) in renameList:
            if (processIndicator):
                processIndicator.beginStep()
            entry.renameTo(processIndicator=processIndicator, **pathInfo)  # removes self when the last subentry was renamed (if no further subentries exist)
        return(newParent)


    def getRenameList(self, newParent, pathInfo, filtering=True):
        """Create a list of <entry, pathInfo> pairs where the entries are all subentries of self's context, 
        and pathInfo describes their new placement.
        """
        raise NotImplementedError


    def findGroupFor(self, **pathInfo):
        """Find or create a Group described by given path info.
        
        Return Group
        """
        raise NotImplementedError



# Internal
    def getNumberedEntriesMap(self):
        """Return a dictionary mapping numbers to the subentries of self's parent Group.
        """
        result = {}
        for entry in self.getContext().getParentGroup().getSubEntries(filtering=False):
            if ((self.getContext().model.organizedByDate)  # TODO: move to OrganizationByName
                or (self.getScene() == entry.getOrganizer().getScene())):
                result[entry.getOrganizer().getNumber()] = entry
        return(result)


    def findNearestGap(self, origin, numberList):
        """Find the gap nearest to a number in a list of numbers.
        
        Number origin gives the number to start looking at
        List numberList contains the list of all numbers
        Return Number between 1 and (len(numberList) + 1)
        """
        distance = 0
        result = 0
        while (result == 0):
            if ((0 < (origin - distance))
                and (not ((origin - distance) in numberList))):  # gap in (distance) steps before origin
                    result = (origin - distance)
            elif ((origin - distance) == self.getNumber()):  # gap is created when self is moved
                result = (origin - distance)
            elif (not ((origin + distance) in numberList)):  # gap in (distance) steps after origin
                result = (origin + distance)
            elif ((origin + distance) == self.getNumber()):  # gap is created when self is moved
                result = (origin + distance)
            distance = (distance + 1)
        return(result)

    
    def createReorderSequence(self, target, gap, numberList):
        """Return a list of number pairs describing the renumbering actions to move self to origin.
        
        Number target the new number of self
        Number gap the gap in numbering nearest to target
        List numberList the list of existing numbers
        """
        moveList = []
        if (target in numberList):
            step = (1 if (gap < target) else -1)
            current = gap
            while (current != target):
                moveList.append(((current + step), current))
                current = (current + step)
        if (self.getNumber() == gap):  # special case: gap is the place where self is removed
            moveList.insert(0, (self.getNumber(), target))
        else:
            moveList.append((self.getNumber(), target))
        return(moveList)


    def renumberTo(self, newNumber, progressBar=None):
        """Renumber Singles in self's parent group so that self can change to the given number.
        
        Number newNumber
        PhasedProgressBar progressBar
        """
        Logger.debug('MediaOrganization.renumberTo(): Assigning new number %d to number %d' % (newNumber, self.getNumber()))
        numberToEntryMap = self.getNumberedEntriesMap()
        numbersUsed = numberToEntryMap.keys()
        Logger.debug('MediaOrganization.renumberTo(): Used numbers are %s' % numbersUsed)
        gap = self.findNearestGap(newNumber, numbersUsed)
        Logger.debug('MediaOrganization.renumberTo(): Nearest gap is %d' % gap)
        numberPairList = self.createReorderSequence(newNumber, gap, numbersUsed)
        Logger.debug('MediaOrganization.renumberTo(): Reordering %s' % numberPairList)
        renameList = []
        for (now, then) in numberPairList:
            entry = numberToEntryMap[now]
            pathInfo = entry.getOrganizer().getPathInfo()
            pathInfo['number'] = then
            newPath = entry.getOrganizer().constructPath(**pathInfo)
            renameList.append((entry, entry.getPath(), newPath))
            Logger.debug('from %s\n  to %s' % (entry.getPath(), newPath))
#         Logger.debug('MediaOrganization.renumberTo(): Mapping names %s' % renameList)
        if (self.__class__.ImageFilerModel.renameList(renameList)):
            return(_('%d media renumbered' % len(renameList)))
        else:
            return(_('Renumbering failed!'))

