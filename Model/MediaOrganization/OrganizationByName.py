# -*- coding: latin-1 -*-
"""(c) by nobisoft 2015-
"""


# Imports
## Standard
from __builtin__ import classmethod
import copy
import re
import os.path
import glob
#import StringIO
import logging
import gettext
## Contributed 
#import wx
import wx.lib.masked
## nobi
from nobi.wx.Menu import Menu
## Project
from Model import Installer
from Model.MediaClassHandler import MediaClassHandler
from Model.MediaNameHandler import MediaNameHandler
from Model.MediaFilter import MediaFilter
from Model.MediaOrganization import MediaOrganization
from Model.Group import Group
from UI.MediaFilterPane import MediaFilterPane, FilterConditionWithMode
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




# Package Variables
Logger = logging.getLogger(__name__)



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
    def getDescription(cls):
        """Return a description of the organization. 
        """
        return(_('organized by name, %d names used, %d free')
               % (cls.nameHandler.getNumberUsedNames(),
                  cls.nameHandler.getNumberFreeNames()))


#     @classmethod
#     def getFilterPaneClass(cls):
#         """Return the class to instantiate filter pane.
#         """
#         return(FilterPaneByName)

    
    @classmethod
    def constructPathForOrganization(cls, **kwargs):
        """
        String name
        Number scene
        """
        result = None
        if (('name' in kwargs)
            and (kwargs['name'] <> None)
            and (kwargs['name'] <> '')):
#             group = self.context.model.getEntry(name=kwargs['name'], group=True)  # FIXME: how to determine the model in a class method?
#             if (group):
#                 raise NotImplementedError
#             else:
#                 letter = kwargs['name'][0]
#                 result = os.path.join(letter, kwargs['name'])
            letter = kwargs['name'][0]
            result = os.path.join(letter, kwargs['name'])
        else:
            logging.error('OrganizationByName.constructPathForOrganization(): No name given!')
            return(None)
        if (('scene' in kwargs)
            and kwargs['scene']):
            try:
                scene = (cls.FormatScene % (int(kwargs['scene'])))
            except: 
                scene = MediaClassHandler.ElementNew
            result = os.path.join(result, scene)
        else:  # no scene given yields a singleton
            pass
        return(result)


    @classmethod
    def pathInfoForImport(self, importParameters, sourcePath, level, oldName, pathInfo):
        """Return a pathInfo mapping extended according to directory name oldName.
        """
        if ((0 < level)
            and os.path.isdir(sourcePath)):
            importParameters.logString('\nCannot import embedded folder "%s"!' % sourcePath)
            result = None
        else:
            result = super(OrganizationByName, self).pathInfoForImport(importParameters, sourcePath, level, oldName, pathInfo)
            if (not 'name' in result):
                baseLength = 0  # TODO: for safety, recover length of import directory
                newName = self.deriveName(importParameters.log, sourcePath[baseLength:])
                result['name'] = newName
        return(result)

        
    @classmethod
    def constructPathFromImport(cls, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):  
        """Import image at sourcePath.
        """
        pathInfo = copy.copy(targetPathInfo)
        if ('elements' in pathInfo):
            raise ('OrganizationByName.constructPathFromImport(): targetPathInfo may not contain "elements"!')
        if (not 'name' in pathInfo):
            raise ('OrganizationByName.constructPathFromImport(): targetPathInfo must contain "name"!')
        singleton = True
        if (level == 0):  # not embedded, is a single
            groupExists = os.path.isdir(cls.constructPath(**pathInfo))
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
        else:  # embedded, is inside a group, name already contained in targetDir
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
            group = Group(cls.ImageFilerModel, path)
            groupPathPattern = os.path.join(cls.ImageFilerModel.getRootDirectory(), '[a-z]')
            match = re.match(groupPathPattern, path)
            if (match):
                parent = cls.ImageFilerModel.getRootEntry()
            else: 
                (parentPath, name) = os.path.split(path)  # @UnusedVariable
                parent = cls.getGroupFromPath(parentPath)
                if (parent == None):
                    raise ValueError, ('OrganizationByName.getGroupFromPath(): Cannnot find parent Group for "%s"' % path)
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
    def deriveName(self, log, path):
        """Derive the name under which the file at path shall be imported.
         
        StringIO log collects all messages.
        String path contains the name of the file/directory to create a new name for.
        Return String containing the legal name, or None if no names are free anymore. 
        """
        if (path.find(self.ImageFilerModel.getRootDirectory()) <> 0):
            print('OrganizationByName.deriveName(): Outside of root directory: "%s"' % path)
        else:
            path = path[len(self.ImageFilerModel.getRootDirectory()):]
        newName = None # safe start state
        # search for legal name in path
        words = self.ImageFilerModel.getWordsInPathName(path)
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


    @classmethod
    def initFilterPane(cls, aMediaFilterPane):
        """Add date filter to filter pane.
        """
        super(OrganizationByName, cls).initFilterPane(aMediaFilterPane)
        aMediaFilterPane.addCondition(SingletonFilter(aMediaFilterPane))
        aMediaFilterPane.addCondition(SceneFilter(aMediaFilterPane))
        aMediaFilterPane.addSeparator()

    

# Lifecycle
    def __init__(self, anEntry, aPath):
        """Create a OrganizationByName instance to go with anEntry.
        """
        # inheritance
        super(OrganizationByName, self).__init__(anEntry, aPath)
        # internal state
        try:
            self.__class__.nameHandler.registerNameAsUsed(self.getName())
        except: 
            if (not self.context.isGroup()):
                logging.warning('OrganizationByName(): "%s" is not a legal name in "%s"' % (self.getName(), anEntry.getPath()))
        return(None)



# Setters
    def setIdentifiersFromPath(self, path):
        """Isolate name and scene (if any) from path, and return remaining part of path.

        path String relative pathname of file, with leading model root directory and trailing extension removed
        
        TODO: make independent from OS-dependent separator characters (/ vs. \)
        TODO: allow capitalized names (while letter groups should be normalized to lower-case) 
        
        Returns a String 
        """
        self.name = ''
        self.scene = ''
        # first try: 'letter/name/scene-' is a Single inside a Group
        match = re.search(r"""([a-z])                  # single-letter directory = \1
                              \\((\1[a-z]+)[0-9]?)  # directory with name = \3 and optional digit, all captured in \2
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
                                  \\((\1[a-z]+)[0-9]?)  # directory with name = \3 and optional digit, all captured in \2
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
                    Logger.info('OrganizationByName.setIdentifiersFromPath(): Cannot extract identifiers from "%s"' % path)
                    rest = path  # neither image nor group, nothing consumed
        return(rest)


    def relabelToScene(self, newScene):
        """Relabel all media in the same scene as self.context to newScene
        
        String newScene contains the number of the new scene 
        """
        logging.debug('OrganizationByName.relabelToScene(): Moving entries from scene %s to scene %s (from "%s")' 
                      % (self.getScene(), newScene, self.context.getPath()))
        parentGroup = self.context.getParentGroup()
        for entry in parentGroup.getSubEntries():
            if (entry.organizer.getScene() == self.getScene()):
                entry.renameTo(makeUnique=True, scene=newScene)



# Getters
    def isUnknown(self):
        """Return whether self is incompletely specified.

        Return Boolean
        """
        if (self.getScene() == MediaClassHandler.ElementNew):
            return(True)
        match = re.match(r'([^\d]+)\d*', self.getName())  # isolate name in name+number identifiers
        if (match == None):
            return(True)
        else:
            if (self.nameHandler.isNameLegal(match.group(1))):  # legal name
                return(False)
            else:
                return(True)

    
    def isFilteredBy(self, aFilter):
        """Return whether self's context is filtered. 
        
        Return True if context shall be hidden, False otherwise
        """
        if ((aFilter.singleCondition <> None)
            and (aFilter.singleCondition <> self.isSingleton())):
            Logger.debug('OrganizationByName.isFilteredBy(): Single condition filters %s' % self.getContext())
            return(True)
        if ((MediaFilter.SceneConditionKey in aFilter.conditionMap)
            and aFilter.conditionMap[MediaFilter.SceneConditionKey]
            and (self.getScene() <> (OrganizationByName.FormatScene % aFilter.conditionMap[MediaFilter.SceneConditionKey]))):
            Logger.debug('OrganizationByName.isFilteredBy(): Scene condition filters %s' % self.getContext())
            return(True)
        return(False)

    
    def getNumbersInGroup(self):
        """Return the (ascending) list of Numbers in self's group.
        
        TODO: Remove this when OrganizationByName uses embedded Groups for the scene, and let the Group
        list the numbers. 
        """
        return([e.getOrganizer().getNumber() 
                for e in self.getContext().getParentGroup().getSubEntries() 
                if ((not e.isGroup())
                    and (e.getOrganizer().getScene() == self.getScene()))])


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
        if (self.context.isGroup()):
            menu.Append(GUIId.ConvertToSingle, GUIId.FunctionNames[GUIId.ConvertToSingle])
            if (1 < len(self.context.getSubEntries(filtering=False))):
                menu.Enable(GUIId.ConvertToSingle, False)
        menu.AppendSeparator()
        # functions applicable to Singles inside named Groups
        if ((not self.getContext().isGroup())
            and (not self.isSingleton())):
            menu.AppendSubMenu(self.deriveRenumberSubMenu(), GUIId.FunctionNames[GUIId.AssignNumber])
        if ((not self.context.isGroup())
            and (not self.isSingleton())):
            sceneMenu = Menu()
            sceneId = GUIId.SelectScene
            for scene in self.getContext().getParentGroup().getOrganizer().getScenes():
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
        
        Return String to display a message to the user
            or None
        """
        message = None
        if ((menuId == GUIId.ChooseName)
            or (menuId == GUIId.RandomName)):
            if (menuId == GUIId.ChooseName):
                newName = self.askNewName(parentWindow)
                if (newName):
                    self.getContext().renameTo(name=newName)
            else:
                newName = self.nameHandler.getFreeName()
                if (newName):
                    self.getContext().renameTo(name=newName)
                else:
                    message = 'No more free names!'
        elif (menuId == GUIId.ConvertToGroup):
            message = self.convertToGroup()
        elif (menuId == GUIId.RelabelScene):
            newScene = self.askNewScene(parentWindow)
            if (newScene):
                self.relabelToScene(newScene)
        elif ((GUIId.SelectScene <= menuId)
              and (menuId <= (GUIId.SelectScene + GUIId.MaxNumberScenes))):
            newScene = self.getContext().getParentGroup().getOrganizer().getScenes()[menuId - GUIId.SelectScene]
            logging.debug('OrganizationByName.runContextMenu(): Changing scene of "%s" to %s' % (self.getPath(), newScene))
            message = self.getContext().renameTo(makeUnique=True, scene=newScene)
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
              and (self.getScene() <> '')):
            return(False)
        return(True)


    def getName(self):
        return(self.name)
    
    
    def getScene(self):
        # TODO: make getScene() return None if no scene defined, add getSceneString for this semantics
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
        result = reduce(findHole, scenes, 1)
        if (0 <= result):  # no hole found, append
            result = (-len(scenes))
            if (MediaClassHandler.ElementNew in scenes):
                result = (result + 1)
        return(OrganizationByName.FormatScene % (-result))


# Other API Funcions
    def renameGroup(self, elements=set(), classesToRemove=None, removeIllegalElements=False,
                    name=None, scene=None):
        """Rename self's context (which is a Group) according to the specified changes.
        
        Return the Group to be selected after the renaming.
        """
        if (scene):
            raise ValueError, ('Passed illegal parameter for scene "%s" to OrganizationByName.renameGroup()' % scene)
        if (not name):
            raise ValueError, 'Passed no name to OrganizationByName.renameGroup()'
        model = self.__class__.ImageFilerModel
        # ensure new group exists
        newParent = model.getEntry(name=name)
        Logger.debug('OrganizationByName.renameGroup(): New parent is "%s"' % newParent)
        if (newParent):
            if (not newParent.isGroup()):  # singleton exists
                singleton = newParent
                newParent = Group.createAndPersist(model, 
                                                   self.__class__.constructPath(name=name))
                singleton.renameTo(name=name, scene='1', makeUnique=True)
        else:  # name as yet unused
            newParent = Group.createAndPersist(model, 
                                               self.__class__.constructPath(name=name))
        # move scenes of self to unused scenes of newParent
        sceneMap = {}
        existingScenes = newParent.getOrganizer().getScenes(filtering=False)
        try:
            existingScenes.remove(MediaClassHandler.ElementNew)
        except: 
            pass
        sceneNumbers = [int(s) for s in existingScenes]
        nextFreeScene = 1
        for scene in self.getScenes():
            if (scene == MediaClassHandler.ElementNew):
                sceneMap[MediaClassHandler.ElementNew] = MediaClassHandler.ElementNew
            else:
                while (nextFreeScene in sceneNumbers):
                    nextFreeScene = (nextFreeScene + 1)
                sceneMap[scene] = (OrganizationByName.FormatScene % nextFreeScene)
        Logger.debug('OrganizationByName.renameGroup(): Scene map is "%s"' % sceneMap)
        # move subentries to new group
        for subEntry in self.getContext().getSubEntries(filtering=True):
            subEntry.renameTo(elements=elements, 
                              classesToRemove=classesToRemove,
                              removeIllegalElements=removeIllegalElements,
                              name=name,
                              scene=sceneMap[subEntry.getOrganizer().getScene()])
        return(newParent)


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
        if (scene <> ''): 
            result['scene'] = scene
        return(result)



# Internal - to change without notice
    def convertToGroup(self):
        """Convert the current singleton Single to a Group with the same name.
        """
        Logger.debug('OrganizationByName.convertToGroup(): Converting "%s" to a group' % self.getPath())
        Group.createAndPersist(self.model, name=self.getName())
        self.renameTo(scene='1', number='1')


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



class SingletonFilter(FilterConditionWithMode):
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
        else:
            newFilterValue = None
        Logger.debug('SingletonFilter.onChange(): Changing mode to %s' % newFilterValue)
        self.filterModel.setConditions(single=newFilterValue)
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('SingletonFilter.updateAspect(): Processing change of filter')
            newFilterValue = self.filterModel.getSingleton()
            if (newFilterValue == True):
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexRequire)
            elif (newFilterValue == False):
                self.modeChoice.SetSelection(MediaFilterPane.FilterModeIndexExclude)
            else:
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
        scene = self.sceneNumber.GetValue()
        if (scene == 0):
            newMode = FilterConditionWithMode.FilterModeIndexIgnore
            Logger.debug('SceneFilter.onChange(): Ignoring scene filter 0')
        else:
            newMode = self.modeChoice.GetSelection()
        if (newMode == FilterConditionWithMode.FilterModeIndexRequire):
            self.filterModel.setConditions(Scene=scene)
            Logger.debug('SceneFilter.onChange(): Setting scene filter to %s' % scene)
        elif (newMode == FilterConditionWithMode.FilterModeIndexExclude):
            self.filterModel.setConditions(Scene=False)
            self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexIgnore)
            Logger.info('SceneFilter.onChange(): Excluding scenes NYI, clearing scene filter!')
        else:
            self.filterModel.setConditions(Scene=False)
            Logger.debug('SceneFilter.onChange(): Clearing scene filter')
        wx.EndBusyCursor()


    def updateAspect(self, observable, aspect):
        if (aspect == 'changed'):
            Logger.debug('SceneFilter.updateAspect(): Processing change of filter')
            filterValue = self.filterModel.getFilterValueFor(MediaFilter.SceneConditionKey)
            if (filterValue):
                self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexRequire)
                self.sceneNumber.SetValue(filterValue)
                Logger.debug('SceneFilter.updateAspect(): Setting to %s' % filterValue)
            else: 
                self.modeChoice.SetSelection(FilterConditionWithMode.FilterModeIndexIgnore)
                Logger.debug('SceneFilter.updateAspect(): Clearing filter')
        else:
            Logger.error('SceneFilter.updateAspect(): Unknown aspect "%s" of object "%s"' % (aspect, observable))

