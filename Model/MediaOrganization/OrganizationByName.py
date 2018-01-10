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
import wx
## nobi
from nobi.wx.Menu import Menu
## Project
from Model import Installer
from Model.MediaNameHandler import MediaNameHandler
from Model.MediaClassHandler import MediaClassHandler
#from Model.Entry import Entry
from Model.Group import Group
import UI  # to access UI.PackagePath
from UI import GUIId
from Model.MediaOrganization import MediaOrganization



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
    def getDescription(cls):
        """Return a description of the organization. 
        """
        return(_('organized by name, %d names used, %d free')
               % (cls.nameHandler.getNumberUsedNames(),
                  cls.nameHandler.getNumberFreeNames()))


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
                scene = MediaClassHandler.ElementNew
            result = os.path.join(result, scene)
        else:  # no scene given yields a singleton
            pass
        return(result)


    @classmethod
    def constructPathFromImport(self, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):  
        """Import image at sourcePath.
        """
        pathInfo = copy.copy(targetPathInfo)
        if ('elements' in pathInfo):
            raise ('OrganizationByName.constructPathFromImport(): targetPathInfo may not contain "elements"!')
        singleton = True
        if (level == 0):  # not embedded, is a single
            # determine name of image
            pathInfo['name'] = self.deriveName(importParameters.log, sourcePath[baseLength:])
            if (not pathInfo['name']):
                importParameters.logString('Cannot determine new name for "%s", terminating import!' % sourcePath)
                return
            groupExists = os.path.isdir(self.constructPath(**pathInfo))
            singleExists = (len(glob.glob(self.constructPath(**pathInfo) + MediaOrganization.IdentifierSeparator + '*')) > 0)
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
                self.ensureDirectoryExists(importParameters.log, importParameters.getTestRun(), targetDir, None)
                pathInfo['scene'] = MediaClassHandler.ElementNew
                singleton = False
        # determine extension
        (dummy, extension) = os.path.splitext(sourcePath)  # @UnusedVariable
        pathInfo['extension'] = extension[1:].lower() 
        # determine elements
        tagSet = self.ImageFilerModel.deriveTags(importParameters,
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
        newPath = self.constructPath(elements=tagSet,
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
#         # split old path into elements
#         words = self.getNamePartsInPathName(path)
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
        if (match
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
            if (match 
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
                elif (path == ''):  # fourth try: '' is the root node
                    self.name = ''
                    rest = ''
                else:  # no match, or illegal name
                    logging.info('OrganizationByName.setIdentifiersFromPath(): Cannot extract identifiers from "%s"' % path)
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
        if ((not self.context.isGroup())
            and (not self.isSingleton())):
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
        
        Return String to display a message to the user
            or None
        """
        message = None
        if ((menuId == GUIId.ChooseName)
            or (menuId == GUIId.RandomName)):
            if (menuId == GUIId.ChooseName):
                newName = self.askNewName(parentWindow)
            else:
                newName = self.nameHandler.getFreeName()
            message = self.renameMedia(newName)
        elif (menuId == GUIId.ConvertToGroup):
            message = self.convertToGroup()
        elif (menuId == GUIId.RelabelScene):
            newScene = self.askNewScene(parentWindow)
            if (newScene):
                self.relabelToScene(newScene)
        elif ((GUIId.SelectScene <= menuId)
              and (menuId <= (GUIId.SelectScene + GUIId.MaxNumberScenes))):
            newScene = self.context.getParentGroup().getScenes()[menuId - GUIId.SelectScene]
            logging.debug('OrganizationByName.runContextMenu(): Changing scene of "%s" to %s' % (self.getPath(), newScene))
            message = self.context.renameTo(makeUnique=True, scene=newScene)
        else:
            super(OrganizationByName, self).runContextMenu(menuId, parentWindow)
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
    def convertToGroup(self):
        """Convert the current singleton Single to a Group with the same name.
        
        This is probably not needed as the rename function will handle conversion to a Group automatically.
        #TODO: remove
        """
        print('Converting "%s" to a group' % self.getPath())
        newGroup = Group.createFromName(self.model, self.getName())
        self.setParentGroup(newGroup)
        self.renameTo(scene='1', number='1')

    

    def renameMedia(self, name):
        """Rename self's context media to name specified. 
        
        String name
        Return
        """
        kwargs = {'name': name}
        if (not self.context.isGroup()):
            kwargs['elements'] = self.context.getElements()
            newEntry = self.context.model.getEntry(name=name)
            if (newEntry): 
                kwargs['makeUnique'] = True
                if (newEntry.isGroup()):  # name used by Group
                    kwargs['scene'] = MediaClassHandler.ElementNew
                else:  # name used by singleton
                    newGroup = Group.createFromName(self.context.model, name)
                    parent = self.context.model.getEntry(group=True, name=name[0:1])
                    assert (parent <> None), ('No Group for "%s" found!' % name[0:1]) 
                    newGroup.setParentGroup(parent)
                    newEntry.renameTo(name=name,
                                      scene=1,
                                      makeUnique=True)
                    kwargs['scene'] = MediaClassHandler.ElementNew
            else:  # name free, create a singleton
                kwargs['scene'] = None
        self.context.renameTo(**kwargs)
        if (self.context.isGroup
            and (self.context.getParentGroup() == None)):
            targetGroup = self.context.model.getEntry(group=True, name=name)
            assert (targetGroup <> None), ('Group "%s" not found after merging two groups!' % name)
            self.context.model.setSelectedEntry(targetGroup)
        


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


