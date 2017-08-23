# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
from __builtin__ import classmethod
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
import exifread
import wx
## nobi
from nobi.wxExtensions.Menu import Menu
from nobi.PartialDateTime import PartialDateTime
## Project
import UI  # to access UI.PackagePath
from UI import GUIId
from .Entry import Entry
from .Group import Group
from .MediaNameHandler import MediaNameHandler
import Installer



# Internationalization
# requires "PackagePath = __path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)  #, languages=['en'])
except BaseException as e:  # likely an IOError because no translation file found
    print('%s: Cannot initialize translation engine from path %s; using original texts (error following).' % (__file__, LocalesPath))
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
    NewIndicator = 'new'  # indicates a newly imported media
    NameSeparator = '-'  # to separate identifier parts such as name, scene, year, month, day
    ElementSeparator = '.'  # to separate elements
    FormatNumber = '%03d'  # format string for number ensuring uniqueness of pathname



# Class Variables
    ImageFilerModel = None  # to access legal names 
    MoveToLocations = OrderedDict()  # last move-to locations for repeating; no concurrent usage of subclasses!
    
    
# Class Methods
    @classmethod
    def setModel(self, model):
        """Set up the MediaOrganization for use with model.
        """
        self.ImageFilerModel = model


    @classmethod
    def getNamePartsInPathName(self, path):
        """Return all words in String path.
        
        Illegal words, such as extension and camera identifiers, are ignored.
     
        Return List of String
        """
        words = []
        for word in re.split(r'[\W_/\\]+', path, flags=re.UNICODE):
            if (not self.isIgnoredNamePart(word)):
                words.append(word)
        return(words)


    @classmethod
    def isIgnoredNamePart(self, namePart):  # @UnusedVariable
        """Check whether namePart can be a name element as part of a pathname.
        
        String namePart        
        Returns a Boolean indicating whether namePart can be ignored.
        """
        if ((namePart == '')  # emtpy string
            or Entry.isLegalExtension(namePart)  # known file types
            or re.match(r'CAM\d+|IMG|HPIM\d+', namePart, re.IGNORECASE)):  # camera identifiers
            return(True)
        else:
            return(False)


    @classmethod
    def constructPath(self, **kwargs):
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
            result = self.ImageFilerModel.getRootDirectory()
        result = os.path.join(result, self.constructPathForOrganization(**kwargs))
        number = None
        if (('makeUnique' in kwargs)
            and kwargs['makeUnique']):
            number = 1
            while (0 < len(glob.glob(result + self.NameSeparator + (self.FormatNumber % number) + '*'))):
                number = (number + 1)
        elif (('number' in kwargs)
              and kwargs['number']):
            number = kwargs['number']
        if (number):
            number = int(number)
            result = (result + self.NameSeparator + (self.FormatNumber % number))
        if (('elements' in kwargs)
            and kwargs['elements']):
            result = (result + kwargs['elements'])
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
    def constructPathFromImport(cls, importParameters, sourcePath, level, baseLength, targetDir, illegalElements):
        """Construct a pathname to import media at sourcePath to. 
        
        Importing.ImportParameterObject importParameters
        String sourcePath is the pathname of the image
        Number level counts the embedding from the initial import directory
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir is the pathname of the directory to import into
        Dictionary illegalElements collects a mapping of illegal elements to source pathnames
        
        Return a String containing the new absolute pathname
        """
        raise NotImplementedError


    @classmethod
    def getGroupFromPath(cls, path):  # @UnusedVariable
        """Retrieve the group into which media at path shall be included.
        
        Fallback implementation which returns the root node.
        
        String path contains the media's file path
        Returns a MediaFiler.Group instance
        """
        return(cls.ImageFilerModel.getRootEntry())


    @classmethod
    def importImage(cls, importParameters, sourcePath, level, baseLength, targetDir, illegalElements):
        """Import image at sourcePath, i.e. move to new location in model's directory.
        
        Importing.ImportParameterObject importParameters
        String sourcePath is the pathname of the image
        Number level counts the embedding from the initial import directory
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir is the pathname of the directory to import into
        Dictionary illegalElements collects a mapping of illegal elements to source pathnames
        """
        newPath = cls.constructPathFromImport(importParameters, sourcePath, level, baseLength, targetDir, illegalElements)
        importParameters.logString('Importing "%s"\n       as "%s"\n' % (sourcePath, newPath))
        if (not importParameters.getTestRun()):
            try:
                (head, tail) = os.path.split(newPath)  # @UnusedVariable
                if (not os.path.exists(head)):
                    os.makedirs(head)
                shutil.copy2(sourcePath, newPath)  # os.rename(sourcePath, newPath)
                if (importParameters.getDeleteOriginals()):
                    os.remove(sourcePath)
            except Exception as e:
                print('Error renaming "%s"\n            to "%s"' % (sourcePath, newPath))
                raise e


    @classmethod
    def registerMoveToLocation(cls, year, month, day, name, scene):
        """Store information where media was moved to, for retrieval as targets for subsequent moves.
        
        Subclasses must pick appropriate parameters.
        """
        #raise NotImplementedError
        pass


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        """
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.NameSeparator), 
                                      flag=(wx.ALIGN_CENTER_VERTICAL))
        aMediaNamePane.numberInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(60,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.numberInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.numberInput, flag=(wx.ALIGN_CENTER_VERTICAL))



# Lifecycle
    def __init__(self, anEntry, aPath):
        """Create a MediaOrganization instance to go with anEntry.
        
        MediaFiler.Entry anEntry is the group, image, or movie to be organized
        String aPath contains the path for anEntry
        Returns a MediaFiler.MediaOrganization instance
        """
        # internal state
        self.context = anEntry
        self.path = os.path.normpath(aPath)
        self.number = ''
        unconsumed = self.setIdentifiersFromPath(self.context.getOrganizationIdentifier())
        unconsumed = self.setNumberFromPath(unconsumed)
        return(None)



# Setters
    def setIdentifiersFromPath(self, path):
        """Extract identifiers relevant for the organization from path & return unconsumed part of path. 
        
        Trailing number will be recovered later and should not be extracted.
        
        Return String
        """
        raise BaseException('Subclass must implement')


    def setNumberFromPath(self, pathRest):
        """Check whether pathRest begins with a 3-digit number, store it if so, and return the unconsumed rest.
        
        Assumes that Entry.NameSeparator introduces the number.
        
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
            kwargs['elements'] = self.context.getElementString()
        if (not 'extension' in kwargs):
            kwargs['extension'] = self.context.getExtension()
        return(self.constructPath(**kwargs))


# Getters
    def getPath(self):
        return(self.path)


    def getNumber(self):
        if (self.number):
            return(int(self.number))
        else:
            return(None)


    def getNumberString(self):
        return(self.number)



    # These getters must be defined in the respective subclasses
    def extendContextMenu(self, menu):
        pass
    def runContextMenuItem(self, menuId, parentWindow):  # @UnusedVariable
        raise NotImplementedError
    # OrganizationByName only
    def getName(self):
        return(None)
    def getScene(self):
        return(None)
    def isSingleton(self):
        return(False)
    # OrganizationByDate only
    def getYear(self):
        return(None)
    def getMonth(self):
        return(None)
    def getDay(self):
        return(None)
    def getYearString(self):
        return(None)
    def getMonthString(self):
        return(None)
    def getDayString(self):
        return(None)
    


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
            if ((self.NewIndicator in self.context.getElements())
                and (not self.NewIndicator in otherEntry.getElements())):
                print('Keep   "%s"\nremove "%s"' % (otherEntry.getPath(), self.context.getPath()))
                newPath = otherEntry.getPath()
            elif ((not self.NewIndicator in self.context.getElements())
                  and (self.NewIndicator in otherEntry.getElements())):
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



# Internal - to change without notice
class OrganizationByName(MediaOrganization):
    """A strategy to organize media by name.
    
    - There is a list of legal names.
    - Media is identified by name, scene, number, and elements. 
    - Media are stored in folders per name, which are stored in folders per 1st letter of name. No further folder levels.
    - Elements are allowed on media file names only.
    """



# Constants
    FormatScene = '%02d'  # format string for scene number



# Class Methods
    @classmethod
    def setModel(self, model):
        """Also load the legal names. 
        
        MediaCollection model
        """
        # inheritance
        super(self, self).setModel(model)
        # internal state
        self.nameHandler = MediaNameHandler(Installer.getNamesFilePath())


    @classmethod
    def constructPathForOrganization(self, **kwargs):
        """
        String name
        Number scene
        """
        result = None
        if (('name' in kwargs)
            and (kwargs['name'] <> None)
            and (kwargs['name'] <> '')):
            letter = kwargs['name'][0]
            result = os.path.join(letter, kwargs['name'])
        else:
            logging.error('OrganizationByName.constructPathForOrganization(): No name given!')
            return(None)
        if (('scene' in kwargs)
            and kwargs['scene']):
            try:
                scene = (self.FormatScene % (int(kwargs['scene'])))
            except: 
                scene = self.NewIndicator
            result = os.path.join(result, scene)
        else:  # no scene given yields a singleton
            pass
        return(result)


    @classmethod
    def constructPathFromImport(self, importParameters, sourcePath, level, baseLength, targetDir, illegalElements):  
        """Import image at sourcePath.
        """
        pathInfo = {'rootDir': targetDir}
        singleton = True
        if (level == 0):  # not embedded, is a single
            # determine name of image
            pathInfo['name'] = self.deriveName(importParameters.log, sourcePath[baseLength:])
            if (not pathInfo['name']):
                importParameters.logString('Cannot determine new name for "%s", terminating import!' % sourcePath)
                return
            groupExists = os.path.isdir(self.constructPathForOrganization(**pathInfo))
            singleExists = (len(glob.glob(self.constructPathForOrganization(**pathInfo) + MediaOrganization.NameSeparator + '*')) > 0)
            if (singleExists):  # a single of this name exists, turn into group to move into it
                importParameters.logString('OrganizationByName: Cannot merge two singles into group (NYI)!')
                return
            elif (groupExists):  # a group of this name exists, move into it
                importParameters.logString('Existing name "%s" used in "%s"' % (pathInfo['name'], sourcePath))
                pathInfo['scene'] = self.NewIndicator
                singleton = False
            else:  # neither Single nor Group exist, create singleton
                pass
        else:  # embedded, is inside a group, name already contained in targetDir
            singleExists = (len(glob.glob(targetDir + MediaOrganization.NameSeparator + '*')) > 0)
            if (singleExists):  # a single of this name exists, turn into group to move into it
                importParameters.logString('OrganizationByName: Cannot merge single with group (NYI)!')
                return                
            else:  # no Single exists, put into the group
                self.ensureDirectoryExists(importParameters.log, importParameters.getTestRun(), targetDir, None)
                pathInfo['scene'] = self.NewIndicator
                singleton = False
        # determine extension
        (dummy, extension) = os.path.splitext(sourcePath)  # @UnusedVariable
        pathInfo['extension'] = extension[1:].lower() 
        # determine elements
        pathInfo['elements'] = self.ImageFilerModel.deriveElements(importParameters, 
                                                                   sourcePath[:-len(extension)], 
                                                                   baseLength, 
                                                                   False, 
                                                                   illegalElements)
        # add new indicator as needed
        if (singleton):
            if (importParameters.getMarkAsNew()
                and (not Entry.NameSeparator in pathInfo['elements'])):
                pathInfo['elements'] = (pathInfo['elements'] + self.ElementSeparator + self.NewIndicator)
        else:  # in a Group, create new number
            pathInfo['makeUnique'] = True
        # rename
        newPath = self.constructPath(**pathInfo)
        return(newPath)


    @classmethod
    def getGroupFromPath(cls, path):
        """Return the Group representing the name in path. Create it if it does not exist.
        
        String path filename of media (may be a folder or a file)
        Returns a MediaFiler.Group
        Raises ValueError 
        """
        parent = None
        name = cls.deriveName(StringIO.StringIO(), path)
        if (os.path.join(name, '') in path):  # if name is a directory, path indicates a media group
            group = cls.ImageFilerModel.getEntry(group=True, name=name)
            if (not group):
                group = Group.createFromName(cls.ImageFilerModel, name)
                parent = cls.ImageFilerModel.getEntry(group=True, name=name[0:1])
                if (parent == None):
                    raise ValueError
                group.setParentGroup(parent)
        else:
            group = cls.ImageFilerModel.getEntry(group=True, name=name[0:1])
        if (not group):
            raise ValueError
        return(group)


    @classmethod
    def ensureDirectoryExists(self, log, testRun, parentDir, dirName):  # @UnusedVariable
        """Ensure the directory indicated by parentDir/dirName exists.
        
        StringIO log collects all messages.
        Boolean testRun indicates whether changes are allowed
        String parentDir contains the path to the parent directory
        String dirName contains the name of the last directory, or None  
        """
        if (dirName):
            newDir = os.path.join(parentDir,
                                  dirName[0],
                                  dirName)
        else:
            newDir = parentDir
        #log.write('OrganizationByName.ensureDirectoryExists of "%s"\n' % newDir)
        if (not testRun):
            if (not os.path.exists(newDir)):
                os.makedirs(newDir)
        return(newDir)


    @classmethod
    def deriveName(self, log, path):
        """Derive the name under which the file at path shall be imported.
         
        StringIO log collects all messages.
        String path contains the name of the file/directory to create a new name for.
        
        Return a String containing the legal name, or None if no names are free anymore. 
        """
        if (path.find(self.ImageFilerModel.getRootDirectory()) <> 0):
            print('OrganizationByName.deriveName(): Outside of root directory: "%s"' % path)
        else:
            path = path[len(self.ImageFilerModel.getRootDirectory()):]
        newName = None # safe start state
        # split old path into elements
        words = self.getNamePartsInPathName(path)
        # search for legal name in path
        for word in words: 
            word = word.lower()
            #log.write(' checking "%s" for name-ness' % word)
            if (self.nameHandler.isNameLegal(word)):  # name given
                if (newName == None):  # first name found
                    #log.write(', accepting it as first name\n')
                    newName = word
                else:  # already found a name, stick to it
                    #log.write(', found it a second time\n')
                    if (newName <> word):
                        log.write('File "%s" contains names "%s" (chosen) and "%s" (ignored)\n' % (path, newName, word))
            else:
                #log.write(', no name :-(\n')
                pass    
        # if none found, pick random one
        if (newName == None):  # no name found, randomly select unused one
            newName = self.nameHandler.getFreeName()
            if (newName == None):  # no more free names
                log.write('No more free names.\n')
            else:
                log.write('Choosing free name "%s" for file "%s"\n' % (newName, path))
        elif (self.nameHandler.isNameFree(newName)):  # old name exists and is still free
            log.write('Found free legal name "%s" in file "%s"\n' % (newName, path))
            self.nameHandler.registerNameAsUsed(newName) 
        else: # old name exists but is occupied
            log.write('Existing name "%s" used in file "%s"\n' % (newName, path))
        return(newName)


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        """
        # name
        aMediaNamePane.identifierString = wx.StaticText(aMediaNamePane, -1, '--')
        aMediaNamePane.GetSizer().Add(aMediaNamePane.identifierString, flag = (wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, '/'), flag=(wx.ALIGN_CENTER_VERTICAL))
        #scene
        aMediaNamePane.sceneInput = wx.TextCtrl (aMediaNamePane, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.sceneInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.sceneInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # number
        # TODO: super(OrganizationByName, cls).initNamePane(aMediaNamePane)
        MediaOrganization.initNamePane(aMediaNamePane)



# Lifecycle
    def __init__(self, anEntry, aPath):
        """Create a OrganizationByName instance to go with anEntry.
        """
        # inheritance
        super(OrganizationByName, self).__init__(anEntry, aPath)
        # internal state
        self.__class__.nameHandler.registerNameAsUsed(self.getName())
        return(None)



# Setters
    def setIdentifiersFromPath(self, path):
        """Isolate name and scene (if any) from path, and return remaining part of path.

        path String relative pathname of file, with leading model root directory and trailing extension removed
        
        Returns a String 
        """
        self.name = ''
        self.scene = ''
        # first try: '/letter/name/scene-' is a Single inside a Group
        match = re.search(r"""([a-z])               # single-letter directory = \1
                              \\((\1[a-z]+)[0-9]?)  # directory with name = \3 and optional digit, all captured in \2
                              \\((\d\d)|new)        # two-digit number or "new" = \4
                              ([^\\]*)$             # non-directories until EOL = \6
                           """, 
                          path,
                          re.VERBOSE)
        if (match  # path is for an image in a group of images with the same name
            and self.nameHandler.isNameLegal(match.group(3))):  # and name is legal
            self.name = match.group(2)
            self.scene = match.group(4)
            rest = match.group(6)
        else:  # second try: '/letter/name' is a singleton Single
            match = re.search(r"""([a-z])               # single-letter directory = \1 
                                  \\((\1[a-z]+)[0-9]?)  # directory with name = \3 and optional digit, all captured in \2
                                  ([^\\]*)$             # non-directories until EOL = \4
                               """, 
                              path, 
                              re.VERBOSE)
            if (match  # path is for an single named image 
                and self.nameHandler.isNameLegal(match.group(3))):  # and name is legal
                self.name = match.group(2)
                rest = match.group(4)
            else:  # third try: '/letter' is a Group
                match = re.search(r'''^([a-z])$         # single letter directory = \1 
                                   ''', 
                                   path, 
                                   re.VERBOSE)
                if (match):
                    self.name = match.group(1)
                    rest = ''
                else:  # no match, or illegal name
                    logging.info('OrganizationByName.setIdentifiersFromPath(): Cannot extract identifiers from "%s"' % path)
                    rest = path  # neither image nor group, nothing consumed
        return(rest)


    def relabelToScene(self, newScene):
        """Relabel all media in the same scene as self.context to newScene
        
        String newScene contains the number of the new scene 
        """
        #print('Relabelling scene %s to %s' % (self.getScene(), newScene))
        parentGroup = self.context.getParentGroup()
        for entry in parentGroup.getSubEntries():
            if (entry.getScene() == self.getScene()):
                entry.renameTo(makeUnique=True, scene=newScene)



# Getters
    def constructPathForSelf(self, **kwargs):
        """
        """
        if (not 'name' in kwargs):
            kwargs['name'] = self.getName()
        if (not 'scene' in kwargs):
            kwargs['scene'] = self.getScene()
        return(super(OrganizationByName, self).constructPathForSelf(**kwargs))


    def extendContextMenu(self, menu):
        """Extend the context menu to contain functions relevant for organization by name.
        
        MediaFiler.Entry.Menu menu 
        """
        menu.Append(GUIId.RandomName, GUIId.FunctionNames[GUIId.RandomName])
        menu.Append(GUIId.ChooseName, GUIId.FunctionNames[GUIId.ChooseName])
        menu.AppendSeparator()
        # functions applicable to singletons, i.e. media outside groups
        if (self.context.isSingleton()):
            menu.Append(GUIId.ConvertToGroup, GUIId.FunctionNames[GUIId.ConvertToGroup])
        # functions applicable to Singles inside named Groups
        if ((not self.context.isGroup())
            and (not self.context.isSingleton())):
            sceneMenu = Menu()
            sceneId = GUIId.SelectScene
            for scene in self.context.getParentGroup().getScenes():
                if (sceneId <= (GUIId.SelectScene + GUIId.MaxNumberScenes)):  # respect max number of scenes in menu
                    #print('Putting %d into scene menu' % sceneId)
                    sceneMenu.Append(sceneId, scene)
                    if (scene == self.getScene()):
                        sceneMenu.Enable(sceneId, False)
                    sceneId = (sceneId + 1)
            if (sceneId > GUIId.SelectScene):  # scenes exist
                menu.insertAfterId(GUIId.ChooseName, 
                                   newText=GUIId.FunctionNames[GUIId.RelabelScene], 
                                   newId=GUIId.RelabelScene)
                menu.insertAfterId(GUIId.ChooseName, 
                                   newText=GUIId.FunctionNames[GUIId.SelectScene], 
                                   newMenu=sceneMenu)


    def runContextMenuItem(self, menuId, parentWindow):  # @UnusedVariable
        """Run the functions for the menu items added in extendContextMenu()
        """
        if ((menuId == GUIId.ChooseName)
            or (menuId == GUIId.RandomName)):
            if (menuId == GUIId.ChooseName):
                newName = self.askNewName(parentWindow)
            else:
                newName = self.nameHandler.getFreeName()
            if (newName):
                kwargs = {'name': newName}
                if (self.isSingleton()
                    or (not self.context.isGroup())):
                    kwargs['elements'] = self.context.getElements()
                    newEntry = self.context.model.getEntry(name=newName)
                    if (newEntry): 
                        if (newEntry.isGroup()):  # newName used by Group
                            kwargs['scene'] = MediaOrganization.NewIndicator
                            kwargs['makeUnique'] = True
                        else:  # newName used by singleton
                            print('Merging two singletons NYI!')
                            return
                    else:  # newName free, create a singleton
                        kwargs['scene'] = None
                else:  # self.context is a Group
                    pass
                self.context.renameTo(**kwargs)
                self.context.model.setSelectedEntry(self.context)
        elif (menuId == GUIId.ConvertToGroup):
            print('Conversion of singleton to Group NYI!')
        elif (menuId == GUIId.RelabelScene):
            print('Relabelling scenes NYI!')
        elif ((GUIId.SelectScene <= menuId)
              and (menuId <= (GUIId.SelectScene + GUIId.MaxNumberScenes))):
            pass  # handled where?
        else:
            super(OrganizationByName, self).runContextMenu(menuId, parentWindow)


    def isSingleton(self):
        """Indicate whether self's context is the only media for its name. 
        
        Returns a Boolean
        """
        if (self.context.isGroup()):
            return(False)
        elif (self.getScene()
              and (self.getScene() <> '')):
            return(False)
        return(True)


    def getName(self):
        return(self.name)
    
    
    def getScene(self):
        # TODO: make getScene() return None if no scene defined, add getSceneString for this semantics
        return(self.scene)

    
    def getScenes(self):
        """Return a sorted list of scenes contained in self, if self is a Group.
        
        Return List of String
        """
        result = []
        if (self.context.isGroup()):
            for subEntry in self.context.getSubEntries():
                scene = subEntry.organizer.getScene()
                if (not (scene in result)):
                    result.append(scene)
            result.sort()
        return(result)

    

# Other API Funcions
    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        super(OrganizationByName, self).setValuesInNamePane(aMediaNamePane)
        aMediaNamePane.identifierString.SetLabel(self.getName())
        aMediaNamePane.sceneInput.SetValue(self.getScene())
        aMediaNamePane.sceneInput.Enable(not (self.context.isGroup()
                                              or self.isSingleton()))  # TODO: wrong for singletons


    def getValuesFromNamePane(self, aMediaNamePane):
        """
        """
        result = super(OrganizationByName, self).getValuesFromNamePane(aMediaNamePane)
        # result['name'] = aMediaNamePane.identifierString.GetLabel()  TODO: make interactive?
        scene = aMediaNamePane.sceneInput.GetValue()
        if (scene == ''):
            result['scene'] = None
        else: 
            result['scene'] = scene
        return(result)


    
# Internal - to change without notice
    def askNewName(self, parentWindow):
        """User wants to rename media. Ask for new name. 
        
        Returns String containing new name, or None if user cancelled. 
        """
        dialog = wx.TextEntryDialog(parentWindow, _('Enter New Name'), _('Choose Name'), '')
        ok = True
        newName = None
        while (ok and 
               (not self.nameHandler.isNameLegal(newName))):
            ok = (dialog.ShowModal() == wx.ID_OK)
            if (ok):
                newName = dialog.GetValue()
                if (not self.nameHandler.isNameLegal(newName)):
                    dialog.SetValue('%s is not a legal name' % newName)
                    newName = None
        dialog.Destroy()
        return(newName)



class OrganizationByDate(MediaOrganization):
    """A strategy to organize media by date.
    
    - Media is identified by year, month, day, number, and elements, all optional.
    - Media are stored in folders per year, per month, per day.
    - Elements are allowed on media names only.
    """


# Constants
    # format strings for date output
    FormatYear = '%04d'
    FormatMonth = '%02d'
    FormatYearMonth = (FormatYear + MediaOrganization.NameSeparator + FormatMonth)
    FormatDay = '%02d'
    FormatYearMonthDay = (FormatYearMonth + MediaOrganization.NameSeparator + FormatDay)
    UnknownDateName = (FormatYear % 0)
    # RE patterns to recognize dates
    YearString = '((?:' + UnknownDateName + ')|(?:(?:18|19|20)\d\d))'  # 4-digit year
    ReducedYearString = r'[/\\](\d\d)'  # 2-digit year, only allowed at beginning of path component
    MonthString = '[01]\d'  # 2-digit month
    DayString = '[0123]\d'  # 2-digit day
    SeparatorString = r'[-_:/\.\\]'  # separator characters
    YearPattern = re.compile('%s(?!\d)' % YearString)
    ReducedYearPattern = re.compile('%s(?!\d)' % ReducedYearString)
    MonthPattern = re.compile('%s%s(%s)(?!\d)' % (YearString, SeparatorString, MonthString))
    ReducedMonthPattern = re.compile(r'%s%s(%s)(?!\d)' % (ReducedYearString, SeparatorString, MonthString))
    DayPattern = re.compile('%s(%s)(%s)\\2(%s)(?!\d)' % (YearString, SeparatorString, MonthString, DayString))
    ReducedDayPattern = re.compile('%s(%s)(%s)\\2(%s)(?!\d)' % (ReducedYearString, SeparatorString, MonthString, DayString))



# Variables
# Class Methods
    @classmethod
    def constructPathForOrganization(self, **kwargs):
        """
        Number year
        Number month
        Number day
        """
        if (('year' in kwargs)
            and kwargs['year']):
            year = kwargs['year']
        else:
            year = int(self.UnknownDateName)
        result = (self.FormatYear % year)
        if (('month' in kwargs)
            and kwargs['month']):
            month = kwargs['month']
            result = os.path.join(result, (self.FormatYearMonth % (year, month)))
            if (('day' in kwargs)
                and kwargs['day']):
                result = os.path.join(result, 
                                      (self.FormatYearMonthDay % (year, month, kwargs['day'])),
                                      (self.FormatYearMonthDay % (year, month, kwargs['day'])))
            else:
                result = os.path.join(result, 
                                      (self.FormatYearMonth % (year, month)))
        else:
            result = os.path.join(result,
                                  (self.FormatYear % year))
        return(result)


    @classmethod
    def constructPathFromImport(self, importParameters, sourcePath, level, baseLength, targetDir, illegalElements):  # @UnusedVariable
        """
        """
        # determine date of image
        (year, month, day) = self.deriveDate(importParameters.log, sourcePath, importParameters.getPreferPathDateOverExifDate())
        # determine extension
        (dummy, extension) = os.path.splitext(sourcePath)
        extension = extension.lower() 
        # determine elements
        newElements = self.ImageFilerModel.deriveElements(importParameters, 
                                                          sourcePath[:-len(extension)], 
                                                          baseLength, 
                                                          True, 
                                                          illegalElements)
        if (importParameters.getMarkAsNew()
            and (not self.NewIndicator in newElements)):
            newElements = (newElements + Entry.NameSeparator + self.NewIndicator)
        # ensure uniqueness via number
        newPath = self.constructPath(rootDir=targetDir,
                                year=year,
                                month=month,
                                day=day,
                                elements=newElements,
                                extension=extension[1:],
                                makeUnique=True)
        # rename
        return(newPath)


    @classmethod
    def getGroupFromPath(cls, path):
        """
        """
        (year, month, day, pathRest) = cls.deriveDateFromPath(StringIO.StringIO(), path)  # @UnusedVariable
        group = cls.ImageFilerModel.getEntry(group=True, year=year, month=month, day=day)
        if (group):
            return(group)
        else:
            return(super(OrganizationByDate, cls).getGroupFromPath(path))


    @classmethod
    def ensureDirectoryExists(self, log, testRun, rootDirectory, year, month, day):  # @UnusedVariable 
        """Ensure the directory indicated by a date exists.
        
        StringIO log collects all messages.
        Boolean testRun indicates whether changes are allowed
        String rootDirectory contains the path to the model's root directory
        String year contains the year, or 'undated' 
        String or None month, day contain the month and day, if any 
        """
        newDir = rootDirectory
        if (year):  # for safety, should at least be "undated"
            newDir = os.path.join(newDir, year)
            if (month):
                newDir = os.path.join(newDir, "%s-%s" % (year, month))
                if (day):
                    newDir = os.path.join(newDir, "%s-%s-%s" % (year, month, day))
        #log.write('Ensuring existence of "%s"\n' % newDir)
        if (not testRun):
            if (not os.path.exists(newDir)):
                os.makedirs(newDir)
        return(newDir)


    @classmethod
    def deriveDate(self, log, path, preferPathDate=True):
        """Derive a date from the file at path. 
        
        If a date can be derived from the path, it takes precedence over a date derived from the EXIF image data. 
        year is guaranteed to contain a String; month and day may be None. 
        
        StringIO log collects messages.
        String path contains the file path.
        Boolean preferPathDate indicates that a date derived from path takes precedence over a date derived from EXIF data
        
        Returns a tuple (year, month, day) which either are a Number or None (if not defined). 
        """
        # default values
        year = int(self.UnknownDateName)
        month = None
        day = None
        datesDiffer = False
        exifMoreSpecific = False
        # determine dates
        exifDate = self.deriveDateFromFile(log, path)
        pathDate = self.deriveDateFromPath(log, path)
        if ((exifDate[0] <> None)
            and (pathDate[0] <> self.UnknownDateName)
            and ((exifDate[0] <> pathDate[0])
                 or (exifDate[1] <> pathDate[1])
                 or (exifDate[2] <> pathDate[2]))):
            datesDiffer = True
        # select date
        if (preferPathDate):  # date derived from path takes precedence
            if (pathDate[0] <> self.UnknownDateName):
                (year, month, day, dummy) = pathDate
                # if exif date is more specific than path date, use it
                if (year == exifDate[0]):
                    if (month == None):
                        exifMoreSpecific = True
                        (month, day) = exifDate[1:]
                    elif (month == exifDate[1]):
                        if (day == None):
                            exifMoreSpecific = True
                            day = exifDate[2]
            elif (exifDate[0] <> None):
                (year, month, day) = exifDate
        else:  # date derived from EXIF takes precedence
            if (exifDate[0]):
                (year, month, day) = exifDate
            elif (pathDate[0] <> self.UnknownDateName):
                (year, month, day, dummy) = pathDate
        if (exifMoreSpecific):
            log.write('EXIF (%s) more specific than path (%s) in file "%s"\n' % (exifDate, pathDate, path))
        elif (datesDiffer):
            log.write('EXIF (%s) and path (%s) differ in file "%s"\n' % (exifDate, pathDate, path))
        if (year):
            year = int(year)
        if (month):
            month = int(month)
        if (day):
            day = int(day)
        return(year, month, day)


    @classmethod
    def deriveDateFromFile(self, log, path):  # @UnusedVariable
        """Determine date of image from EXIF information.
        
        StringIO log collects messages
        String path contains the absolute filename
        
        Returns a triple (year, month, day)
            which either contains year, month, and day as String
            or contains None for each entry
        """
        date = None
        if ((os.path.isfile(path))  # plain file
            and (path[-4:].lower() == '.jpg')):  # of type JPG
            with open(path, "rb") as f:
                try:
                    exifTags = exifread.process_file(f)
                except:
                    logging.warning('OrganizationByDate.deriveDateFromFile(): cannot read EXIF data from "%s"!' % path)
                    return(None, None, None)
                if (('Model' in exifTags)
                    and (exifTags['Model'] == 'MS Scanner')):
                    return(None, None, None)
                if (('Software' in exifTags)
                    and (0 <= exifTags['Software'].find('Paint Shop Photo Album'))):
                    return (None, None, None)
                if (exifTags):
                    for key in ['DateTimeOriginal',
                                # 'Image DateTime',  # bad date, changed by imaging software
                                'EXIF DateTimeOriginal', 
                                'EXIF DateTimeDigitized'
                                ]:
                        if (key in exifTags):
                            date = exifTags[key]
                            break
                    if (date):
                        match = self.DayPattern.search(str(date))
                        year = match.group(1)
                        month = match.group(3)
                        day = match.group(4)
                        if (year == self.UnknownDateName):
                            month = None
                            day = None
                        #log.write('Recognized date (%s, %s, %s) in EXIF data of file "%s"\n' % (year, month, day, path)) 
                        return(year, month, day)
        return(None, None, None)


    @classmethod
    def deriveDateFromPath(cls, log, path):  # @UnusedVariable
        """Determine the date of the file PATH. 
        
        StringIO log is used to report progress. 
        String path contains the absolute filename.  

        Return a triple (year, month, day, rest) where 
            year, month, and day are either String or None 
            rest is a String containing the rest of path not consumed by the match
        """
        # intialize variables
        year = None
        month = None
        day = None
        # search for date
        match = cls.DayPattern.search(path)
        usingReducedPattern = False
        if (match == None):
            usingReducedPattern = True
            match = cls.ReducedDayPattern.search(path)
        if (match):
            if (match.group(2) == '.'):  # German date format DD.MM.YY(YY)
                day = match.group(1)
                month = match.group(3)
                year = match.group(4)
            else:  # YY(YY)-MM-DD
                year = match.group(1)
                month = match.group(3)
                day = match.group(4)
            if (usingReducedPattern):
                assert (len(year) == 2), ('Reduced year "%s" too long in "%s"' % (year, path)) 
                year = cls.expandReducedYear(year)
            matched = (cls.FormatYearMonthDay % (int(year), int(month), int(day)))
            matchIndex = match.start()
        else:
            match = cls.MonthPattern.search(path)
            usingReducedPattern = False
            if (match == None):
                #log.write('Month pattern did not match in "%s"\n' % path)
                usingReducedPattern = True
                match = cls.ReducedMonthPattern.search(path)
            if (match):
                year = match.group(1)
                if (usingReducedPattern):  # fix two-digit year
                    assert (len(year) == 2), ('Reduced year "%s" too long in "%s"' % (year, path)) 
                    year = cls.expandReducedYear(year)
                month = match.group(2)
                matched = (cls.FormatYearMonth % (int(year), int(month)))
                matchIndex = match.start()
            else: 
                match = cls.YearPattern.search(path)
                usingReducedPattern = False
# A number starting the filename may be a year or just a counter - don't interpret as year
#                 if (match == None):
#                     usingReducedPattern = True
#                     match = cls.ReducedYearPattern.search(path)
                if (match):
                    year = match.group(1)
                    if (usingReducedPattern):
                        year = cls.expandReducedYear(year)
                    matched = (cls.FormatYear % int(year))
                    matchIndex = match.start()
                else:
                    (year, month, day) = cls.deriveDateWithMonthFromPath(log, path)
                    if (year):
                        matched = ''
                        matchIndex = -1
                    else:
                        year = cls.UnknownDateName
                        matched = ''
                        matchIndex = -1
        #log.write('Recognized (%s, %s, %s) in path "%s"\n' % (year, month, day, path)) 
        # skip to last occurrence of match
        rest = path
        while (matchIndex >= 0):  
            rest = rest[(matchIndex + len(matched)):]
            matchIndex = rest.find(matched)
        return (year, month, day, rest)


    @classmethod
    def deriveDateWithMonthFromPath(cls, log, path):  # @UnusedVariable
        """Determine the date of a media file from its path. 
        
        StringIO log is used to report progress. 
        String path contains the absolute filename.

        Return a triple (year, month, day, rest) where 
            year, month, and day are either String or None 
            rest is a String containing the rest of path not consumed by the match
        """
        # intialize variables
        year = None
        month = None
        day = None
        ms = [u'Januar', u'Februar', u'M�rz', u'April', u'Mai', u'Juni', u'Juli', u'August', u'September', u'Oktober', u'November', u'Dezember']
        for m in ms: 
            pattern = ('%s\W*(\d\d)' % m)
            match = re.search(pattern, path)
            if (match):
                year = cls.expandReducedYear(match.group(1))
                month = (cls.FormatMonth % (ms.index(m) + 1))
                break
            else: 
                pattern = ('%s[.]\W*(\d\d)' % m[0:3])
                match = re.search(pattern, path)
                if (match):
                    year = cls.expandReducedYear(match.group(1))
                    month = (cls.FormatMonth % (ms.index(m) + 1))
                    break
        return(year, month, day)


    @classmethod
    def expandReducedYear(cls, year):
        """Year has been specified with two digits only (i.e., 0-99). Prefix '19' or '20' as appropriate.
        
        String year
        Return String with a four digit year
        """
        currentYear = (datetime.date.today().year % 100)
        if (int(year) <= currentYear):  # add 2000 only if the result is earlier than current year
            year = ('20' + year)
        else:
            year = ('19' + year)
        return(year)


    @classmethod
    def registerMoveToLocation(cls, year=None, month=None, day=None, name=None, scene=None):
        """Store information where media was moved to, for retrieval as targets for subsequent moves.
        
        String year
        String month
        String day
        """
        if ((name <> None)
            or (scene <> None)):
            raise ValueError
        print('OrganizationByDate.registerMoveToLocation(): Registering (%s, %s, %s)' % (year, month, day))
        moveToLocation = {'year': year, 'month': month, 'day': day}
        path = cls.constructPathForOrganization(rootDir='', **moveToLocation)
        (dummy, menuText) = os.path.split(path)
        if (not menuText in cls.MoveToLocations):
            cls.MoveToLocations[menuText] = moveToLocation
            if (GUIId.MaxNumberMoveToLocations < len(cls.MoveToLocations)):
                cls.MoveToLocations.popitem(last=False)


    @classmethod
    def initNamePane(cls, aMediaNamePane):
        """Add controls to MediaNamePane to represent the organization's identifiers.
        """
        # year
        aMediaNamePane.yearInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(80,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.yearInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.yearInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.NameSeparator), flag=(wx.ALIGN_CENTER_VERTICAL))
        # month
        aMediaNamePane.monthInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.monthInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.monthInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # separator
        aMediaNamePane.GetSizer().Add(wx.StaticText(aMediaNamePane, -1, cls.NameSeparator), flag=(wx.ALIGN_CENTER_VERTICAL))
        # day
        aMediaNamePane.dayInput = wx.TextCtrl(aMediaNamePane, size=wx.Size(40,-1), style=wx.TE_PROCESS_ENTER)
        aMediaNamePane.dayInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.dayInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # generic 
        # TODO: super(OrganizationByName, cls).initNamePane(aMediaNamePane)
        MediaOrganization.initNamePane(aMediaNamePane)



# Lifecycle
# Setters
    def setIdentifiersFromPath(self, path):
        """Set year, month, day (if any) from path, and return remaining part of path.
        
        Returns a String containing the remaining part of PATH to the right of the last identifier found.
        """
        (year, month, day, rest) = self.deriveDateFromPath(StringIO.StringIO(), path)
        self.year = year
        self.month = month
        self.day = day
        year = (int(year) if year else None)
        month = (int(month) if month else None)
        day = (int(day) if day else None)
        self.dateTaken = PartialDateTime(year, month, day)
        return(rest)



# Getters
    def constructPathForSelf(self, **kwargs):
        """
        """
        checkMakeUnique = False
        if (not 'year' in kwargs):
            kwargs['year'] = self.getYear()
        elif (kwargs['year'] <> self.getYear()):
            checkMakeUnique = True
        if (not 'month' in kwargs):
            kwargs['month'] = self.getMonth()
        elif(kwargs['month'] <> self.getMonth()):
            checkMakeUnique = True
        if (not 'day' in kwargs):
            kwargs['day'] = self.getDay()
        elif (kwargs['day'] <> self.getDay()):
            checkMakeUnique = True
        if (checkMakeUnique
            and (not 'number' in kwargs)):
            kwargs['makeUnique'] = True
        return(super(OrganizationByDate, self).constructPathForSelf(**kwargs))


    def extendContextMenu(self, menu):
        """Extend the context menu to contain functions relevant for organization by date.

        MediaFiler.Entry.Menu menu 
        Return nobi.wxExtensions.Menu (which is a wx.Menu)
        """
        moveToMenu = Menu()
        moveToId = GUIId.SelectMoveToLocation
        for menuText in sorted(self.__class__.MoveToLocations.keys()):
            if (moveToId <= (GUIId.SelectMoveToLocation + GUIId.MaxNumberMoveToLocations)):
                mtl = self.__class__.MoveToLocations[menuText]
                print('Adding move-to location "%s" into menu entry %s with id %d' % (mtl, menuText, moveToId))
                moveToMenu.Append(moveToId, menuText)
                if ((mtl['year'] == self.getYearString())
                    and (mtl['month'] == self.getMonthString())
                    and (mtl['day'] == self.getDayString())):
                    moveToMenu.Enable(moveToId, False)
                moveToId = (moveToId + 1)
        if (GUIId.SelectMoveToLocation < moveToId):  
            menu.AppendMenu(0, GUIId.FunctionNames[GUIId.SelectMoveToLocation], moveToMenu)
        return(menu)


    def runContextMenuItem(self, menuId, parentWindow):
        """Run functions to handle the menu items added in extendContextMenu()
        """
        if ((GUIId.SelectMoveToLocation <= menuId)
            and (menuId <= (GUIId.SelectMoveToLocation + GUIId.MaxNumberMoveToLocations))):
            mtlIndex = (menuId - GUIId.SelectMoveToLocation)
            mtlText = sorted(self.__class__.MoveToLocations.keys())[mtlIndex]
            mtl = self.__class__.MoveToLocations[mtlText]
            print('Moving "%s" to %s' % (self.getPath(), mtl))
            self.context.renameTo(makeUnique=True, **mtl)
        else:
            super(OrganizationByDate, self).runContextMenuItem(self, menuId, parentWindow)


    def getDateTaken(self):
        return(self.dateTaken)


    def getYear(self):
        if (((self.year <> None)
             and (int(self.year) <> self.dateTaken.getYear()))
            or ((self.year == None)
                and self.dateTaken.getYear())):
            print('OrganizationByDate.getYear(): explicit and PartialDateTime year do not match')
        if (self.year == None):
            return(None)
        else:
            return(int(self.year))

    
    def getYearString(self):
        if (self.dateTaken.getYear()):
            return(self.__class__.FormatYear % self.dateTaken.getYear())
        else:
            return(self.__class__.UnknownDateName)


    def getMonth(self):
        if (((self.month <> None)
             and (int(self.month) <> self.dateTaken.getMonth()))
            or ((self.month == None)
                and self.dateTaken.getMonth())):
            print('OrganizationByDate.getMonth(): explicit and PartialDateTime month do not match')
        if (self.month == None):
            return(None)
        else:
            return(int(self.month))
    

    def getMonthString(self):
        if (self.dateTaken.getMonth()):
            return(self.__class__.FormatMonth % self.dateTaken.getMonth())
        else:
            return(u'')

    
    def getDay(self):
        if (((self.day <> None)
             and (int(self.day) <> self.dateTaken.getDay()))
            or ((self.day == None)
                and self.dateTaken.getDay())):
            print('OrganizationByDate.getDay(): explicit and PartialDateTime day do not match')
        if (self.day == None):
            return(None)
        else:
            return(int(self.day))    


    def getDayString(self):
        if (self.dateTaken.getDay()):
            return(self.__class__.FormatDay % self.dateTaken.getDay())
        else:
            return(u'')



# Other API Funcions
    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        super(OrganizationByDate, self).setValuesInNamePane(aMediaNamePane)
        aMediaNamePane.yearInput.SetValue(self.getYearString())
        aMediaNamePane.monthInput.SetValue(self.getMonthString())
        aMediaNamePane.dayInput.SetValue(self.getDayString())


    def getValuesFromNamePane(self, aMediaNamePane):
        """
        
        Return Dictionary mapping String to values
            or None if field values are illegal
        """
        result = super(OrganizationByDate, self).getValuesFromNamePane(aMediaNamePane)
        year = aMediaNamePane.yearInput.GetValue()
        if (year == ''):
            result['year'] = None
        else:
            try:
                result['year'] = int(year)
            except:
                return(None)
        month = aMediaNamePane.monthInput.GetValue()
        if (month == ''):
            result['month'] = None
        else:
            try:
                result['month'] = int(month)
            except:
                return(None)
        day = aMediaNamePane.dayInput.GetValue()
        if (day == ''):
            result['day'] = None
        else:
            try:
                result['day'] = int(day)
            except: 
                return(None)
        return(result)



# Event Handlers
# Internal - to change without notice
