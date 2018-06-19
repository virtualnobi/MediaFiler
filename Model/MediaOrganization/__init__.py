# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
# from __builtin__ import classmethod
import datetime
import re
import os.path
import glob
import shutil
import StringIO
from collections import OrderedDict
import logging
import gettext
## Contributed 
import wx
## nobi
from nobi.wx.Menu import Menu
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
    _ = Translation.ugettext
def N_(message): return message



class MediaOrganization(object):
    """Defines two organizations for media, by name and by date.

    A variation of the Strategy pattern: The two organization classes define different behavior 
    as Strategy does, but they are instantiated to carry data specific to each media. 

    For example, the OrganizationByName instances keep name and scene, while OrganizationByDate 
    instances keep year, month, day for their media context. 
    """


# Constants
    IdentifierSeparator = '-'  # to separate identifier parts such as number, name, scene, year, month, day
    FormatNumber = '%03d'  # format string for number ensuring uniqueness of pathname



# Class Variables
    Logger = logging.getLogger(__name__)
    ImageFilerModel = None  # to access legal names 
    MoveToLocations = []  # last move-to locations for repeated moving; no concurrent usage of subclasses!
    


# Class Methods
    @classmethod
    def setModel(self, model):
        """Set up the MediaOrganization for use with model.
        """
        self.ImageFilerModel = model


    @classmethod
    def getDescription(cls):
        """Return a description of the organization. 
        """
        raise NotImplementedError


    @classmethod
    def getFilterPaneClass(cls):
        """Return the class to instantiate filter pane.
        """
        raise NotImplementedError


    @classmethod
    def constructPath(cls, **kwargs):  # TODO: turn elements key into a set, not a string
        """Construct a pathname, given the parameters from kwargs.
        
        If a parameter is not contained in kwargs, it is derived from self's settings.
        If a parameter is contained in kwargs, but None, it will not be used to construct a path (e.g., scene).
        If a parameter is contained in kwargs, other than None, it will be used instead of self's setting.

        If either makeUnique or number is given, the resulting pathname contains a number. 
        makeUnique takes precedence over the number parameter.

        Number number contains the number of the media (in date or name group)
        Boolean makeUnique requests to create a unique new pathname (takes precedence over number)
        String elements as given by MediaClassHandler().getElementString()
        String extension contains the media's extension

        Return a String containing the path
        """
        if (('rootDir' in kwargs)
            and kwargs['rootDir']):
            result = kwargs['rootDir']
        else:
            result = cls.ImageFilerModel.getRootDirectory()
        result = os.path.join(result, cls.constructPathForOrganization(**kwargs))
        number = None
        if (('makeUnique' in kwargs)
            and kwargs['makeUnique']):
            number = 1
            while (0 < len(glob.glob(result + cls.IdentifierSeparator + (cls.FormatNumber % number) + '*'))):
                number = (number + 1)
        elif (('number' in kwargs)
              and kwargs['number']):
            number = kwargs['number']
        if (number):
            if (isinstance(number, str)
                or isinstance(number, unicode)):
                print('MediaOrganization.constructPath(): Deprecated use of non-numeric number!')
                number = int(number)
            result = (result + cls.IdentifierSeparator + (cls.FormatNumber % number))
        if (('elements' in kwargs)
            and kwargs['elements']):
            tagSpec = kwargs['elements']
            if (isinstance(tagSpec, str)
                or isinstance(tagSpec, unicode)):
                print('Organization.constructPath(): Deprecated usage of string parameter for elements!')
                tagSpec = cls.ImageFilerModel.getClassHandler().stringToElements(tagSpec)
            result = (result + cls.ImageFilerModel.getClassHandler().elementsToString(tagSpec))
        if (('extension' in kwargs)
            and kwargs['extension']):
            result = (result + '.' + kwargs['extension'])
        return(result)


    @classmethod
    def constructPathForOrganization(self, **kwargs):
        """Construct the organization-specific part of a media pathname, between root directory and number.
        """
        raise NotImplementedError


    @classmethod
    def constructPathFromImport(cls, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):
        """Construct a pathname to import media at sourcePath to. 
        
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
        
        Importing.ImportParameterObject importParameters
        String sourcePath is the pathname of the image
        Number level counts the embedding from the initial import directory
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir is the pathname of the directory to import into  # TODO: remove
        Dictionary targetPathInfo contains information about the target path
        Dictionary illegalElements collects a mapping of illegal elements to source pathnames
        """
        if (targetDir <> targetPathInfo['rootDir']):
            raise ValueError, ('targetDir %s does not match %s!' % (targetDir, targetPathInfo['rootDir']))
        newPath = cls.constructPathFromImport(importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements)
        importParameters.logString('Importing "%s"\n       as "%s"\n' % (sourcePath, newPath))
        if (not importParameters.getTestRun()):
            try:
                (head, tail) = os.path.split(newPath)  # @UnusedVariable
                if (not os.path.exists(head)):
                    os.makedirs(head)
                shutil.copy2(sourcePath, newPath)
                if (importParameters.getDeleteOriginals()):
                    os.remove(sourcePath)
            except Exception as e:
                print('Error renaming "%s"\n            to "%s". Complete error:\n%s' % (sourcePath, newPath, e))


    @classmethod
    def registerMoveToLocation(cls, path):
        """Store information where media was moved to, for retrieval as targets for subsequent moves.
        
        Subclasses must pick appropriate parameters.
        """
        cls.MoveToLocations.append(path)
        if (GUIId.MaxNumberMoveToLocations < len(cls.MoveToLocations)):
            del cls.MoveToLocations[0]


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        """
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.IdentifierSeparator), 
                                      flag=(wx.ALIGN_CENTER_VERTICAL))
        aMediaNamePane.numberInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(60,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.numberInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))



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
            logging.warning('MediaOrganization(): "%s" may contain illegal identifier' % aPath)
        unconsumed = self.setNumberFromPath(unconsumed)
        return(None)



# Setters
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
        if (match):  # number found  
            self.number = match.group(1)
            return(match.group(2))
        else:  # no number found
            self.number = ''
            return(pathRest)


    def constructPathForSelf(self, **kwargs):
        """Construct a path for self, incorporating changes as specified in kwargs.

        If a parameter is not contained in kwargs, it is derived from self's settings.
        If a parameter is contained in kwargs, but None, it will not be used to construct a path (e.g., scene).
        If a parameter is contained in kwargs, other than None, it will be used instead of self's setting.

        String number contains the number of the media (in date or name group)
        Boolean makeUnique requests to create a unique new pathname (takes precedence over number)
        String elements as given by MediaClassHandler().getElementString()
        String extension contains the media's extension

        Return a String containing the path for self's context
        """
        if (not 'number' in kwargs):
            kwargs['number'] = self.getNumber()
        if (not 'elements' in kwargs):
            kwargs['elements'] = self.context.getElements()
        if (not 'extension' in kwargs):
            kwargs['extension'] = self.context.getExtension()
        return(self.constructPath(**kwargs))


# Getters
    def getContext(self):
        """Return the Entry which is organized by self.
        """
        return(self.context)


    def isUnknown(self):
        """Return whether self is incompletely specified.

        Return Boolean
        """
        raise NotImplementedError


    def isFilteredBy(self, aFilter):
        """Return whether self is being filtered.
        
        MediaFilter aFilter
        Return Boolean
        """
        raise NotImplementedError


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
         
        TODO: Remove his when OrganizationByName uses embedded Groups for the scene, and let the Group
        list the numbers. 
        """
        return([e.getOrganizer().getNumber() 
                for e in self.getContext().getParentGroup().getSubEntries() 
                if (not e.isGroup())])


    def extendContextMenu(self, menu):
        """
        The AssignNumber function will be added in subclasses, as it's not applicable to singletons in organization by name.
        """
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
            lastNumber = currentNumber
        renumberList.append(lastNumber + 1)
        assignNumberMenu = wx.Menu()
        for i in renumberList:
            assignNumberMenu.Append((GUIId.AssignNumber + i), str(i))
            if (i == self.getNumber()):
                assignNumberMenu.Enable((GUIId.AssignNumber + i), False)
        return(assignNumberMenu)


    def runContextMenuItem(self, menuId, parentWindow):  # @UnusedVariable
        """
        Number menuId
        wx.Window parentWindow to display messages
        Return String describing execution status
        """
        if ((GUIId.AssignNumber <= menuId)
            and (menuId <= (GUIId.AssignNumber + GUIId.MaxNumberNumbers))):
            number = (menuId - GUIId.AssignNumber)
            self.__class__.Logger.debug('MediaOrganization.runContextMenu(): Renaming to number %d' % number)
            return(self.renumberTo(number))
        else:
            self.__class__.Logger.error('MediaOrganization.runContextMenu(): Unhandled function %d on "%s"!' % (menuId, self.getContext().getPath()))
    


# Other API Functions
    def deleteDouble(self, otherEntry, mergeElements=False):
        """Remove otherEntry, but rename self to keep its information if needed. 
        
        If mergeElements is True, elements from otherEntry are added to self's elements.
        If mergeElements is False, self is renamed to otherEntry if
        - self contains "new", but otherEntry does not
        - self has fewer elements than otherEntry does

        MediaFiler.Entry otherEntry
        Boolean mergeElements
        """
        newPath = None
        if (mergeElements):
            newElements = self.context.getElements().union(otherEntry.getElements())
            print('From "%s"\n     adding elements %s\n  to "%s"' % (otherEntry.getPath(), newElements, self.context.getPath()))
            self.context.renameTo(elements=newElements)
        else:
            if ((MediaClassHandler.ElementNew in self.context.getElements())
                and (not MediaClassHandler.ElementNew in otherEntry.getElements())):
                print('Keep   "%s"\nremove "%s"' % (otherEntry.getPath(), self.context.getPath()))
                newPath = otherEntry.getPath()
            elif ((not MediaClassHandler.ElementNew in self.context.getElements())
                  and (MediaClassHandler.ElementNew in otherEntry.getElements())):
                print('Keep   "%s"\nremove "%s"' % (self.context.getPath(), otherEntry.getPath()))
            else:
                if (len(self.context.getElements()) < len(otherEntry.getElements())):
                    print('Keep   "%s"\nremove "%s"' % (otherEntry.getPath(), self.context.getPath()))
                    newPath = otherEntry.getPath()
                else:
                    print('Keep   "%s"\nremove "%s"' % (self.context.getPath(), otherEntry.getPath()))
        otherEntry.remove()
        if (newPath):  
            self.context.renameToFilename(newPath)


    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        aMediaNamePane.numberInput.SetValue(self.getNumberString())
        aMediaNamePane.numberInput.Enable(not self.context.isGroup())


    def getValuesFromNamePane(self, aMediaNamePane):
        """Return the organization-specific fields in aMediaNamePane as a dictionary
        
        UI.MediaNamePane aMediaNamePane
        
        Return Dictionary
        """
        result = {}
        number = aMediaNamePane.numberInput.GetValue()
        if (number == ''):
            result['number'] = None
        else:
            try:
                result['number'] = int(number)
            except:
                return(None)
        return(result)


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
                and (not ((origin - distance) in numberList))):
                    result = (origin - distance)
            elif ((origin - distance) == self.getNumber()):
                result = (origin - distance)
            elif (not ((origin + distance) in numberList)):
                result = (origin + distance)
            elif ((origin + distance) == self.getNumber()):
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
            while (current <> target):
                moveList.append(((current + step), current))
                current = (current + step)
        if (self.getNumber() == gap):  # special case: gap is the place where self is removed
            moveList.insert(0, (self.getNumber(), target))
        else:
            moveList.append((self.getNumber(), target))
        return(moveList)


    def renumberTo(self, newNumber):
        """Renumber Singles in self's parent group so that self can change to the given number.
        """
        MediaOrganization.Logger.debug('MediaOrganization.renumberTo(): Assigning new number %d to number %d' % (newNumber, self.getNumber()))
        numberToEntryMap = self.getNumberedEntriesMap()
        numbersUsed = numberToEntryMap.keys()
        MediaOrganization.Logger.debug('MediaOrganization.renumberTo(): Used numbers are %s' % numbersUsed)
        gap = self.findNearestGap(newNumber, numbersUsed)
        MediaOrganization.Logger.debug('MediaOrganization.renumberTo(): Nearest gap is %d' % gap)
        numberPairList = self.createReorderSequence(newNumber, gap, numbersUsed)
        MediaOrganization.Logger.debug('MediaOrganization.renumberTo(): Reordering %s' % numberPairList)
        renameList = []
        for (now, then) in numberPairList:
            entry = numberToEntryMap[now]
            renameList.append((entry, entry.getPath(), entry.getOrganizer().constructPathForSelf(number=then)))
        MediaOrganization.Logger.debug('MediaOrganization.renumberTo(): Mapping names %s' % renameList)
        if (self.__class__.ImageFilerModel.renameList(renameList)):
            return(_('%d media renumbered' % len(renameList)))
        else:
            return(_('Renumbering failed!'))

