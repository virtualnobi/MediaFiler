"""
(c) by nobisoft 2015-
"""


## Imports
# Standard
from __future__ import print_function
# import copy
import os.path
import re
import logging
import gettext
import subprocess
# Contributed 
import wx
# nobi
from nobi.os import numberOfFiles
from nobi.ObserverPattern import Observable, Observer
from nobi.SecureConfigParser import SecureConfigParser
from nobi.logging import profiledOnLogger
# Project 
from Model import GlobalConfigurationOptions
from Model import Installer
from Model.MediaClassHandler import MediaClassHandler 
from Model.Entry import Entry
from Model.Single import Single
from Model.MediaMap import MediaMap
from Model.MediaOrganization.OrganizationByDate import OrganizationByDate, FilterByDate
from Model.MediaOrganization.OrganizationByName import OrganizationByName, FilterByName
from Model.CachingController import CachingController
from UI import GUIId



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
import UI  # to access UI.PackagePath
from UI.Importing import ImportParameterObject
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
#     _ = Translation.ugettext
    _ = Translation.gettext  # Python 3 
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)



class MediaCollection(Observable, Observer):
    """Model representing a set of image files, including class definitions and organization model.
    
    The classes are specified in a text file found in relative path given by ClassFileName.
    - Lines starting with # are comments.
    - The first token is the name of the class.
    - Subsequent tokens starting with '+' are required elements, ie. this class can only apply if the required element applies.
    - Subsequent tokens starting with '-' are prohibited elements, ie. this class cannot apply if the prohibited element applies.
    - If the next token is '[]', several elements of the following set can be chosen. 
    - Otherwise, only one element of the following set can be chosen.
    - All remaining tokens list the elements in this class. 
        
    The names are listed in a text file found in relative path given by NamesFileName.
    If the names file exists, the images are organized by name: The root directory contains folders with the initial letter of the names, 
    which contain files or folders. Names of single files consist of the name and subsequent class elements. Names of folders consist only
    of the name; files contained in folders consist of a number and subsequent class elements.
    If the names file does not exist, the images are organized by date: The root directory contains folders per year, which contain folders
    per month, which contain single images or image folders. Single image names consist of the date and subsequent class elements. 
    folder names consist of the date and text.
    
    The following aspects of ImageFilerModel are observable:
    - startFiltering: Filter has changed, starting to filter Entries
    - stopFiltering: Filter has changed, and all Entries have been processed
    - selection: the selected Entry has changed
    - size: the collection size has changed (i.e., an Entry has been removed)
    """



# Constants
    ReorderTemporaryTag = 'reordering'  # to ensure uniqueness in renameList()



# Class Methods
    def runConfiguredProgram(self, option, fileName, parentWindow):
        """Run the external program configured for the given option on the given file.
        
        The option string must be valid configuration option. 
        
        
        String option specifies which configuration option to use
        String fileName specifies the file name to insert instead of the placeholder
        wx.Window parentWindow to display an error dialog if required
        Return Boolean indicating successful execution
        """
        Logger.debug('MediaCollection.runConfiguredProgram(): Looking for configuration of "%s"' % option)
        progName = self.getConfiguration(option)
        if (not progName):
            Logger.warn('MediaCollection.runConfiguredProgram(): No external program specified for option "%s"' % option)
            dlg = wx.MessageDialog(parentWindow,
                                   ('No external command specified for the\n"%s" option!' % option),
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return(False)
        Logger.debug('MediaCollection.runConfiguredProgram(): Found external command "%s"' % progName)
        if (GlobalConfigurationOptions.Parameter in progName):
            command = progName.replace(GlobalConfigurationOptions.Parameter, fileName)
        else:
            command = progName
        Logger.debug('MediaCollection.runConfiguredProgram(): Calling "%s"' % command)
        try:
            run = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            result = run.returncode
        except Exception as exc:
            result = -1
            message = ('External command "%s" failed with exception\n %s' % (command, exc))
        finally:
            if (result != 0):
                message = ('External command "%s" failed with error code %s' % (command, result))
        if (result != 0):
            Logger.warn('MediaCollection.runConfiguredProgram(): Failed with message "%s"' % message)
            dlg = wx.MessageDialog(parentWindow,
                                   message,
                                   'Error',
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return(False)
        return(True)



# Lifecycle 
    def __init__(self, rootDir, processIndicator):
        """Create a new MediaCollection.
        
        String rootDir specifies the path to the image root directory.
        nobi.ProgressIndicator progressIndicator
        """
        Logger.debug('MediaCollection.init()')
        # inheritance
        Observable.__init__(self, ['startFiltering', 'stopFiltering', 'selection', 'size'])
        # internal state
        if (rootDir):
            self.setRootDirectory(rootDir, processIndicator)
        self.iteratorState = []
        Logger.debug('MediaCollection.init() finished')

    
    @profiledOnLogger(Logger, sort='time')
    def setRootDirectory (self, rootDir, processIndicator):
        """Change the root directory to process a different image set.
        
        String rootDir
        PhasedProgressBar progressIndicator
        """
        processIndicator.beginPhase(3)
        self.rootDirectory = os.path.normpath(rootDir)
        # clear all data
        self.selectedEntry = None
        self.initialEntry = None
        CachingController.clear()
        # set up the configuration persistence
        #TODO: Must move to app to be available while mediacollection is created
        self.configuration = SecureConfigParser(Installer.getConfigurationFilePath())
        self.configuration.read(Installer.getConfigurationFilePath())
        if (not self.configuration.has_section(GUIId.AppTitle)):
            self.configuration.add_section(GUIId.AppTitle)
        #
        if (os.path.exists(Installer.getNamesFilePath())): 
            self.organizedByDate = False
            self.organizationStrategy = OrganizationByName
            filterClass = FilterByName
        else:
            self.organizedByDate = True
            self.organizationStrategy = OrganizationByDate
            filterClass = FilterByDate  
        self.organizationStrategy.setModel(self)
        processIndicator.beginStep(_('Reading tag definitions'))
        self.classHandler = MediaClassHandler(Installer.getClassFilePath())
        if (self.classHandler.isLegalElement(MediaCollection.ReorderTemporaryTag)):
            index = 1
            tag = ('%s%d' % (MediaCollection.ReorderTemporaryTag, index))
            while (self.classHandler.isLegalElement(tag)):
                index = (index + 1)
                tag = ('%s%d' % (tag, index))
            MediaCollection.ReorderTemporaryTag = tag
            Logger.warning('MediaCollection.setRootDirectory(): Temporary reordering tag changed to "%s"' % tag)
        # read groups and images
        self.root = Entry.createInstance(self, self.rootDirectory)
        self.loadSubentries(self.root, processIndicator)  # implicit progressIndicator.beginStep()
        processIndicator.beginStep(_('Calculating collection properties'))
        self.cacheCollectionProperties()
        self.filter = filterClass(self) 
        self.filter.addObserverForAspect(self, 'filterChanged')
        self.filteredEntries = self.getCollectionSize()
        # select initial entry
        if (os.path.exists(Installer.getInitialFilePath())):
            self.initialEntry = Entry.createInstance(self, Installer.getInitialFilePath())
        path = self.getConfiguration(GlobalConfigurationOptions.LastMedia)
        if (path):
            if (not os.path.isabs(path)):  # TODO: unconditional when relative path is stored for last media
                path = os.path.join(Installer.getMediaPath(), path)
            entry = self.getEntry(path=path)
            if (entry):
                Logger.info('MediaCollection.setRootDirectory(): selecting "%s" from last run.' % path)
                if (entry.isGroup() 
                    and (100 < len(entry.getSubEntries()))):
                    entry = entry.getSubEntries()[0]
                    Logger.info('MediaColleection.setRootDirectory(): Reselected "%s" because initial group contained more than 100 entries.' % entry)
                self.setSelectedEntry(entry)
            else:
                Logger.info('MediaCollection.setRootDirectory(): last viewed media "%s" does not exist.' % path)
                self.setSelectedEntry(self.root)
        else: 
            Logger.info('MediaCollection.setRootDirectory(): last viewed media not saved')
            self.setSelectedEntry(self.root)



# Setters
    def setSelectedEntry(self, entry):
        """Set the selected entry.
        """
        Logger.debug('MediaCollection.setSelectedEntry(%s)' % entry)
        previousSelection = self.selectedEntry
        self.selectedEntry = entry
        if (self.selectedEntry):  # store selected entry for next program run
            path = entry.getPath()
            path = path[len(Installer.getMediaPath()) + 1:]  # remove "/" as well
            self.setConfiguration(GlobalConfigurationOptions.LastMedia, path)
        if (previousSelection != self.selectedEntry):
            self.changedAspect('selection')


    def loadSubentries (self, entry=None, progressIndicator=None):
        """Load, store, and return the children of entry, recursively walking the entire image set. 

        MediaFiler.Entry entry the entry to load subentries for 
        PhasedProgressBar progressIndicator or None if recursive call
        Return list of subentries (empty if entry is a MediaFiler.Image)
        """
        result = []
        if (entry == None):  # retrieve root entries
            parentDir = self.rootDirectory
        else:  # retrieve entries contained in entry
            if (not entry.isGroup()):  # a single image has no subentries
                return([])
            parentDir = entry.getPath()
        fileList = os.listdir(parentDir)
        if (progressIndicator):
            progressIndicator.beginPhase(len(fileList))
        # read files in directory
        for fileName in fileList:
            if (progressIndicator):
                progressIndicator.beginStep(_('Reading media from %s') % fileName)
            fileName = os.path.join(parentDir, fileName)
            subEntry = Entry.createInstance(self, fileName)
            if (subEntry):
                result.append(subEntry)
                subEntry.setParentGroup(entry)
                subEntry.addObserverForAspect(self, 'remove')
                if subEntry.isGroup():
                    self.loadSubentries(subEntry)
        return(result)


    def setConfiguration(self, option, value):
        """Set the configuration option to value.
        
        String option
        String value

        #TODO: Must move to app to be available while mediacollection is created
        """
        if (not self.configuration.has_section(GUIId.AppTitle)):
            self.configuration.add_section(GUIId.AppTitle)
        self.configuration.set(GUIId.AppTitle, option, value)



# Getters
    def getRootDirectory(self):
        return(self.rootDirectory)


    def getClassHandler(self):
        return(self.classHandler)


    def getRootEntry(self):
        """Return the root element. This is a Group containing all other Entries.
        """
        if (self.root == None):
            raise AssertionError('MediaCollection.getRootEntry(): Root node is None')
        return(self.root)


    def getInitialEntry(self):
        """Return the "initial" entry, which may be used to display an entry before all entries are loaded, 
        or if none is selected.
        """
        return(self.initialEntry)


    def getEntry(self, filtering=False, group=None, path=None, **kwargs):
        """Return the (first) Entry (Single or Group) which fits the given criteria, or None if none exists.
        
        Boolean filtering determines whether the search is restricted to filtered Entries (True) or all Entries (False)
        Boolean group limits the search to only Groups (True) or Singles (False) or both (None)
        String path contains the pathname of the Entry to retrieve
        Dictionary kwargs contains organization-specific conditions
            year, month, day
            name, scene

        Returns an Entry, or None
        """
        # searching = self.getRootEntry().getSubEntries(filtering)
        searching = [self.getRootEntry()]
        while (len(searching) > 0):
            entry = searching.pop()
            if (((group == None) or (group == entry.isGroup()))
                and ((path == None) or (path == entry.getPath()))
                and entry.getOrganizer().matches(**kwargs)):
                return (entry)
            if (entry.isGroup()):
                # TODO: possible performance improvement
                #and ((name == None) or (name == entry.getName()))
                #and ((year == None) or (year == entry.getYear()))
                searching.extend(entry.getSubEntries(filtering))  # queue subentries of Group for searching                    
        return(None)


    def getSelectedEntry(self):
        """Return the selected entry.
        
        If no entry is selected, returns the root Group.
        
        Return Model.Entry
        """
        if (self.selectedEntry == None):
            return(self.root)
        else:
            return(self.selectedEntry)


    def getMinimumResolution(self, progressIndicator=None):
        """Return the smallest image resolution.

        If minimum resolution is not cached, assume maximum resolution is unknown as well. 
        Calculate both in this case. 
        
        ProgressIndicator progressIndicator displays progress to the user
        Return Number
        """
        if (self.cachedMinimumResolution == None):
            self.getMaximumResolution(progressIndicator)
        return(self.cachedMinimumResolution)


    def getMaximumResolution(self, progressIndicator=None):
        """Return the biggest image resolution.
        
        ProgressIndicator progressIndicator displays progress to the user
        Return Number 
        """
        if (self.cachedMaximumResolution == None):
            for entry in self:  # get resolution of some entry
                self.cachedMinimumResolution = entry.getResolution()
                self.cachedMaximumResolution = self.cachedMinimumResolution
                break
            counter = 0
            print('MediaCollection.getMaximumResolution(): Finding max resolution')
            if (progressIndicator):
                progressIndicator.beginPhase(self.getCollectionSize(), _('Calculating media resolutions'))
            for entry in self:
                if (progressIndicator):
                    progressIndicator.beginStep()
                counter = (counter + 1)
                if ((counter % 100) == 0):
                    print('  Reading resolution of %sth entry "%s"' % (counter, entry))
                resolution = entry.getResolution()
                if (resolution < self.cachedMinimumResolution):  # smaller one found
                    self.cachedMinimumResolution = resolution
                if (self.cachedMaximumResolution < resolution):  # bigger one found
                    self.cachedMaximumResolution = resolution
        return (self.cachedMaximumResolution)


    def getCollectionSize(self):
        """Return the number of media in self's collection.
        """
        return(self.cachedCollectionSize)


    def getEarliestDate(self):  # TODO: move to OrganizationByDate
        """Return the date of the earliest Entry in self.
        """
        return(self.cachedEarliestDate)


    def getLatestDate(self):  # TODO: move to OrganizationByDate
        """Return the date of the latest Entry in self.
        """
        return(self.cachedLatestDate)


    def getNextEntry(self, entry):
        """Get the next entry following entry. 

        Return a MediaFiler.Entry or None
        """
        print('MediaCollection.getNextEntry() deprecated!')
        if ((entry == None)
            or (entry == self.getRootEntry())
            or (entry == self.initialEntry)):
            return(self.root.getFirstEntry())
        else:
            return(entry.getNextEntry())


    def getPreviousEntry(self, entry):
        """Get the previous entry preceeding entry.

        Return MediaFiler.Entry or None
        """
        print('MediaCollection.getPreviousEntry() deprecated!')
        if ((entry == None)
            or (entry == self.getRootEntry())
            or (entry == self.initialEntry)):
            return(self.root.getLastEntry())
        else:
            return(entry.getPreviousEntry())


    def getConfiguration(self, option):
        """Retrieve the value for configuration option.
        
        String option
        Returns String containing value or None if not existing
        #TODO: Must move to app to be available while mediacollection is created
        """
        if (self.configuration.has_section(GUIId.AppTitle)
            and self.configuration.has_option(GUIId.AppTitle, option)):
            return(self.configuration.get(GUIId.AppTitle, option))
        else: 
            return(None)


    def getDescription(self):
        """Return a description of the model, including organization, number of images, etc.
        
        Return String
        """
        result = ('%s: %d %s%s, %s' % (self.rootDirectory,
                                     self.getCollectionSize(),
                                     _('media'),
                                     ((' (%s filtered)' % self.getFilteredEntriesCount()) if (self.getFilter().isActive()) else ''), 
                                     self.organizationStrategy.getDescription()))
        return(result)


    def getTagOccurrences(self):
        """Count occurrences of tags and return a mapping of tags to numbers. 
        
        Return dict mapping String to Number
        """
        counting = dict()
        for entry in self: 
            for tag in entry.getTags():
                if (tag in counting):
                    counting[tag] = (counting[tag] + 1)
                else:  # tag not yet seen
                    counting[tag] = 1
        tags = list(counting)
        tags.sort()
        result = dict()
        for tag in tags:
            result[tag] = counting[tag]
        return(result)



# Inheritance - Observer
    def updateAspect(self, observable, aspect):
        """observable changed its aspect. 
        """
        Observer.updateAspect(self, observable, aspect)
        if (observable == self.filter):  # filter changed
            self.filterEntries(wx.GetApp())
        elif (aspect == 'remove'):  # entry removed
            if (isinstance(observable, Single)):
                self.cachedCollectionSize = (self.cachedCollectionSize - 1)
            else:  # observable is a Group
                self.cachedCollectionSize = (self.cachedCollectionSize - observable.getGroupSize())
            # invalidate cached properties if affected
            if (observable.getFileSize() == self.cachedMinimumSize):
                self.cachedMinimumSize = None
            if (observable.getFileSize() == self.cachedMaximumSize):
                self.cachedMaximumSize = None
            if (observable.getResolution() == self.cachedMinimumResolution):
                self.cachedMinimumResolution = None
            if (observable.getResolution() == self.cachedMaximumResolution):
                self.cachedMaximumResolution = None
            # ensure selected entry is not subitem of removed entry
            entry = self.selectedEntry
            while (entry != None):
                if (entry == observable):
                    if ('True' == self.getConfiguration(GlobalConfigurationOptions.ShowParentAfterRemove)):
                        self.setSelectedEntry(observable.getParentGroup())
                    else:
                        self.setSelectedEntry(observable.getPreviousEntry(filtering=True))
                    break
                entry = entry.getParentGroup()
            self.changedAspect('size')



# Other API Functions
    def renameList(self, renameList, progressBar=None):
        """Rename many media files at once.
        
        The parameter is a list of triples which contain
        - the Single to rename (to access rename and update functions)
        - the current pathname of the Single (to verify no other changes have been done)
        - the new pathname of the Single
        
        List of (Single, String, String) renameList 
        PhasedProgressBar progressBar
        Return Boolean indicating success 
        """
        if (progressBar): 
            progressBar.beginPhase(len(renameList) + 1)
        conflicts = []
        for (entry, oldPath, newPath) in renameList:
            if (progressBar):
                progressBar.beginStep()
            if ((entry.getPath() != oldPath) 
                or (not os.path.exists(oldPath))):
                Logger.warning('MediaCollection.renameList(): Entry "%s" was expected to be named "%s"!' % (entry.getPath(), oldPath))
                return(False)
            if (oldPath == newPath):
                Logger.warning('MediaCollection.renameList(): Identical rename "%s" ignored!' % oldPath)
            elif os.path.exists(newPath):
                tmpElements = set((MediaCollection.ReorderTemporaryTag, )).union(entry.getTags())
                pathInfo = entry.getOrganizer().getPathInfo()
                pathInfo['elements'] = tmpElements
                tmpPath = entry.getOrganizer().__class__.constructPath(**pathInfo)
                if (not entry.renameToFilename(tmpPath)):
                    return(False)
                conflicts.append((entry, newPath))
            else:
                if (not entry.renameToFilename(newPath)):
                    return(False)
        if (progressBar):
            progressBar.beginStep()
        for (entry, newPath) in conflicts:
            if (not entry.renameToFilename(newPath)):
                return(False)
        return(True)


    @profiledOnLogger(Logger)
    def findDuplicates(self, aProgressIndicator=None):
        """Search duplicates, merge file names, and remove one. 
        
        aProgressIndicator shall understand beginStep()
        Return Sequence of Number (collisions, participants) where
            collisions gives the number of groups of identical Singles
            participants gives the total of Singles involved in collisions
        """
        if (aProgressIndicator):
            aProgressIndicator.beginPhase(2, _('Finding duplicates'))        
        mmap = MediaMap(self, aProgressIndicator)
        if (aProgressIndicator):
            aProgressIndicator.beginPhase(self.getCollectionSize(), _('Linking duplicates'))
        for entry in self:
            if (isinstance(entry, Single)):
                if (aProgressIndicator):
                    aProgressIndicator.beginStep()
                duplicates = mmap.getDuplicates(entry)
                entry.setDuplicates(duplicates)
                if (0 < len(duplicates)):
                    Logger.debug('MediaCollection.findDuplicates(): %s duplicates found for "%s"' % (len(duplicates), entry.getPath()))
        return(mmap.getCollisions())


    def replaceTagBy(self, oldTag, newTag, aProgressIndicator=None):
        """In all media, replace a tag by another.
        
        String oldTag
        String newTag
        ProgressIndicator aProgressIndicator
        Returns String describing how many tags have been replaced
        """
        tagsReplaced = 0
        if (aProgressIndicator):
            aProgressIndicator.beginPhase(self.getCollectionSize(), _('Replacing tag "%s" by "%s"' % (oldTag, newTag)))
        for entry in self:
            if (aProgressIndicator):
                aProgressIndicator.beginStep()
            tags = entry.getTags()
            if (oldTag in tags):
                newTags = tags.difference(set([oldTag])).union(set([newTag]))
                Logger.debug('Entry.replaceTagBy: New tags "%s" for "%s"' % (newTags, entry))
                entry.renameTo(elements=newTags)
        return(_('%s occurrences replaced') % tagsReplaced)



## Filtering
    def getFilter (self):
        """Return the current MediaFilter.
        """
        return(self.filter)


    def getFilteredEntriesCount(self):
        """Return the count of visible Entries after filtering.
        Return Number
        """
        return(self.filteredEntries)


    def filterEntries(self, progressIndicator=None):
        """Self's filter has changed. Recalculate the filtered entries. 
        """
        Logger.debug('MediaCollection.filterEntries() started')
        self.changedAspect('startFiltering')
        progressIndicator.beginPhase(self.getCollectionSize(), 'Filtering media')
        if (self.getFilter().isFiltering()): 
            self.filteredEntries = 0 
            entryFilter = self.getFilter()
            for entry in self: 
                if (entry.isGroup()):  # Group is filtered after all its children are
                    entry.setFilter(len(entry.getSubEntries(filtering=True)) == 0)
                else:
                    progressIndicator.beginStep()
                    entry.setFilter(entryFilter.filtersEntry(entry))
                    if (entry.isFiltered()):
                        self.filteredEntries = (self.filteredEntries + 1)
        else:  # filter not active or empty
            for entry in self:
                progressIndicator.beginStep()
                entry.setFilter(False)
            self.filteredEntries = self.getCollectionSize()
        # if selected entry is filtered, search for unfiltered parent
        if (self.getSelectedEntry().isFiltered()):
            entry = self.getSelectedEntry().getParentGroup()
            while ((entry != self.getRootEntry())
                and entry.isFiltered()):
                entry = entry.getParentGroup()
            if (entry == None):
                Logger.error('MediaCollection.filterEntries(): Root not found!')
            self.setSelectedEntry(entry)
        self.changedAspect('stopFiltering')
        Logger.debug('MediaCollection.filterEntries() finished')



## Importing
    def importImages(self, importParameters):
        """Import images from a directory. 
        
        Importing.ImportParameterObject importParameters contains all import parameters

        Return a String containing the log.
        """
        if (0 == len(os.listdir(importParameters.getImportDirectory()))):  # shortcut to be quick
            importParameters.logString(_('Import directory "%s" is empty' % importParameters.getImportDirectory()))
            return(importParameters.getLog())
        if (importParameters.getCheckForDuplicates()):
            importParameters.setMediaMap(MediaMap.getMap(self, importParameters.getProcessIndicator()))
            if (importParameters.getMediaMap() == None):
                importParameters.setCheckForDuplicates(False)
                importParameters.logString('No media map created; will not check for duplicates.')
            else:
                importParameters.logString('Media map exists; will check for duplicates.')
        #TODO: determine number of files recursively, print here, and use for progress bar
        importParameters.setNumberOfFilesToImport(numberOfFiles(importParameters.getImportDirectory()))
        importParameters.logString('Importing %s files by %s from "%s" into "%s"\n' 
                                   % (importParameters.getNumberOfFilesToImport(),
                                      ('date' if (self.organizationStrategy == OrganizationByDate) else 'name'),
                                      importParameters.getImportDirectory(), 
                                      self.rootDirectory))
        try:
            self.importImagesRecursively(importParameters,
                                         importParameters.getImportDirectory(), 
                                         0, 
                                         len(importParameters.getImportDirectory()), 
                                         self.rootDirectory, 
                                         {'rootDir': self.rootDirectory})
        except StopIteration:
            pass
        except Exception as e:
            raise
            importParameters.logString('Import was interrupted due to this error:\n%s' % e)
        if (importParameters.getReportIllegalElements()):
            for key in importParameters.getIllegalElements():  
                count = len(importParameters.getIllegalElements()[key])
                importParameters.logString('"%s" is an illegal word found in %d entries, e.g.' % (key, count))
                importParameters.logString('\t%s' % importParameters.getIllegalElements()[key][0])
        return(importParameters.getLog())


    def importImagesRecursively(self, importParameters, sourceDir, level, baseLength, targetDir, targetPathInfo):
        """Import a directory with all files, recursively.

        If the number of files in the import directory exceeds the maximum number of files to import,
        as given in importParameters, StopIteration is raised. 

        Importing.ImportParameterObject importParameters contains all import parameters
        String sourceDir contains the pathname of the directory whose files shall be imported
        Number level counts the recursion level
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir  # TODO: remove
        Dictionary targetPathInfo describes the target path
            rootDir
            <organization-specific> 
        """
        removeProcessedFiles = ((not importParameters.getTestRun())
                                and (importParameters.getDeleteOriginals()))
        allFiles = os.listdir(sourceDir)
        allFiles.sort()  # ensure that existing numbers are respected in new numbering
        if (level == 0):
            if (importParameters.getTestRun()):
                statusText = _('Testing import from %s')
            else:  
                statusText = _('Importing from %s')
            importParameters.getProcessIndicator().beginPhase(importParameters.getNumberOfFilesToImport(), (statusText % importParameters.getImportDirectory()))
        for oldName in allFiles:
            importParameters.getProcessIndicator().beginStep()
            sourcePath = os.path.join(sourceDir, oldName)
            newTargetPathInfo = self.organizationStrategy.pathInfoForImport(importParameters,
                                                                            sourcePath,
                                                                            level,
                                                                            oldName,
                                                                            targetPathInfo)
            if (os.path.isdir(sourcePath)):  # import a directory
                self.importImagesRecursively(importParameters,
                                             sourcePath, 
                                             (level + 1), 
                                             baseLength, 
                                             targetDir,   # newPath, 
                                             newTargetPathInfo)
                if (removeProcessedFiles
                    and (len(os.listdir(sourcePath)) == 0)):
                    try: 
                        os.rmdir(sourcePath)
                    except Exception as e:
                        Logger.error('MediaCollection.importImagesRecursively(): Cannot remove "%s"' % sourcePath)
            else:  # import a media file
                (dummy, extension) = os.path.splitext(sourcePath)
                if (Entry.isLegalExtension(extension[1:]) 
                    or (not importParameters.getIgnoreUnhandledTypes())):
                    fileSize = os.stat(sourcePath).st_size
                    if (importParameters.getMinimumFileSize() < fileSize):
                        if (importParameters.canImportOneMoreFile()):
                            duplicate = None
                            if (importParameters.getCheckForDuplicates()):
                                duplicate = importParameters.getMediaMap().getDuplicate(sourcePath)
                            if (duplicate == None):
                                self.organizationStrategy.importMedia(importParameters, 
                                                                      sourcePath, 
                                                                      level, 
                                                                      baseLength, 
                                                                      targetDir,
                                                                      newTargetPathInfo,
                                                                      importParameters.getIllegalElements())
                                importParameters.setNumberOfImportedFiles(importParameters.getNumberOfImportedFiles() + 1)
                                if (removeProcessedFiles):
                                    try:
                                        os.remove(sourcePath)
                                    except Exception as e:
                                        importParameters.logString('Error: Can''t remove "%s":\n%s' % (sourcePath, e))
                            else:
                                importParameters.logString('Duplicate of "%s"\n  found in "%s"' % (sourcePath, duplicate))
                                if (removeProcessedFiles):
                                    try:
                                        os.remove(sourcePath)
                                    except Exception as e:
                                        importParameters.logString('Error: Can''t remove "%s":\n%s' % (sourcePath, e))
                        else:
                            importParameters.logString('Maximum number of %s files for import reached!' % importParameters.getMaxFilesToImport())
                            raise StopIteration
                    else:
                        if (removeProcessedFiles):
                            try:
                                os.remove(sourcePath)
                            except Exception as e: 
                                importParameters.logString('Error: Can''t remove (small) file "%s"\n%s' % (sourcePath, e))
                else:
                    if (removeProcessedFiles):
                        try:
                            os.remove(sourcePath)
                        except Exception as e:
                            importParameters.logString('Error: Can''t remove (unhandled) file "%s"\n%s' % (sourcePath, e))


    def fixPathWhileImporting(self, parameters, oldPath):
        """
        Importing.ImportParameterObject parameters
        String oldPath contains the actual file path
        
        Return String contains the corrected path
        """
        match = re.search('Nr[. ]*(\d+)(?!\d)', oldPath)
        if (match):
            newPath = (oldPath[:match.start()] + 'No' + str(int(match.group(1))) + oldPath[match.end():])
            parameters.logString('Fixed "%s"\n    to "%s"' % (oldPath, newPath))
            oldPath = newPath
        return(oldPath)


    def deriveTags(self, parameters, oldPath, baseLength, illegalTags):
        """Create a set containing all tags of oldPath, including ones required by tag definition.
        
        Importing.ImportParameterObject parameters
        String oldPath is the absolute path of the file (needed to include into illegalElements)
        Integer baseLength is the length of the prefix of oldPath which shall not be considered.
        Dictionary illegalTags associates unknown tag Strings with path names of files where they occur
        Return Set of String containing known tags
        """
        # reduce to relevant part of pathname 
        fixedPath = self.fixPathWhileImporting(parameters, oldPath[baseLength:])
        elements = set()
        words = self.getWordsInPathName(fixedPath)
        for word in words: 
            if self.classHandler.isLegalElement(word):
                elements.add(self.classHandler.normalizeTag(word))
            else:  # unknown 
                if (parameters.getKeepUnknownTags()):
                    elements.add(word)
                if (word in illegalTags):  # illegal element occurred before
                    illegalTags[word].append(oldPath) # add to list of occurrences
                else:  # first occurrence of illegal element
                    illegalTags[word] = [oldPath]  # create list of occurrences
        # add required tags
        elements = self.classHandler.includeRequiredElements(elements)
        return(elements)


    def getWordsInPathName(self, path):  # TODO: use for tag and name derivation
        """Return all words in String path which might be legal organization identifiers or tags.
        
        Ignore numbers, known file types, and known camera identifiers.
        
        Return Set of String
        """
        words = set()
        RegexCameraIdentifiers = re.compile('CAM|IMG|HPIM|DSC')  # TODO: make configurable
#         for word in re.split(r'[\W_/\\]+', path, flags=re.UNICODE):
        for word in re.split(r'[\W_/\\]+', path):
            if ((word == '')
                or (Entry.isLegalExtension(word))
                or re.match(r'^\d+$', word)  
                or RegexCameraIdentifiers.match(word)): 
                pass  # these are ignored
            else:  # legal word
                words.add(word)
        return(words)



# section: Iteration
    def __iter__(self):
        """Return an iterator object, returning MediaFiler.Entry objects in self in post-order.
         
        Note this returns self, suitably initialized. This means only one iteration can run on self at any time.
        """
        self.iteratorState = [(None, 0, False)]  # push a triple (entry, index, childrenVisited) representing start position
        return(self)
        
        
    def next(self):
        """Return next MediaFiler.Entry from self. 
        
        Return an Entry, or raise StopIteration if last entry was already returned
        """
        if (len(self.iteratorState) == 0):  # stack of positions already exhausted
            raise StopIteration
        while (len(self.iteratorState) > 0):  # while there are positions on the stack
            (entry, index, childrenVisited) = self.iteratorState.pop(0)
            if (entry == None): # index is pointing into root collection
                entryList = self.root.getSubEntries(False)
            else:  # index is pointing into entry's subEntries
                entryList = entry.getSubEntries(False) # get all subentries, unfiltered
            if (index >= len(entryList)):  # at end of entryList
                pass  # must pop another position
            elif (entryList[index].isGroup()):  # next element is a group
                if childrenVisited:  # children were visited, return this group
                    self.iteratorState.insert(0, (entry, (index + 1), False))  # push position after this group
                    return(entryList[index])  # return this group
                else:  # children have not been visited, descend to them 
                    self.iteratorState.insert(0, (entry, index, True))  # push position at this group, indicating children have been visited
                    self.iteratorState.insert(0, (entryList[index], 0, False))  # push position at beginning of group's subentries
            else:  # entryList[index] is an image, not a group
                self.iteratorState.insert(0, (entry, (index + 1), False))  # push position after this image
                return(entryList[index])  # return this image
        raise StopIteration  # stack of positions is exhausted, no more entries


    def __next__(self):  # Python 3
        return(self.next())



#  Internal
    def cacheCollectionProperties(self):
        """Calculate and cache properties of the entire collection, to avoid repeated iterations.
        """
        Logger.info('MediaCollection.cacheCollectionProperties()')
        self.cachedCollectionSize = 0
        self.cachedMinimumSize = None
        self.cachedMaximumSize = None
        self.cachedMinimumResolution = None
        self.cachedMaximumResolution = None
        self.cachedEarliestDate = None
        self.cachedLatestDate = None
        for entry in self:
            self.cachedCollectionSize = (self.cachedCollectionSize + 1)
# TODO: way to time-consuming (reads all images which have no width/height metadata)
#             resolution = entry.getResolution() 
#             if ((resolution < self.cachedMinimumResolution)
#                 or (self.cachedMinimumResolution == 0)):
#                 self.cachedMinimumResolution = resolution
#             if (self.cachedMaximumResolution < resolution):
#                 self.cachedMaximumResolution = resolution
            if (self.organizedByDate):  # TODO: move to MediaOrganization
                entryDate = entry.getOrganizer().dateTaken
                if (entryDate):
                    if ((not self.cachedEarliestDate)
                        or (entryDate.getEarliestDateTime() < self.cachedEarliestDate)):
                        self.cachedEarliestDate = entryDate.getEarliestDateTime()
                    if ((not self.cachedLatestDate)
                        or (self.cachedLatestDate < entryDate.getLatestDateTime())):
                        self.cachedLatestDate = entryDate.getLatestDateTime()
        Logger.debug('MediaCollection.cacheCollectionProperties(): Date ranges from %s to %s' 
                      % (self.cachedEarliestDate, self.cachedLatestDate))
        Logger.debug('MediaCollection.cacheCollectionProperties(): File size ranges from %s to %s' 
                      % (self.cachedMinimumSize, self.cachedMaximumSize))                
        Logger.debug('MediaCollection.cacheCollectionProperties(): Image resolution ranges from %s to %s' 
                      % (self.cachedMinimumResolution, self.cachedMaximumResolution))                
        Logger.info('MediaCollection.cacheCollectionProperties() finished')



