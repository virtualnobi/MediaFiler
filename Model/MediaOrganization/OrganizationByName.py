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
import StringIO
import logging
import gettext
## Contributed 
import wx
## nobi
from nobi.wxExtensions.Menu import Menu
## Project
from Model import Installer
from Model.MediaNameHandler import MediaNameHandler
from Model.MediaClassHandler import MediaClassHandler
from Model.Entry import Entry
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
    def constructPathFromImport(self, importParameters, sourcePath, level, baseLength, targetDir, targetPathInfo, illegalElements):  
        """Import image at sourcePath.
        """
#        pathInfo = {'rootDir': targetDir}
        pathInfo = copy.copy(targetPathInfo)
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
                pathInfo['makeUnique'] = True
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
                pathInfo['elements'] = (pathInfo['elements'] + MediaClassHandler.TagSeparator + MediaClassHandler.ElementNew)
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
        try:
            self.__class__.nameHandler.registerNameAsUsed(self.getName())
        except: 
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
        logging.debug('OrganizationByName.relabelToScene(): Moving entries from scene %s to scene %s (from "%s")' % (self.getScene(), newScene), self.context.getPath())
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
            newScene = self.askNewScene(parentWindow)
            if (newScene):
                self.relabelToScene(newScene)
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

