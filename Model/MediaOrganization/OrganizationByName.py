# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
import copy
import re
import os.path
import glob
import logging
import gettext
from collections import OrderedDict
import functools
from operator import indexOf
## Contributed 
#import wx
import wx.lib.masked
## nobi
from nobi.wx.Menu import Menu
from nobi.wx.Validator import TextCtrlIsIntValidator
## Project
from Model import Installer
from Model.MediaClassHandler import MediaClassHandler
from Model.MediaNameHandler import MediaNameHandler
from Model.MediaFilter import MediaFilter
from Model.MediaOrganization import MediaOrganization
from Model.Group import Group
from UI.MediaFilterPane import MediaFilterPane, FilterConditionWithMode, FilterCondition
import UI  # to access UI.PackagePath
from UI import GUIId



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANG']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at "%s"; using originals instead of locale %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3
def N_(message): return message




# Package Variables
Logger = logging.getLogger(__name__)



class OrganizationByName(MediaOrganization):
    """A strategy to organize media by name.
    
    - There is a list of legal names.
    - Media is identified by name, scene, number, and tags. 
    - Media are stored in folders per name, which are stored in folders per 1st letter of name. No further folder levels.
    - Tags are allowed on media file names only.
    """



# Constants
    FormatScene = '%02d'  # format string for scene number



# Class Methods
    @classmethod
    def setModel(self, aMediaCollection):
        """Also load the legal names. 
        
        aMediaCollection specifies the model
        """
        # inheritance
        super(self, self).setModel(aMediaCollection)
        # internal state
        self.setNameHandler()


    @classmethod
    def setNameHandler(self):
        """Set the class singleton name handler. 
        
        Even if a name handler was defined, there are no dependencies and it can be simply discarded.
        Registering names of all Entrys does not hurt, as there are none when the class is initialized via setModel()
        """ 
        path = Installer.getNamesFilePath()
        Logger.debug('OrganizationByName.setNameHandler(): Loading name handler from "%s"' % path)
        self.nameHandler = MediaNameHandler(path)
        Logger.debug('OrganizationByName.setNameHandler(): Registering names...')
        for entry in self.getModel(): 
            self.nameHandler.registerNameAsUsed(entry.getOrganizer().getName())
        Logger.debug('OrganizationByName.setNameHandler(): Names registered')


    @classmethod
    def getDescription(cls):
        """Return a description of the organization. 
        """
        return(_('organized by name, %d names used, %d free')
               % (cls.nameHandler.getNumberUsedNames(),
                  cls.nameHandler.getNumberFreeNames()))


    @classmethod
    def constructOrganizationPath(cls, **kwargs):
        """
        String name
        Number scene
        Return String 
        """
        if ((not 'name' in kwargs)
            or (not kwargs['name'])
            or (kwargs['name'] == '')):
            raise ValueError('OrganizationByName.constructOrganizationPath(): No name given!')        
        result = None
        letter = kwargs['name'][0]
        entry = cls.ImageFilerModel.getEntry(name=kwargs['name'])
        if ((entry
             and (entry.isGroup()))  # a group already exists, ensure scene parameter is defined 
            or (('scene' in kwargs)
                 and kwargs['scene'])
            or ('makeUnique' in kwargs)):  # no entry exists, but a group path is required
            if (('scene' in kwargs)
                and (kwargs['scene'] != None)
                and (kwargs['scene'] != '')):
                try:
                    scene = (cls.FormatScene % (int(kwargs['scene'])))
                except: 
                    scene = MediaClassHandler.ElementNew
            else:
                scene = MediaClassHandler.ElementNew
            result = os.path.join(letter, kwargs['name'], scene)
        else:  # no group exists, assume a singleton
            result = os.path.join(letter, kwargs['name'])
        return(result)


    @classmethod
    def pathInfoForImport(self, importParameters, sourcePath, level, oldName, pathInfo):
        """Override MediaOrganization.pathInfoForImport()
        
        Return None if no more names exist.
        """
        result = super(OrganizationByName, self).pathInfoForImport(importParameters, sourcePath, level, oldName, pathInfo)
        if (not 'name' in result):
            if ('rootDir' in pathInfo):
                baseLength = len(pathInfo['rootDir'])
            else: 
                Logger.error('OrganizationByName.pathInfoForImport(): Missing parameter "rootDir"!')
                baseLength = 0
            newName = self.deriveName(importParameters, sourcePath[baseLength:])
            if (newName == None):  # indicates no more free names
                result = None
                Logger.debug('OrganizationByName.pathInfoForImport(): No free name found')
            else:
                result['name'] = newName
                Logger.debug('OrganizationByName.pathInfoForImport(): Determined new name "%s"' % newName)
        else:
            Logger.debug('OrganizationByName.pathInfoForImport(): Found name "%s"' % result['name'])
        return(result)

        
    @classmethod
    def constructPathFromImport(cls, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):  
        """
        """
        pathInfo = copy.copy(targetPathInfo)
        if ('elements' in pathInfo):
            raise ('OrganizationByName.constructPathFromImport(): targetPathInfo may not contain "elements"!')
        if (not 'name' in pathInfo):
            raise ('OrganizationByName.constructPathFromImport(): targetPathInfo must contain "name"!')
        singleton = True
        if (level == 0):  # not embedded, single file to import
            groupExists = (importParameters.getModel().getEntry(name=pathInfo['name'], group=True) != None)
            singleExists = (len(glob.glob(cls.constructPath(**pathInfo) + MediaOrganization.IdentifierSeparator + '*')) > 0)
            if (singleExists):  # a single of this name exists, turn into group to move into it
                importParameters.logString('OrganizationByName: Cannot merge two singles into group (NYI)!')
                return
            elif (groupExists):  # a group of this name exists, move into it
                importParameters.logString('Existing name "%s" used in "%s"' % (pathInfo['name'], sourcePath))
                pathInfo['scene'] = MediaClassHandler.ElementNew
                pathInfo['makeUnique'] = True
                singleton = False
            else:  # neither Single nor Group exist, create singleton
                pass
        else:  # embedded, is inside an import folder, name already contained in targetDir
            singleExists = (len(glob.glob(targetDir + MediaOrganization.IdentifierSeparator + '*')) > 0)
            if (singleExists):  # a single of this name exists, turn into group to move into it
                importParameters.logString('OrganizationByName: Cannot merge single with group (NYI)!')
                return                
            else:  # no Single exists, put into the group
                cls.ensureDirectoryExists(importParameters.log, importParameters.getTestRun(), targetDir, None)
                match = re.search((pathInfo['name'] + MediaOrganization.IdentifierSeparator + '(\d\d)(?!\d)'),
                                  sourcePath)
                if (match): 
                    pathInfo['scene'] = int(match.group(1))
                else:
                    pathInfo['scene'] = MediaClassHandler.ElementNew
                singleton = False
        # determine extension
        (dummy, extension) = os.path.splitext(sourcePath)  # @UnusedVariable
        pathInfo['extension'] = extension[1:].lower() 
        # determine elements
        tagSet = cls.ImageFilerModel.deriveTags(importParameters,
                                                 sourcePath,
                                                 baseLength,
                                                 illegalElements)
        if (pathInfo['name'] in tagSet):
            tagSet.remove(pathInfo['name'])
        # add new indicator as needed
        if (singleton):
            if (importParameters.getMarkAsNew()):
                tagSet.add(MediaClassHandler.ElementNew)
        else:  # in a Group, create new number
            pathInfo['makeUnique'] = True
        # rename
        newPath = cls.constructPath(elements=tagSet,
                                     **pathInfo)
        return(newPath)


    @classmethod
    def getGroupFromPath(cls, path):
        """Return the Group representing the name in path. Create it if it does not exist.
        
        String path filename of media (may be a folder or a file)
        Returns a MediaFiler.Group
        Raises ValueError 
        """
        group = cls.ImageFilerModel.getEntry(group=True, path=path)
        if (group == None):
            group = Group(cls.ImageFilerModel, path)  # TODO: recursion unlimited when "random name" 
            groupPathPattern = os.path.join(cls.ImageFilerModel.getRootDirectory(), '[a-z]')
            print('OrganizationByName.getGroupFromPath(): Searching for path "%s"' % groupPathPattern)
            match = re.match(groupPathPattern, path)
            if (match):
                parent = cls.ImageFilerModel.getRootEntry()
            else: 
                (parentPath, name) = os.path.split(path)  # @UnusedVariable
                parent = cls.getGroupFromPath(parentPath)
                if (parent == None):
                    raise ValueError('OrganizationByName.getGroupFromPath(): Cannnot find parent Group for "%s"' % path)
            group.setParentGroup(parent)
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
    def deriveName(self, importParameters, path):
        """Derive the name under which the file at path shall be imported.
         
        ImportParameterObject importParameters provides log and test-run flag
        String path contains the name of the file/directory to create a new name for.
        Return String containing the legal name, or None if no names are free anymore. 
        """
        if (path.find(self.ImageFilerModel.getRootDirectory()) != 0):
            Logger.debug('OrganizationByName.deriveName(): Outside of root directory: "%s"' % path)
        else:
            path = path[len(self.ImageFilerModel.getRootDirectory()):]
        newName = None
        # search for legal name in path
        words = self.ImageFilerModel.getWordsInPathName(path)
        for word in words: 
            word = word.lower()
            if (self.nameHandler.isNameLegal(word)):  # name given
                if (newName == None):  # first name found
                    newName = word
                else:  # already found a name, stick to it
                    if (newName != word):
                        importParameters.logString('\nFile "%s" contains names "%s" (chosen) and "%s" (ignored)\n' % (path, newName, word))
        # if none found, pick random one
        if (newName == None):  # no name found, randomly select unused one
            newName = self.nameHandler.getFreeName()
            if (newName == None):  # no more free names
                importParameters.logString('\nNo more free names.\n')
            else:
                importParameters.logString('\nChoosing free name "%s" for file "%s"\n' % (newName, path))
                if (importParameters.getTestRun()):  # if only a test run, keep this as free name
                    self.nameHandler.registerNameAsFree(newName)
        elif (self.nameHandler.isNameFree(newName)):  # name exists and is still free
            importParameters.logString('\nFound free legal name "%s" in file "%s"\n' % (newName, path))
            if (not importParameters.getTestRun()): 
                self.nameHandler.registerNameAsUsed(newName)  # TODO: When importing an empty directory with a legal name, this registers the name, although there are no media with this name
        else: # name exists but is occupied
            if (self.getModel().getEntry(name=newName)):  # name is used (also considering number if it exists)
                importParameters.logString('\nExisting name "%s" used in file "%s"\n' % (newName, path))
            else:  # name not used with this number
                importParameters.logString('\nExisting name "%s" is used, but not with this number\n' % newName)
        return(newName)


    @classmethod
    def registerMoveToLocation(cls, pathInfo):
        """overwrite MediaOrganization.registerMoveToLocation()
        """
        register = OrderedDict()
        for value in ('name', 'scene'):
            if (value in pathInfo):
                register[value] = pathInfo[value]
        super(OrganizationByName, cls).registerMoveToLocation(register)


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
        aMediaNamePane.sceneInput = wx.TextCtrl(aMediaNamePane, 
                                                size=wx.Size(40,-1), 
                                                style=wx.TE_PROCESS_ENTER,
                                                validator=TextCtrlIsIntValidator(label=_('Scene'), 
                                                                                 minimum=1,
                                                                                 emptyAllowed=True))
        aMediaNamePane.sceneInput.Bind(wx.EVT_TEXT_ENTER, aMediaNamePane.onRename)
        aMediaNamePane.GetSizer().Add(aMediaNamePane.sceneInput, flag=(wx.ALIGN_CENTER_VERTICAL))
        # number
        # TODO: super(OrganizationByName, cls).initNamePane(aMediaNamePane)
        MediaOrganization.initNamePane(aMediaNamePane)


    @classmethod
    def initFilterPane(cls, aMediaFilterPane):
        """Add date filter to filter pane.
        """
        super(OrganizationByName, cls).initFilterPane(aMediaFilterPane)
        aMediaFilterPane.addCondition(SingletonFilter(aMediaFilterPane))
        aMediaFilterPane.addCondition(SceneFilter(aMediaFilterPane))
        aMediaFilterPane.addCondition(GroupSizeFilter(aMediaFilterPane))
        aMediaFilterPane.addSeparator()

    
    @classmethod
    def conditionsFromFilter(cls, aNewMediaFilterPane, aMediaFilter):
        """overwrite MediaOrganization.conditionsFromFilter
        """
        result = []  # super(OrganizationByName, cls).conditionsFromFilter(aNewMediaFilterPane, aMediaFilter)
        if (aMediaFilter.getFilterValueFor(FilterByName.ConditionKeySingle) != None):
            text = wx.StaticText(aNewMediaFilterPane, -1, '')
            if (aMediaFilter.getFilterValueFor(FilterByName.ConditionKeySingle)):
                text.SetLabel(_('Singleton required'))
            else:
                text.SetLabel(_('Singleton prohibited'))
            result.append(text)
        if (aMediaFilter.getFilterValueFor(FilterByName.ConditionKeyScene) != None):
            text = wx.StaticText(aNewMediaFilterPane, -1, (_('Scene %s') % aMediaFilter.getFilterValueFor(FilterByName.ConditionKeyScene)))
            result.append(text)
        if (aMediaFilter.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger) != None):
            text = wx.StaticText(aNewMediaFilterPane, -1, (_('Group with more than %s entries') % aMediaFilter.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger)))
            result.append(text)
        if (aMediaFilter.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller) != None):
            text = wx.StaticText(aNewMediaFilterPane, -1, (_('Group with less than %s entries') % aMediaFilter.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller)))
            result.append(text)
        return result



# Lifecycle
    def __init__(self, anEntry, aPath):
        """Create a OrganizationByName instance to go with anEntry.
        
        TODO: Ensure deletion of self's context is reflected by freeing up the name again
        """
        # inheritance
        super(OrganizationByName, self).__init__(anEntry, aPath)
        # internal state
        try:
            self.__class__.nameHandler.registerNameAsUsed(self.getName())
        except: 
            if (not self.context.isGroup()):
                Logger.warning('OrganizationByName(): "%s" is not a legal name in "%s"' % (self.getName(), anEntry.getPath()))
        return(None)



# Setters
    def setIdentifiersFromPath(self, path):
        """Isolate name and scene (if any) from path, and return remaining part of path.

        path String relative pathname of file, without leading root directory and trailing extension
        
        TODO: make independent from OS-dependent separator characters (/ vs. \)
        
        Returns a String 
        """
        self.name = ''
        self.scene = ''
        # first try: 'letter/name/scene-' is a Single inside a Group
        match = re.search(r"""([a-z])                  # single-letter directory = \1
                              \\((\1[a-z]+)[0-9]?)     # directory with name = \3 and optional digit, all captured in \2
                              \\((\d\d)|new)           # two-digit number or "new" = \4
                              ([^\\]*)$                # non-directories until EOL = \6
                           """, 
                          path,
                          re.VERBOSE)
        if (match
            and self.nameHandler.isNameLegal(match.group(3))):  # and name is legal
            self.name = match.group(2)
            self.scene = match.group(4)
            rest = match.group(6)
        else:  # second try: 'letter/name' is a singleton Single
            match = re.search(r"""([a-z])                  # single-letter directory = \1 
                                  \\((\1[a-z]+)[0-9]?)     # directory with name = \3 and optional digit, all captured in \2
                                  ([^\\]*)$                # non-directories until EOL = \4
                               """, 
                              path, 
                              re.VERBOSE)
            if (match 
                and self.nameHandler.isNameLegal(match.group(3))):  # and name is legal
                self.name = match.group(2)
                rest = match.group(4)
            else:  # third try: 'letter' is a Group
                match = re.search(r'''^([a-z])$         # single letter directory = \1 
                                   ''', 
                                   path, 
                                   re.VERBOSE)
                if (match):
                    self.name = match.group(1)
                    rest = ''
                elif (path == ''):  # fourth try: '' is the root node
                    self.name = ''
                    rest = ''
                else:  # no match, or illegal name
                    Logger.warning('OrganizationByName.setIdentifiersFromPath(): Cannot extract identifiers from "%s" (unknown name?)' % path)
                    rest = path  # neither image nor group, nothing consumed
        Logger.debug('OrganizationByName.setIdentifiersFromPath(): Resulted in name="%s", scene="%s", rest="%s"' 
                     % (self.name, self.scene, rest))
        return(rest)


    def relabelToScene(self, newScene):
        """Relabel all media in the same scene as self.context to newScene
        
        String newScene contains the number of the new scene 
        """
        oldScene = self.getScene()
        Logger.debug('OrganizationByName.relabelToScene(): Moving entries from scene %s to scene %s (from "%s")' 
                      % (oldScene, newScene, self.context.getPath()))
        parentGroup = self.getContext().getParentGroup()
        processIndicator = wx.GetApp()  # TODO: move out to UI packages
        if (processIndicator):
            processIndicator.beginPhase(len(parentGroup.getSubEntries()), (_('Renaming scene %s to %s') % (oldScene, newScene)))
        for entry in parentGroup.getSubEntries(filtering=False):
            if (processIndicator):
                processIndicator.beginStep()
            if (entry.getOrganizer().getScene() == oldScene):
                pathInfo = entry.getOrganizer().getPathInfo()
                pathInfo['scene'] = newScene
                pathInfo['makeUnique'] = True
                entry.renameTo(processIndicator=processIndicator, **pathInfo)



# Getters
    def isUnknown(self):
        """Return whether self is incompletely specified.

        Return Boolean
        """
        if (self.getScene() == MediaClassHandler.ElementNew):
            return(True)
        match = re.match(r'([^\d]+)\d*', self.getName())  # isolate name in name+number identifiers
        if (match == None):
            return(True)  # no name?
        else:
            if (not self.nameHandler.isNameLegal(match.group(1))):  # illegal name
                return(True)
        return(False)

    
    def matches(self, **kwargs):
        """override MediaOrganization.matches
        """
        return(((not 'name' in kwargs)
                or (kwargs['name'] == None)
                or (kwargs['name'] == self.getName()))
               and ((not 'scene' in kwargs)
                or (kwargs['scene'] == None)
                or (kwargs['scene'] == self.getScene())))


    def getPathInfo(self, filtering=False):
        """override MediaOrganization.getPathInfo(self)
        """
        result = MediaOrganization.getPathInfo(self, filtering)
        if (self.isSingleton()):
            try:
                del result['number']
            except:
                pass
        result['name'] = self.getName()
        if ((not self.isSingleton())
            and (not self.getContext().isGroup())):
            result['scene'] = self.getScene()
        return(result)


    def getNumbersInGroup(self):
        """Return the (ascending) list of Numbers in self's group.
        
        TODO: merge with MediaOrganization.getNumberedEntriesMap()
        
        TODO: Remove this when OrganizationByName uses embedded Groups for the scene, and let the Group
        list the numbers. 
        """
        return([e.getOrganizer().getNumber() 
                for e in self.getContext().getParentGroup().getSubEntries(filtering=False) 
                if ((not e.isGroup())
                    and (e.getOrganizer().getScene() == self.getScene()))])


    def extendContextMenu(self, menu):
        """Extend the context menu to contain functions relevant for organization by name.
        
        MediaFiler.Entry.Menu menu 
        """
        # media functions
        # structure functions
        menu.insertAfterId(GUIId.SelectMoveTo, 
                           newText=GUIId.FunctionNames[GUIId.RandomName], 
                           newId=GUIId.RandomName)
        menu.insertAfterId(GUIId.RandomName, 
                           newText=GUIId.FunctionNames[GUIId.ChooseName], 
                           newId=GUIId.ChooseName)
        if (self.getContext().isGroup()):
            menu.insertAfterId(GUIId.ChooseName, 
                               newText=GUIId.FunctionNames[GUIId.ConvertToSingle], 
                               newId=GUIId.ConvertToSingle)
            if (1 < len(self.context.getSubEntries(filtering=False))):
                menu.Enable(GUIId.ConvertToSingle, False)
        if (self.isSingleton()):
            menu.insertAfterId(GUIId.ChooseName, 
                               newText=GUIId.FunctionNames[GUIId.ConvertToGroup], 
                               newId=GUIId.ConvertToGroup)
        # group functions
        if ((not self.getContext().isGroup())
            and (not self.isSingleton())):
            menu.insertAfterId(GUIId.SelectMoveTo, 
                               newText=GUIId.FunctionNames[GUIId.AssignNumber], 
                               newMenu=self.deriveRenumberSubMenu())
            sceneMenu = Menu()
            sceneMenu.currentEntry = self.getContext()
            sceneList = self.getContext().getParentGroup().getOrganizer().getScenes()
            if (0 < len(sceneList)):
                for sceneStr in sceneList:
                    sceneNum = (0 if sceneStr == MediaClassHandler.ElementNew else int(sceneStr))
                    sceneMenu.Append(GUIId.SelectSceneIDs[sceneNum], sceneStr)
                    if (sceneStr == self.getScene()):
                        sceneMenu.Enable(GUIId.SelectSceneIDs[sceneNum], False)
                menu.insertAfterId(GUIId.SelectMoveTo, 
                                   newText=GUIId.FunctionNames[GUIId.RelabelScene], 
                                   newId=GUIId.RelabelScene)
                menu.insertAfterId(GUIId.SelectMoveTo, 
                                   newText=GUIId.FunctionNames[GUIId.SelectScene], 
                                   newMenu=sceneMenu)
        # delete functions


    def runContextMenuItem(self, menuId, parentWindow):  # @UnusedVariable
        """Run the functions for the menu items added in extendContextMenu()
        
        Return String to display a message to the user
            or None
        """
        message = None
        if ((menuId == GUIId.ChooseName)
            or (menuId == GUIId.RandomName)):
            newName = None
            if (menuId == GUIId.ChooseName):
                newName = self.askNewName(parentWindow)
            elif (menuId == GUIId.RandomName):
                newName = self.nameHandler.getFreeName()
                if (not newName):
                    message = _('No more free names!')
            if (newName):
                oldName = self.getName()
                pathInfo = self.getPathInfo()
                pathInfo['name'] = newName
                entry = self.getModel().getEntry(name=newName)
                if (entry):  # name exists
                    if (not entry.isGroup()):
                        try:
                            entry.getOrganizer().convertToGroup()
                        except BaseException as e:
                            message = ('Cannot convert "%s" to Group' % entry.getOrganizer().getName())
                            Logger.error('OrganizatonByName.runContextMenuEntry(): %s (error follows)\n%s' % (message, e))
                            return(message)
                    if (self.getContext().isGroup()):
                        pass  # scenes in group will be mapped to newly created scenes
                    else:  # either a Singleton or a Single extracted out of named Group
                        pathInfo['scene'] = MediaClassHandler.ElementNew
                        pathInfo['makeUnique'] = True                        
                else:  # name unused
                    if (not (self.isSingleton() 
                             or self.getContext().isGroup())):  # Single extracted out of a named Group
                        pathInfo['scene'] = None
                        pathInfo['number'] = None
                resultingSelection = self.getContext().renameTo(processIndicator=wx.GetApp(), **pathInfo)  # TODO: move out to UI packages
                if (resultingSelection):
                    self.getModel().setSelectedEntry(resultingSelection)
                else:
                    Logger.warn('OrganizationByName.runContextMenuItem(): Renaming did not return a new selection!')
                    self.getModel().setSelectedEntry(self.getContext())  # deprecate
                if (oldName != newName):
                    self.nameHandler.registerNameAsFree(oldName)
                    self.nameHandler.registerNameAsUsed(newName)
        elif (menuId == GUIId.ConvertToGroup):
            message = self.convertToGroup()
        elif (menuId == GUIId.RelabelScene):
            newScene = self.askNewScene(parentWindow)
            if (newScene):
                self.relabelToScene(newScene)
        # elif ((GUIId.SelectScene <= menuId)
        #       and (menuId <= (GUIId.SelectScene + GUIId.MaxNumberScenes))):
        #     newScene = self.getContext().getParentGroup().getOrganizer().getScenes()[menuId - GUIId.SelectScene]
        elif (menuId in GUIId.SelectSceneIDs):
            newScene = indexOf(GUIId.SelectSceneIDs, menuId)
            Logger.debug('OrganizationByName.runContextMenu(): Changing scene of "%s" to %s' % (self.getPath(), newScene))
            pathInfo = self.getPathInfo()
            pathInfo['scene'] = newScene
            pathInfo['makeUnique'] = True 
            self.getContext().renameTo(processIndicator=wx.GetApp(), **pathInfo)  # TODO: move out to UI packages
        else:
            super(OrganizationByName, self).runContextMenuItem(menuId, parentWindow)
        return(message)


    def isSingleton(self):
        """Indicate whether self's context is the only media for its name. 
        
        Returns a Boolean
        """
        if (self.context.isGroup()):
            return(False)
        elif (self.getScene()
              and (self.getScene() != '')):
            return(False)
        return(True)


    def getName(self):
        return(self.name)
    
    
    def getScene(self):
        # TODO: make getScene() return None if no scene defined, add getSceneString for this semantics
        if (self.scene == ''):
            pass
        return(self.scene)

    
    def getScenes(self, filtering=False):
        """Return a sorted list of scenes contained in self, if self is a Group.
        
        Boolean filtering indicates whether to return only filtered or all entries
        Return List of String
        """
        result = []
        if (self.getContext().isGroup()):
            for subEntry in self.getContext().getSubEntries(filtering):
                scene = subEntry.getOrganizer().getScene()
                if (not (scene in result)):
                    result.append(scene)
            result.sort()
        return(result)


    def getFreeScene(self):
        """Return the string representing the next free scene.
        
        Return String
        """
        def findHole(x, y):
            x = int(x)
            if (x < 0):  # found a hole already
                return(x)
            try:  # beware of new indicator
                y = int(y)
            except: 
                return(-(x + 1))
            if ((x + 1) < y):
                return(-(x + 1))
            else:
                return(y)
        scenes = self.getScenes(filtering=False)
        result = functools.reduce(findHole, scenes, 1)
        if (0 <= result):  # no hole found, append
            result = (-len(scenes))
            if (MediaClassHandler.ElementNew in scenes):
                result = (result + 1)
        return(OrganizationByName.FormatScene % (-result))


    def requiresUniqueNumbering(self):
        """As an exception, singletons do not require a number for uniqueness.
        """
        return(not self.isSingleton())


# Other API Funcions
    def findGroupFor(self, **pathInfo):
        """overwrite MediaOrganization.findGroupFor()
        """
        try:
            name = pathInfo['name']
        except: 
            raise ValueError('OrganizationByName.findGroupFor(): No name given!')
        if (name == self.getName()):
            if (self.getContext().isGroup()):
                result = self.getContext()
            else:
                result = self.getContext().getParentGroup()
        else:
            model = self.__class__.ImageFilerModel
            result = model.getEntry(name=name)
            if (result):
                if (not result.isGroup()):  # singleton exists
                    result = self.convertToGroup()
            else:  # name as yet unused
                result = Group.createAndPersist(model, name=name)
        return(result)


    def renameSingle(self, filtering=False, elements=None, removeIllegalElements=False, **pathInfo):
        """After renaming a singleton, register the old name as free and the new name as used. 
        
        overrides MediaOrganization.renameSingle
        """
        oldName = self.getName()
        result = super(OrganizationByName, self).renameSingle(filtering=filtering, elements=elements, removeIllegalElements=removeIllegalElements, **pathInfo)
        if (self.isSingleton()
            and (oldName != self.getName())):
            print('OganizationByName.renameSingle(): Registering "%s" as free' % oldName)
            self.nameHandler.registerNameAsFree(oldName)
            print('OganizationByName.renameSingle(): Registering "%s" as used' % self.getName())
            self.nameHandler.registerNameAsUsed(self.getName())
        return result


    def renameGroup(self, processIndicator=None, filtering=False, **pathInfo):
        """After renaming a named group, register the old name as free and the new name as used. 
        
        overrides MediaOrganization.renameGroup
        """
        oldName = self.getName()
        result = super(OrganizationByName, self).renameGroup(processIndicator=processIndicator, filtering=filtering, **pathInfo)
        if (self.getContext().isGroup()
            and (1 < len(self.getName()))  # named groups have names with more than one letter
            and (oldName != self.getName())):
            print('OganizationByName.renameSingle(): Registering "%s" as free' % oldName)
            self.nameHandler.registerNameAsFree(oldName)
            print('OganizationByName.renameSingle(): Registering "%s" as used' % self.getName())
            self.nameHandler.registerNameAsUsed(self.getName())
        return result


    def getRenameList(self, newParent, pathInfo, filtering=True):
        """Create a list of <entry, pathInfo> to move self's subentries to newParent.
        """
        if (not self.getContext().isGroup()):
            raise ValueError('OrganizationByName.getRenameList(): Entry "%s" is not a Group!' % self)
        # create a map from self's scenes to scenes not yet used by newParent
        if (self.getContext() == newParent):
            sceneMap  = {scene:scene for scene in self.getScenes()}
        else:
            existingScenes = newParent.getOrganizer().getScenes(filtering=False)
            try:
                existingScenes.remove(MediaClassHandler.ElementNew)
            except:
                pass
            existingSceneNumbers = [int(s) for s in existingScenes]
            sceneMap = {}
            nextFreeScene = 1
            for scene in self.getScenes():
                if (scene == MediaClassHandler.ElementNew):
                    sceneMap[MediaClassHandler.ElementNew] = MediaClassHandler.ElementNew
                else:
                    while (nextFreeScene in existingSceneNumbers):
                        nextFreeScene = (nextFreeScene + 1)
                    sceneMap[scene] = (OrganizationByName.FormatScene % nextFreeScene)
                    existingSceneNumbers.append(nextFreeScene)
        Logger.debug('OrganizationByName.getRenameList(): Scene map is "%s"' % sceneMap)
        # create list of subentries and their new pathInfo 
        result = []
        for subEntry in self.getContext().getSubEntries(filtering=filtering):
            newPathInfo = subEntry.getOrganizer().getPathInfo()
            if ('name' in pathInfo):
                newPathInfo['name'] = pathInfo['name']
            newPathInfo['scene'] = sceneMap[newPathInfo['scene']] 
            if (MediaClassHandler.ElementNew == newPathInfo['scene']):  # avoid clashing numbers on "new" scene, which is not mapped
                del newPathInfo['number']
                newPathInfo['makeUnique'] = True
            if ('classesToRemove' in pathInfo):
                newPathInfo['classesToRemove'] = pathInfo['classesToRemove'] 
            if ('removeIllegalElements' in pathInfo):
                newPathInfo['removeIllegalElements'] = pathInfo['removeIllegalElements'] 
            if ('elements' in pathInfo):
                newTags = self.getModel().getClassHandler().combineTagsWithPriority(subEntry.getTags(),
                                                                                    pathInfo['elements'])
                newPathInfo['elements'] = newTags 
            pair = (subEntry, newPathInfo)
            result.append(pair)
        return(result)

 
    def setValuesInNamePane(self, aMediaNamePane):
        """Set the fields of the MediaNamePane for self.
        """
        sceneAndNumberInactive = (not (self.getContext().isGroup()
                                       or self.isSingleton()))
        super(OrganizationByName, self).setValuesInNamePane(aMediaNamePane)
        aMediaNamePane.numberInput.Enable(sceneAndNumberInactive)
        aMediaNamePane.identifierString.SetLabel(self.getName())
        aMediaNamePane.sceneInput.SetValue(self.getScene())
        aMediaNamePane.sceneInput.Enable(sceneAndNumberInactive)


    def getValuesFromNamePane(self, aMediaNamePane):
        """
        """
        result = super(OrganizationByName, self).getValuesFromNamePane(aMediaNamePane)
        if (self.isSingleton()):
            try:
                del result['number']
            except:
                pass
            try:
                del result['makeUnique']
            except:
                pass
        scene = aMediaNamePane.sceneInput.GetValue()
        if (scene != ''): 
            if (self.isSingleton()):
                Logger.debug('Organization.getValuesFromNamePane(): Ignoring scene input for a singleton!')
            else:
                result['scene'] = scene
        return(result)



# Internal - to change without notice
    def convertToGroup(self):
        """Convert the current singleton Single to a Group with the same name.
        
        Return new Group
        """
        Logger.debug('OrganizationByName.convertToGroup(): Converting "%s" to a group' % self.getPath())
        group = Group.createAndPersist(self.__class__.getModel(), name=self.getName())
        pathInfo = self.getPathInfo()
        pathInfo['scene'] = 1
        pathInfo['number'] = 1
        self.getContext().renameTo(**pathInfo)
        return(group)


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
                    dialog.SetValue(_('"%s" is not a legal name') % newName)
                    newName = None
        dialog.Destroy()
        return(newName)


    def askNewScene(self, parentWindow):
        """User wants to relabel a scene (organized by name). Ask for new scene. 
        
        Returns String containing new name, or None if user cancelled. 
        """
        dialog = wx.TextEntryDialog(parentWindow, _('Enter New Scene'), _('Relabel Scene'), '')
        ok = True
        newSceneString = None
        while (ok 
               and (newSceneString == None)):
            ok = (dialog.ShowModal() == wx.ID_OK)
            if (ok):
                newSceneString = dialog.GetValue()
                if (newSceneString != MediaClassHandler.ElementNew):
                    try: 
                        newScene = int(newSceneString)
                    except: 
                        newScene = -1
                    if ((newScene < 0) or (99 < newScene)):
                        dialog.SetValue(_('Scene "%s" is not legal; must be between 0 and 99') % newSceneString)
                        newSceneString = None
                    else:
                        newSceneString = (OrganizationByName.FormatScene % newScene)
                    if (newSceneString in self.getContext().getParentGroup().getOrganizer().getScenes()):
                        dialog2 = wx.MessageDialog(parentWindow, 
                                                   (_('Scene "%s" already exists; move media to this scene anyway?') % newSceneString),
                                                   _('Confirmation'),
                                                   wx.YES_NO | wx.ICON_WARNING)
                        confirmed = (dialog2.ShowModal() == wx.ID_YES)
                        dialog2.Destroy()
                        if (not confirmed):
                            newSceneString = None
            else:
                newSceneString = None
        dialog.Destroy()
        return(newSceneString)


    def getNumberedEntriesMap(self):
        """overwrite MediaOrganization.getNumberedEntriesMap(), 
        to return only numbers from self's group
        """
        result = {}
        for entry in self.getContext().getParentGroup().getSubEntries(filtering=False):
            if (self.getScene() == entry.getOrganizer().getScene()):
                result[entry.getOrganizer().getNumber()] = entry
        return(result)



class FilterByName(MediaFilter):
    """A filter for media organized by name, i.e., including scene and singleton.
    """


# Class Constants
    ConditionKeyScene = 'scene'
    ConditionKeySingle = 'single'
    ConditionKeyGroupSizeLarger = 'groupSizeLarger'
    ConditionKeyGroupSizeSmaller = 'groupSizeSmaller'    
    


# Class Methods
    @classmethod
    def getConditionKeys(cls):
        """overwrite MediaFilter.getConditionKeys()"""
        keys = super(FilterByName, cls).getConditionKeys()
        keys.extend([FilterByName.ConditionKeyScene,
                     FilterByName.ConditionKeySingle,
                     FilterByName.ConditionKeyGroupSizeLarger,
                     FilterByName.ConditionKeyGroupSizeSmaller])
        return(keys)


# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        super(FilterByName, self).__init__(model)
        # internal state
        self.conditionMap[FilterByName.ConditionKeySingle] = None
        self.conditionMap[FilterByName.ConditionKeyScene] = None
        self.conditionMap[FilterByName.ConditionKeyGroupSizeLarger] = None
        self.conditionMap[FilterByName.ConditionKeyGroupSizeSmaller] = None



# Setters
# Getters
    def __repr__(self):
        """override MediaFilter.__repr__()"""
        result = super(FilterByName, self).__repr__()  # ends with ')'
        conditions = ''
        if (self.getFilterValueFor(FilterByName.ConditionKeySingle) != None):
            conditions = ('singleton %s, ' % ('required' if self.getFilterValueFor(FilterByName.ConditionKeySingle) else 'prohibited'))
        if (self.getFilterValueFor(FilterByName.ConditionKeyScene) != None):
            conditions = conditions + ('scene %s, ' % self.getFilterValueFor(FilterByName.ConditionKeyScene))
        if (self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger) != None):
            conditions = conditions + ('group size > %s, ' % self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger))
        if (self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller) != None):
            conditions = conditions + ('group size < %s, ' % self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller))
        result = (result[:-1] + conditions + ')')
        return(result)


    def filteredByConditions(self, entry):
        """override MediaFilter.filteredByConditions()"""
        singleCondition = self.getFilterValueFor(FilterByName.ConditionKeySingle)
        if ((singleCondition != None)
            and (singleCondition != entry.getOrganizer().isSingleton())):
            Logger.debug('FilterByName.filteredByConditions(): Single condition filters %s' % entry)
            return True 
        sceneCondition = self.getFilterValueFor(FilterByName.ConditionKeyScene)
        if ((sceneCondition != None)
            and ((entry.getOrganizer().isSingleton())
                 or (sceneCondition != entry.getOrganizer().getScene()))):
            Logger.debug('FilterByName.filteredByConditions(): Scene condition filters %s' % entry)
            return True
        groupSizeCondition = self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger)
        if (groupSizeCondition != None):
            if (entry.getOrganizer().isSingleton()):
                return True
            parent = entry.getParentGroup()
            if (len(parent.getSubEntries(filtering=False)) < groupSizeCondition):
                return True
        groupSizeCondition = self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller)
        if (groupSizeCondition != None):
            if (entry.getOrganizer().isSingleton()):
                return True
            parent = entry.getParentGroup()
            if (len(parent.getSubEntries(filtering=False)) > groupSizeCondition):
                return True
        return super(FilterByName, self).filteredByConditions(entry)



# Internal
    # def setConditionsAndCalculateChange(self, **kwargs):
    #     """Overwrite MediaFilter.setConditionsAndCalculateChange()"""
    #     changed = super(FilterByName, self).setConditionsAndCalculateChange(**kwargs)
    #     if ((FilterByName.ConditionKeyGroupSizeLarger in kwargs)
    #         and (kwargs[FilterByName.ConditionKeyGroupSizeLarger] != self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger))):
    #             self.setFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger, kwargs[FilterByName.ConditionKeyGroupSizeLarger], raiseChangedEvent=False)
    #             changed = True
    #     if ((FilterByName.ConditionKeyGroupSizeSmaller in kwargs)  
    #           and (kwargs[FilterByName.ConditionKeyGroupSizeSmaller] != self.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller))):
    #             self.setFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller, kwargs[FilterByName.ConditionKeyGroupSizeSmaller], raiseChangedEvent=False)
    #             changed = True
    #     return changed




class SingletonFilter(FilterConditionWithMode):  # TODO: replace by BooleanFilter
    """Represents a filter for singletons (media not in a named group).
    """
    def __init__(self, parent):
        FilterConditionWithMode.__init__(self, parent, _('Single'))


    def getConditionControls(self):
        return([self.modeChoice])


    def onChange(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        newMode = self.modeChoice.GetSelection()
        if (newMode == FilterConditionWithMode.FilterModeIndexRequire):
            newFilterValue = True
        elif (newMode == FilterConditionWithMode.FilterModeIndexExclude):
            newFilterValue = False
        else:  # FilterModeIndexIgnore 
            newFilterValue = None
        Logger.debug('SingletonFilter.onChange(): Changing mode to %s' % newFilterValue)
        self.filterModel.setConditions(single=newFilterValue)
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('SingletonFilter.updateAspect(): Processing change of filter')
            newFilterValue = self.filterModel.getFilterValueFor(FilterByName.ConditionKeySingle)
            if (newFilterValue == True):
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexRequire)
            elif (newFilterValue == False):
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexExclude)
            else:  # None
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexIgnore)
            Logger.debug('SingletonFilter.updateAspect(): Setting to %s' % newFilterValue)
        else:
            Logger.error('SingletonFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))



class SceneFilter(FilterConditionWithMode):
    """Represents a filter for scene numbers.
    """
    def __init__(self, parent):
        FilterConditionWithMode.__init__(self, parent, _('Scene'))
        self.sceneNumber = wx.lib.masked.NumCtrl(parent, 
                                                 -1,
                                                 integerWidth=2,
                                                 fractionWidth=0,
                                                 min=1,
                                                 max=99)
        self.sceneNumber.Bind(wx.lib.masked.EVT_NUM, self.onChange, self.sceneNumber)


    def getConditionControls(self):
        return([self.sceneNumber, self.modeChoice])


    def onChange(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        newSceneInt = self.sceneNumber.GetValue()
        newScene = (OrganizationByName.FormatScene % newSceneInt)
        if (newSceneInt == 0):
            newMode = FilterConditionWithMode.FilterModeIndexIgnore
            Logger.debug('SceneFilter.onChange(): Ignoring newScene filter 0')
        else:
            newMode = self.modeChoice.GetSelection()
            oldScene = self.filterModel.getFilterValueFor(FilterByName.ConditionKeyScene)
            if ((newMode == FilterConditionWithMode.FilterModeIndexIgnore)
                and (newScene != oldScene)):
                newMode = FilterConditionWithMode.FilterModeIndexRequire
        if (newMode == FilterConditionWithMode.FilterModeIndexRequire):
            self.filterModel.setConditions(scene=newScene)
            Logger.debug('SceneFilter.onChange(): Setting newScene filter to %s' % newSceneInt)
        elif (newMode == FilterConditionWithMode.FilterModeIndexExclude):
            self.filterModel.setConditions(scene=None)
            self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexIgnore)
            Logger.warn('SceneFilter.onChange(): Excluding scenes NYI, clearing newScene filter!')
        else:  # mode = ignore
            self.filterModel.setConditions(scene=None)
            Logger.debug('SceneFilter.onChange(): Clearing newScene filter')
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('SceneFilter.updateAspect(): Processing change of filter')
            filterValue = self.filterModel.getFilterValueFor(FilterByName.ConditionKeyScene)
            if (filterValue):
                self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexRequire)
                self.sceneNumber.SetValue(int(filterValue))
                Logger.debug('SceneFilter.updateAspect(): Setting to %s' % filterValue)
        else:
            Logger.error('SceneFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))



class GroupSizeFilter(FilterCondition):
    """Represents a filter on the size of groups.
    """
    FilterRelationIgnore = 'ignore'
    FilterRelationLarger = 'larger'
    FilterRelationSmaller = 'smaller'
    FilterRelations = [FilterRelationIgnore, FilterRelationLarger, FilterRelationSmaller]
    FilterRelationIndexIgnore = FilterRelations.index(FilterRelationIgnore)
    FilterRelationIndexLarger = FilterRelations.index(FilterRelationLarger)
    FilterRelationIndexSmaller = FilterRelations.index(FilterRelationSmaller)


    def __init__(self, parent):
        FilterCondition.__init__(self, parent, _('Group Size'))
        self.relationChoice = wx.Choice(parent, wx.ID_ANY, choices=GroupSizeFilter.FilterRelations)
        self.relationChoice.SetSelection(0)
        self.relationChoice.Bind(wx.EVT_CHOICE, self.onChange, self.relationChoice)
        self.size = wx.lib.masked.NumCtrl(parent, wx.ID_ANY, integerWidth=3, fractionWidth=0, min=1, max=999)
        self.size.Bind(wx.lib.masked.EVT_NUM, self.onChange, self.size)


    def getConditionControls(self):
        return([self.relationChoice, self.size])


    def onChange(self, event):  # @UnusedVariable
        wx.BeginBusyCursor()
        newRelation = self.relationChoice.GetSelection()
        newSize = self.size.GetValue()
        newSizeInt = int(newSize)
        if (newSizeInt == 0):
            newRelation = GroupSizeFilter.FilterRelationIgnore
            Logger.debug('GroupSizeFilter.onChange(): Ignoring illegal new group size "%s"' % newSize)
        if (newRelation == GroupSizeFilter.FilterRelationIndexIgnore):
            self.filterModel.setConditions(groupSizeLarger=None, groupSizeSmaller=None)
            Logger.debug('GroupSizeFilter.onChange(): Clearing group size filter')
        elif (newRelation == GroupSizeFilter.FilterRelationIndexLarger):
            self.filterModel.setConditions(groupSizeLarger=newSizeInt, groupSizeSmaller=None)
            Logger.warn('GroupSizeFilter.onChange(): Requiring groups larger than %s' % newSizeInt)
        else:  # relation == smaller
            self.filterModel.setConditions(groupSizeLarger=None, groupSizeSmaller=newSizeInt)
            Logger.debug('GroupSizeFilter.onChange(): Requiring groups smaller than %s' % newSizeInt)
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('GroupSizeFilter.updateAspect(): Processing change of filter')
            filterValue = self.filterModel.getFilterValueFor(FilterByName.ConditionKeyGroupSizeLarger)
            if (filterValue):
                self.relationChoice.SetSelection(1)
                self.size.SetValue(int(filterValue))
                Logger.debug('GroupSizeFilter.updateAspect(): Requiring groups larger than %s' % filterValue)
            else: 
                filterValue = self.filterModel.getFilterValueFor(FilterByName.ConditionKeyGroupSizeSmaller)
                if (filterValue):
                    self.relationChoice.SetSelection(2)
                    self.size.SetValue(int(filterValue))
                    Logger.debug('GroupSizeFilter.updateAspect(): Requiring groups smaller than %s' % filterValue)
                else:
                    self.relationChoice.SetSelection(0)
                    Logger.debug('GroupSizeFilter.updateAspect(): Clearing filter')
        else:
            Logger.error('GroupSizeFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))


