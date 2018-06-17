"""
(c) by nobisoft 2015-
"""


## Imports
from __future__ import print_function
# Standard
import types
import copy
import os.path
import re
import logging
import gettext
import cProfile, pstats, StringIO
# Contributed 
# nobi
from nobi.ObserverPattern import Observable, Observer
from nobi.SecureConfigParser import SecureConfigParser
# Project 
import GlobalConfigurationOptions
from Model import Installer
from Model.MediaClassHandler import MediaClassHandler 
from Model.MediaFilter import MediaFilter
from Model.Entry import Entry
from Model.MediaOrganization.OrganizationByDate import OrganizationByDate
from Model.MediaOrganization.OrganizationByName import OrganizationByName
from Model.CachingController import CachingController
from UI import GUIId



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
import UI  # to access UI.PackagePath
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
    Logger = logging.getLogger(__name__)
    ReorderTemporaryTag = 'reordering'  # to ensure uniqueness in renameList()



# Class Methods
# Lifecycle 
    def __init__ (self, rootDir=None):
        """Create a new MediaCollection.
        
        String rootDir specifies the path to the image root directory.
        """
        MediaCollection.Logger.debug('MediaCollection.init()')
        # inheritance
        Observable.__init__(self, ['startFiltering', 'stopFiltering', 'selection', 'size'])
        # internal state
        if (rootDir):
#            self.setRootDirectoryProfiled(rootDir)
            self.setRootDirectory(rootDir)
        MediaCollection.Logger.debug('MediaCollection.init() finished')
        return(None)


    def setRootDirectory (self, rootDir):
        """Change the root directory to process a different image set.
        """
        self.rootDirectory = os.path.normpath(rootDir)
        # clear all data
        self.selectedEntry = None
        self.initialEntry = None
        CachingController.clear()
        # set up the configuration persistence
        self.configuration = SecureConfigParser(Installer.getConfigurationFilePath())
        self.configuration.read(Installer.getConfigurationFilePath())
        if (not self.configuration.has_section(GUIId.AppTitle)):
            self.configuration.add_section(GUIId.AppTitle)
        #
        if (os.path.exists(Installer.getNamesFilePath())): 
            self.organizedByDate = False
            self.organizationStrategy = OrganizationByName
        else:
            self.organizedByDate = True
            self.organizationStrategy = OrganizationByDate
        self.organizationStrategy.setModel(self)
        self.classHandler = MediaClassHandler(Installer.getClassFilePath())
        if (self.classHandler.isLegalElement(MediaCollection.ReorderTemporaryTag)):
            index = 1
            tag = ('%s%d' % (MediaCollection.ReorderTemporaryTag, index))
            while (self.classHandler.isLegalElement(tag)):
                index = (index + 1)
                tag = ('%s%d' % (tag, index))
            MediaCollection.ReorderTemporaryTag = tag
            MediaCollection.Logger.warning('MediaCollection.setRootDirectory(): Temporary reordering tag changed to "%s"' % tag)
        # read groups and images
        self.root = Entry.createInstance(self, self.rootDirectory)
        self.loadSubentries(self.root)
        self.cacheCollectionProperties()
        self.filter = MediaFilter(self)
        self.filter.addObserverForAspect(self, 'changed')
        # select initial entry
        if (os.path.exists(Installer.getInitialFilePath())):
            self.initialEntry = Entry.createInstance(self, Installer.getInitialFilePath())
        path = self.getConfiguration(GlobalConfigurationOptions.LastMedia)
        if (path):
            entry = self.getEntry(path=path)
            if (entry):
                MediaCollection.Logger.info('MediaCollection.setRootDirectory(): selecting "%s" from last run' % entry.getPath())
                self.setSelectedEntry(entry)
            else:
                MediaCollection.Logger.info('MediaCollection.setRootDirectory(): last viewed media "%s" does not exist.' % path)
                self.setSelectedEntry(self.root)
        else: 
            MediaCollection.Logger.info('MediaCollection.setRootDirectory(): last viewed media not saved')
            self.setSelectedEntry(self.root)


    def setRootDirectoryProfiled(self, rootDir):
        profiler = cProfile.Profile()
        profiler.enable()
        self.setRootDirectory(rootDir)
        profiler.disable()
        resultStream = StringIO.StringIO()
        ps = pstats.Stats(profiler, stream=resultStream)  # .ps.strip_dirs()  # remove module paths
        #ps.sort_stats('cumulative')  # sort according to time per function call, including called functions
        ps.sort_stats('time')  # sort according to time per function call, excluding called functions
        ps.print_stats(20)  # print top 20 
        print('Profiling Results for MediaCollection.setRootDirectory()')
        print(resultStream.getvalue())
        print('---')




# Setters
    def setSelectedEntry(self, entry):
        """Set the selected entry.
        """
        MediaCollection.Logger.debug('MediaCollection.setSelectedEntry(%s)' % entry)
        self.selectedEntry = entry
        if (self.selectedEntry):
            self.setConfiguration(GlobalConfigurationOptions.LastMedia, entry.getPath())
        self.changedAspect('selection')


    def loadSubentries (self, entry):
        """Load, store, and return the children of entry, recursively walking the entire image set. 

        MediaFiler.Entry entry the entry to load subentries for 
        Return list of subentries (empty if entry is a MediaFiler.Image)
        """
        #print('loadSubentries(%s)' % entry)
        result = []
        # determine which directory to read
        if (entry == None):  # retrieve root entries
            parentDir = self.rootDirectory
        else:  # retrieve entries contained in entry
            if (not entry.isGroup()):  # a single image has no subentries
                return([])
            parentDir = entry.getPath()
        # read files in directory
        for fileName in os.listdir(parentDir):
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
            print('ImageFilerModel.getRootEntry(): No root defined')
        return(self.root)


    def getInitialEntry(self):
        """Return the "initial" entry, which may be used to display an entry before all entries are loaded, 
        or if none is selected.
        """
        return(self.initialEntry)


    def getEntry(self, 
                 filtering=False, group=None,
                 path=None,
                 year=None, month=None, day=None,  
                 name=None, scene=None):
        """Return the (first) Entry (Single or Group) which fits the given criteria, or None if none exists.
        
        Boolean filtering determines whether the search is restricted to filtered Groups (True) or all Groups (False)
        Boolean group limits the search to only Groups (True) or Singles (False) or both (None)
        String path contains the pathname of the Entry to retrieve
        String year
        String month
        String day
        String name
        String scene
        
        Returns an Entry, or None
        """
        searching = self.getRootEntry().getSubEntries(filtering)
        while (len(searching) > 0):
            entry = searching.pop()
            if (((group == None) or (group == entry.isGroup()))
                and ((path == None) or (path == entry.getPath()))  # TODO: move to MediaOrganization
                and ((year == None) or (year == entry.getOrganizer().getYearString()))
                and ((month == None) or (month == entry.getOrganizer().getMonthString()))
                and ((day == None) or (day == entry.getOrganizer().getDayString()))
                and ((name == None) or (name == entry.getOrganizer().getName()))
                and ((scene == None) or (scene == entry.getOrganizer().getScene()))):
                return (entry)
            if (entry.isGroup()):
                # TODO: possible performance improvement
                #and ((name == None) or (name == entry.getName()))
                #and ((year == None) or (year == entry.getYear()))
                searching.extend(entry.getSubEntries(filtering))  # queue subentries of Group for searching                    
        return(None)


    def getSelectedEntry(self):
        """Return the selected entry.
        
        Will return a special initial entry in case the root entry or no entry is selected.
        
        Return Model.Entry
        """
        if ((self.selectedEntry == None)
            or (self.selectedEntry == self.root)):
            return(self.getInitialEntry())
        else:
            return(self.selectedEntry)


    def getMinimumSize(self):
        """Return the smallest image size in bytes.
        """
        if (self.cachedMinimumSize == 0):
            for entry in self:
                fsize = entry.getFileSize()
                if ((fsize < self.cachedMinimumSize)  # smaller one found
                    or (self.cachedMinimumSize == 0)):  # no image found so far
                    self.cachedMinimumSize = fsize
        return(self.cachedMinimumSize)


    def getMaximumSize(self):
        """Return the biggest image size in bytes.
        """
        if (self.cachedMaximumSize == 0):
            for entry in self:
                fsize = entry.getFileSize()
                if (self.cachedMaximumSize < fsize):  # bigger one found
                    self.cachedMaximumSize = fsize
        return (self.cachedMaximumSize)


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
        """
        if (self.configuration.has_section(GUIId.AppTitle)
            and self.configuration.has_option(GUIId.AppTitle, option)):
            return(unicode(self.configuration.get(GUIId.AppTitle, option)))
        else: 
            return(None)


    def getDescription(self):
        """Return a description of the model, including organization, number of images, etc.
        
        Return String
        """
        result = ('%s: %d %s, %s' % (self.rootDirectory,
                                     self.getCollectionSize(),
                                     _('media'), 
                                     self.organizationStrategy.getDescription()))
        return(result)



# Inheritance - Observer
    def updateAspect(self, observable, aspect):
        """observable changed its aspect. 
        """
        Observer.updateAspect(self, observable, aspect)
        if (observable == self.filter):  # filter changed
            self.filterEntries()
        elif (aspect == 'remove'):  # entry removed
            self.cachedCollectionSize = (self.cachedCollectionSize - 1)
            # invalidate cached properties if affected
            if (observable.getFileSize() == self.cachedMinimumSize):
                self.cachedMinimumSize = 0
            if (observable.getFileSize() == self.cachedMaximumSize):
                self.cachedMaximumSize = 0
            # ensure selected entry is not subitem of removed entry
            entry = self.selectedEntry
            while (entry <> None):
                if (entry == observable):
                    if ('True' == self.getConfiguration(GlobalConfigurationOptions.ShowParentAfterRemove)):
                        self.setSelectedEntry(observable.getParentGroup())
                    else:
                        self.setSelectedEntry(observable.getPreviousEntry(filtering=True))
                    break
                entry = entry.getParentGroup()
            self.changedAspect('size')



# Other API Functions
    def renameList(self, renameList):
        """Rename many media files at once.
        
        The parameter is a list of triples which contain
        - the Single to rename (to access rename and update functions)
        - the current pathname of the Single (to verify no other changes have been done)
        - the new pathname of the Single
        
        List of (Single, String, String) renameList 
        Return Boolean indicating success 
        """
        conflicts = []
        for (entry, oldPath, newPath) in renameList:
            if ((entry.getPath() <> oldPath) 
                or (not os.path.exists(oldPath))):
                MediaCollection.Logger.warning('MediaCollection.renameList(): Entry "%s" was expected to be named "%s"!' % (entry.getPath(), oldPath))
                return(False)
            if (oldPath == newPath):
                MediaCollection.Logger.warning('MediaCollection.renameList(): Identical rename "%s" ignored!' % oldPath)
            elif os.path.exists(newPath):
                tmpElements = set((MediaCollection.ReorderTemporaryTag, )).union(entry.getElements())
                tmpPath = entry.organizer.constructPathForSelf(elements=tmpElements)
                if (not entry.renameToFilename(tmpPath)):
                    return(False)
                conflicts.append((entry, newPath))
            else:
                if (not entry.renameToFilename(newPath)):
                    return(False)
        for (entry, newPath) in conflicts:
            if (not entry.renameToFilename(newPath)):
                return(False)
        return(True)



## Filtering
    def getFilter (self):
        """Return the current MediaFilter.
        """
        return(self.filter)


    def filterEntries(self):
        """Self's filter has changed. Recalculate the filtered entries. 
        """
        MediaCollection.Logger.debug('MediaCollection.filterEntries() started')
        self.changedAspect('startFiltering')
        if (self.getFilter().isEmpty()): 
            for entry in self:
                entry.setFilter(False)
        else:  # filters exist
            increment = 100
            number = 0
            entryFilter = self.getFilter()
            for entry in self: 
                entry.setFilter(entryFilter.isFiltered(entry))
                number = (number + 1)
                if ((number % increment) == 0):
                    MediaCollection.Logger.debug('MediaCollection.filterEntries() reached "%s"' % entry.getPath())
        # if selected entry is filtered, search for unfiltered parent
        if (self.getSelectedEntry().isFiltered()):
            entry = self.getSelectedEntry().getParentGroup()
            while ((entry <> self.getRootEntry())
                and entry.isFiltered()):
                entry = entry.getParentGroup()
            if (entry == None):
                MediaCollection.Logger.error('MediaCollection.filterEntries(): Root not found!')
            self.setSelectedEntry(entry)
        self.changedAspect('stopFiltering')
        MediaCollection.Logger.debug('MediaCollection.filterEntries() finished')



## Importing
    def importImages(self, importParameters):
        """Import images from a directory. 
        
        Importing.ImportParameterObject importParameters contains all import parameters
        
        Return a String containing the log.
        """
        illegalElements = {}  # mapping illegal element strings to file names
        importParameters.logString('Importing by %s from "%s" into "%s"\n' 
                                   % (('date' if (self.organizationStrategy == OrganizationByDate) else 'name'),
                                      importParameters.getImportDirectory(), 
                                      self.rootDirectory))
        try:
            self.importImagesRecursively(importParameters,
                                         importParameters.getImportDirectory(), 
                                         0, 
                                         len(importParameters.getImportDirectory()), 
                                         self.rootDirectory, 
                                         {'rootDir': self.rootDirectory},
                                         illegalElements)
        except StopIteration:
            pass
        if (importParameters.getReportIllegalElements()):
            for key in illegalElements:  
                count = len(illegalElements[key])
                importParameters.logString('"%s" is an illegal word found in %d entries, e.g.' % (key, count))
                importParameters.logString('\t%s' % illegalElements[key][0])
        return(importParameters.getLog())


    def importImagesRecursively(self, importParameters, sourceDir, level, baseLength, targetDir, targetPathInfo, illegalElements):
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
        Dictionary illegalElements 
        """
        allFiles = os.listdir(sourceDir)
        allFiles.sort()  # ensure that existing numbers are respected in new numbering
        for oldName in allFiles:
            oldPath = os.path.join(sourceDir, oldName)
            newTargetPathInfo = copy.copy(targetPathInfo)
            if (os.path.isdir(oldPath)):  # import a directory
                if (self.organizedByDate):  # TODO: delegate to MediaOrganization
                    if ((not 'rootDir' in newTargetPathInfo) or
                        (targetDir <> newTargetPathInfo['rootDir'])):
                        raise ValueError, 'Target path incorrect!'
                    newPath = targetDir
                    if (not 'rootDir' in newTargetPathInfo):
                        newTargetPathInfo['rootDir'] = targetDir
                else:  # organized by name
                    if (0 < level):
                        importParameters.logString('\nCannot import embedded folder "%s"!' % oldPath)
                        return
                    if ((not 'rootDir' in newTargetPathInfo) or
                        (targetDir <> newTargetPathInfo['rootDir'])):
                        raise ValueError, 'Target path incorrect!'
                    if (not 'rootDir' in newTargetPathInfo):
                        newTargetPathInfo['rootDir'] = targetDir
                    newName = self.organizationStrategy.deriveName(importParameters.log, oldPath[baseLength:])
                    newPath = self.organizationStrategy.constructPath(rootDir=targetDir, name=newName)  
                    newTargetPathInfo['name'] = newName
                    newTargetPathInfo['rootDir'] = newPath
                self.importImagesRecursively(importParameters,
                                             oldPath, 
                                             (level + 1), 
                                             baseLength, 
                                             newPath, 
                                             newTargetPathInfo,
                                             illegalElements)
                if ((not importParameters.getTestRun())
                    and (importParameters.getDeleteOriginals())
                    and (len(os.listdir(oldPath)) == 0)):
                    importParameters.logString('Removing empty directory "%s"\n' % oldPath)
                    os.rmdir(oldPath)
            else:  # import a media file
                (dummy, extension) = os.path.splitext(oldPath)
                if (Entry.isLegalExtension(extension[1:]) 
                    or (not importParameters.getIgnoreUnhandledTypes())):
                    if (importParameters.canImportOneMoreFile()):
                        fileSize = os.stat(oldPath).st_size
                        if (importParameters.getMinimumFileSize() < fileSize):
                            if ((not 'rootDir' in newTargetPathInfo) or
                                (targetDir <> newTargetPathInfo['rootDir'])):
                                raise ValueError, 'Target path incorrect!'
                            self.organizationStrategy.importMedia(importParameters, 
                                                                  oldPath, 
                                                                  level, 
                                                                  baseLength, 
                                                                  targetDir,
                                                                  newTargetPathInfo,
                                                                  illegalElements)
                        else:
                            importParameters.logString('Ignoring small %sb file "%s"\n' % (fileSize, oldPath))
                    else:
                        importParameters.logString('Maximum number of %s files for import reached!\n' % importParameters.getMaxFilesToImport())
                        raise StopIteration
                else:
                    importParameters.logString('Ignoring unhandled file "%s"\n' % oldPath)


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
        Return Set of String
        """
        # reduce to relevant part of pathname
        fixedPath = self.fixPathWhileImporting(parameters, oldPath[baseLength:])  # TODO: do once at beginning of import
        # find possible tags
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
        for word in re.split(r'[\W_/\\]+', path, flags=re.UNICODE):
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
        #print("photoFilerModel.__iter__")
        self.iteratorState = [(None, 0, False)]  # push a triple (entry, index, childrenVisited) representing start position
        return(self)
        
        
    def next(self):
        """Return next MediaFiler.Entry from self. 
        
        Return an Entry, or raise StopIteration if last entry was already returned
        """
        #print ("photoFilerModel next")
        if ((not isinstance (self.iteratorState, types.ListType))  # not yet initialized
            or (len(self.iteratorState) == 0)):  # stack of positions already exhausted
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
    
                
#  Internal
    def cacheCollectionProperties(self):
        """Calculate and cache properties of the entire collection, to avoid repeated iterations.
        """
        MediaCollection.Logger.info('MediaCollection.cacheCollectionProperties()')
        self.cachedCollectionSize = 0
        self.cachedMinimumSize = 0
        self.cachedMaximumSize = 0
        self.cachedEarliestDate = None
        self.cachedLatestDate = None
        for entry in self:
            self.cachedCollectionSize = (self.cachedCollectionSize + 1)
            fsize = entry.getFileSize()
            if ((fsize < self.cachedMinimumSize)  # smaller one found
                or (self.cachedMinimumSize == 0)):  # no image found so far
                self.cachedMinimumSize = fsize
            if (self.cachedMaximumSize < fsize):  # bigger one found
                self.cachedMaximumSize = fsize
            if (self.organizedByDate):
                entryDate = entry.organizer.dateTaken
                if (entryDate):
                    if ((not self.cachedEarliestDate)
                        or (entryDate.getEarliestDateTime() < self.cachedEarliestDate)):
                        self.cachedEarliestDate = entryDate.getEarliestDateTime()
                    if ((not self.cachedLatestDate)
                        or (self.cachedLatestDate < entryDate.getLatestDateTime())):
                        self.cachedLatestDate = entryDate.getLatestDateTime()
        MediaCollection.Logger.debug('MediaCollection.cacheCollectionProperties(): Date range from %s to %s' 
                      % (self.cachedEarliestDate, self.cachedLatestDate))
        MediaCollection.Logger.debug('MediaCollection.cacheCollectionProperties(): File size range from %s to %s' 
                      % (self.cachedMinimumSize, self.cachedMaximumSize))                
        MediaCollection.Logger.info('MediaCollection.cacheCollectionProperties() finished')



