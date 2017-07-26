"""MediaFiler

Model representing a set of image files, including class definitions and organization model.
    
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

(c) by nobisoft 2015-
"""


## Imports
from __future__ import print_function
# Standard
import types
#import os
import os.path
import re
import logging
#import datetime
# Contributed 
# nobi
from nobi.ObserverPattern import Observable, Observer
from nobi.SecureConfigParser import SecureConfigParser
# Project 
from . import Installer
from .MediaFilter import MediaFilter
from .Entry import Entry
from .MediaClassHandler import MediaClassHandler 
from .Organization import OrganizationByDate
from .Organization import OrganizationByName
from UI import GUIId
#from .MediaNameHandler import MediaNameHandler



class MediaCollection(Observable, Observer):
    """
    """



# Constants
    IdentifierSeparator = u'-'  # separates name components such as name, scene, year, month, day
    ConfigurationOptionParameter = '%1'
    ConfigurationOptionLastMedia = 'last-media'



# Class Methods
# Lifecycle 
    def __init__ (self, rootDir=None):
        """Create a new MediaCollection.
        
        String rootDir specifies the path to the image root directory.
        """
        logging.debug('MediaCollection.init()')
        # inheritance
        Observable.__init__(self, ['startFiltering', 'stopFiltering', 'selection'])
        # internal state
        if (rootDir):
            self.setRootDirectory(rootDir)
        logging.debug('MediaCollection.init() finished')
        return(None)


    def setRootDirectory (self, rootDir):
        """Change the root directory to process a different image set.
        """
        self.rootDirectory = os.path.normpath(rootDir)
        # clear all data
        self.selectedEntry = None
        self.initialEntry = None
#        self.names = []  # list of all legal names
#        self.freeNames = None  # list of all free names, lazily defined
        # set up the configuration persistence
        self.configuration = SecureConfigParser(Installer.getConfigurationFilePath())
        self.configuration.read(Installer.getConfigurationFilePath())
        if (not self.configuration.has_section(GUIId.AppTitle)):
            self.configuration.add_section(GUIId.AppTitle)
        # read legal names and class definitions
#        self.nameHandler = MediaNameHandler(Installer.getNamesFilePath())
        if (os.path.exists(Installer.getNamesFilePath())): 
            self.organizedByDate = False
            self.organizationStrategy = OrganizationByName
        else:
            self.organizedByDate = True
            self.organizationStrategy = OrganizationByDate
        self.organizationStrategy.setModel(self)
        self.classHandler = MediaClassHandler(Installer.getClassFilePath())
        # read groups and images
        self.root = Entry.createInstance(self, self.rootDirectory)
        self.loadSubentries(self.root)
#         if (not self.organizedByDate):
#             self.organizationStrategy.nameHandler.registerAllNamesAsFree()
        self.cacheCollectionProperties()
        # initialize filter to no restrictions
        self.filter = MediaFilter(self)
        self.filter.addObserverForAspect(self, 'changed')
        # select initial entry
        if (os.path.exists(Installer.getInitialFilePath())):
            self.initialEntry = Entry.createInstance(self, Installer.getInitialFilePath())
        path = self.getConfiguration(self.ConfigurationOptionLastMedia)
        if (path):
            entry = self.getEntry(path=path)
            if (entry):
                logging.info('MediaCollection.setRootDirectory(): selecting "%s" from last run' % entry.getPath())
                self.setSelectedEntry(entry)
            else:
                logging.info('MediaCollection.setRootDirectory(): last viewed media "%s" does not exist.' % path)
                self.setSelectedEntry(self.root)
        else: 
            logging.info('MediaCollection.setRootDirectory(): last viewed media not saved')
            self.setSelectedEntry(self.root)



# Setters
    def setSelectedEntry(self, entry):
        """Set the selected entry.
        
        If entry is the (hidden) root entry, the initial image will be selected, if it exists.
        """
        logging.debug('MediaCollection.setSelectedEntry(%s)' % (entry.getPath() if entry else entry))
        self.selectedEntry = entry
        if (self.selectedEntry):
            self.setConfiguration(self.ConfigurationOptionLastMedia, entry.getPath())
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
                and ((path == None) or (path == entry.getPath()))
                and ((year == None) or (year == entry.organizer.getYearString()))
                and ((month == None) or (month == entry.organizer.getMonthString()))
                and ((day == None) or (day == entry.organizer.getDayString()))
                and ((name == None) or (name == entry.getName()))
                and ((scene == None) or (scene == entry.getScene()))):
                return (entry)
            if (entry.isGroup()):
                # TODO: possible performance improvement
                #and ((name == None) or (name == entry.getName()))
                #and ((year == None) or (year == entry.getYear()))
                searching.extend(entry.getSubEntries(filtering))  # queue subentries of Group for searching                    
        return(None)


    def getSelectedEntry(self):
        """Return the selected entry, or None is the (hidden) root is selected.
        """
        if ((self.selectedEntry == None)
            or (self.selectedEntry == self.root)):
            return(self.root)  # self.initialEntry)
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
        return (self.cachedMinimumSize)


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


    def getEarliestDate(self):
        """Return the date of the earliest Entry in self.
        """
        return(self.cachedEarliestDate)


    def getLatestDate(self):
        """Return the date of the latest Entry in self.
        """
        return(self.cachedLatestDate)


    def getNextEntry(self, entry):
        """Get the next entry following entry. 

        Return a MediaFiler.Entry or None
        """
        if ((entry == None)
            or (entry == self.getRootEntry())
            or (entry.getPath() == self.initialEntry)
            ):
            return(self.root.getFirstEntry())
        else:
            return(entry.getNextEntry(entry))


    def getPreviousEntry(self, entry):
        """Get the previous entry preceeding entry.

        Return MediaFiler.Entry or None
        """
        if ((entry == None)
            or (entry == self.getRootEntry())
            or (entry.getPath() == self.initialEntry)
            ):
            return(self.root.getLastEntry())
        else:
            return(entry.getPreviousEntry(entry))


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
                    self.setSelectedEntry(observable.getParentGroup())
                    break
                entry = entry.getParentGroup()



# ## Name Handling
#     def readNamesFromFile (self, nameFileName):
#         """Read valid names from nameFileName and store the list in self.names.
# 
#         Set self.organizedByDate accordingly.
#         """
#         print('MediaCollection.readNamesFromFile() deprecated')
#         self.names = []
#         self.freeNames = None  # wait for use, and instantiate lazily when needed
#         try:
#             nameFile = open(nameFileName)
#         except:  # no names file exists
#             self.organizedByDate = True  # image collection organized by date, not by name
#             return()
#         self.organizedByDate = False  # image collection organized by name
#         for line in nameFile:
#             line = line.strip()  # trim white space
#             if (len (line) > 0):  # non-empty line must be a name
#                 self.names.append(line)
#         nameFile.close()
#     
# 
#     def nameIsLegal (self, name):
#         """Return True if model organized by name and name is a legal name, False otherwise.
#         """
#         print('MediaCollection.nameIsLegal() deprecated')
#         if ((name == None)  # illegal input 
#             or (self.organizedByDate)):  # names are irrelevant
#             return (False)
#         else:
#             return(self.nameHandler.isNameLegal(name))
# 
# 
#     def setFreeNames (self):
#         """Collect free names.
#         """
#         print('MediaCollection.setFreeNames() deprecated')
#         if (self.organizedByDate):
#             self.freeNames = None
#         else:
#             self.nameHandler.registerAllNamesAsFree()
#             for entry in self:
#                 self.nameHandler.registerNameAsUsed(entry.getName())
# 
#         
#     def getFreeName(self):
#         """Return a free name. Return None if images are organized by date, or if all names are used.
#            Removes the name from the list of free names.
#         """
#         print('MediaCollection.getFreeName() deprecated')
#         if (self.organizedByDate):
#             return(None)
#         else:
#             return(self.nameHandler.getFreeName())



## Filtering
    def getFilter (self):
        """Return the current MediaFilter.
        """
        return(self.filter)


    def filterEntries(self):
        """Self's filter has changed. Recalculate the filtered entries. 
        """
        print('MediaCollection.filterEntries() started')
        self.changedAspect('startFiltering')
        if (self.getFilter().isEmpty()): 
            for entry in self:
                entry.setFilter(False)
        else:  # filters exist
            print('Filtering entries')
            increment = 100
            number = 0
            entryFilter = self.getFilter()
            for entry in self: 
                entry.setFilter(entryFilter.isFiltered(entry))
                number = (number + 1)
                if ((number % increment) == 0):
                    print('  reached "%s"' % entry.getPath())
        # if selected entry is filtered, search for unfiltered parent
        if (self.getSelectedEntry().isFiltered()):
            entry = self.getSelectedEntry().getParentGroup()
            while ((entry <> self.getRootEntry())
                and entry.isFiltered()):
                entry = entry.getParentGroup()
            if (entry == None):
                logging.error('MediaCollection.filterEntries(): Root not found!')
            self.setSelectedEntry(entry)
        self.changedAspect('stopFiltering')
        print('MediaCollection.filterEntries() finished')



## Importing
    def importImages(self, importParameters):
        """Import images from a directory. 
        
        Importing.ImportParameterObject importParameters contains all import parameters
        
        Return a String containing the log.
        """
        # prepare logging
        #log = StringIO.StringIO()
        illegalElements = {}  # mapping illegal element strings to file names
        # import files
        if (self.organizedByDate):
            importParameters.logString('Importing by date from "%s" into "%s"' % (importParameters.getImportDirectory(), self.rootDirectory))
            try:
                self.importImagesRecursively(importParameters,
                                             importParameters.getImportDirectory(), 
                                             0, 
                                             len(importParameters.getImportDirectory()), 
                                             self.rootDirectory, 
                                             illegalElements)
            except StopIteration:
                pass
        else:  # organized by name
            importParameters.logString('Importing by name from "%s" into "%s"' % (importParameters.getImportDirectory(), self.rootDirectory))
            try:
                self.importImagesRecursively(importParameters, 
                                             importParameters.getImportDirectory(),
                                             0, 
                                             len(importParameters.getImportDirectory()), 
                                             self.rootDirectory, 
                                             illegalElements)
            except StopIteration:
                pass
        # log illegal elements
        if (importParameters.getReportIllegalElements()):
            for key in illegalElements:  
                count = len(illegalElements[key])
                importParameters.logString('"%s" is an illegal word found in %d entries, e.g.' % (key, count))
                #for path in illegalElements[key]:
                #    log.write('\t%s\n' % path)
                importParameters.logString('\t%s' % illegalElements[key][0])
        # reload images if needed
#         if (not importParameters.getTestRun()): 
#             self.setRootDirectory(self.rootDirectory)  
        return(importParameters.getLog())


    def importImagesRecursively(self, importParameters, sourceDir, level, baseLength, targetDir, illegalElements):
        """Import a directory with all files, recursively.

        If the number of files in the import directory exceeds the maximum number of files to import,
        as given in importParameters, StopIteration is raised. 

        Importing.ImportParameterObject importParameters contains all import parameters
        String sourceDir contains the pathname of the directory whose files shall be imported
        Number level counts the recursion level
        Number baseLength gives the length of the constant prefix in sourceDir, to be ignored for name determination
        String targetDir
        Dictionary illegalElements 
        """
        allFiles = os.listdir(sourceDir)
        allFiles.sort()  # ensure that existing numbers are respected in new numbering
        for oldName in allFiles:
            oldPath = os.path.join(sourceDir, oldName)
            if (os.path.isdir(oldPath)):  # import a directory
                if (self.organizedByDate):
                    newPath = targetDir
                else:  # organized by name
                    if (0 < level):
                        importParameters.logString('\nCannot import embedded folder "%s"!' % oldPath)
                        return
                    newName = self.organizationStrategy.deriveName(importParameters.log, oldPath[baseLength:])
                    newPath = self.organizationStrategy.constructPath(rootDir=targetDir, name=newName)  
                self.importImagesRecursively(importParameters,
                                             oldPath, 
                                             (level + 1), 
                                             baseLength, 
                                             newPath, 
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
                            self.organizationStrategy.importImage(importParameters, 
                                                                  oldPath, 
                                                                  level, 
                                                                  baseLength, 
                                                                  targetDir, 
                                                                  illegalElements)
                        else:
                            importParameters.logString('\tIgnoring small %sb file "%s"' % (fileSize, oldPath))
                    else:
                        importParameters.logString('\nMaximum number of %s files for import reached!' % importParameters.getMaxFilesToImport())
                        raise StopIteration
                else:
                    importParameters.logString('\tIgnoring unhandled file "%s"' % oldPath)


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


    def deriveElements(self, parameters, oldPath, baseLength, keepIllegals, illegalElements):
        """Create a string containing all elements of oldPath, legal ones first in class sequence, illegal ones second.
         
        Importing.ImportParameterObject parameters
        String oldPath is the absolute path of the file (needed to include into illegalElements)
        Integer baseLength is the length of the prefix of oldPath which shall not be considered.
        Boolean keepIllegals determines whether illegal elements are included in the result
        Dictionary illegalElements associates Strings of illegal elements with path names of files.
        
        Returns String containing elements. 
        """
        # split oldPath into elements
        elements = set()  # set of class elements in path
        words = self.getWordsInPathName(self.fixPathWhileImporting(parameters, oldPath[baseLength:]))  # split into components
        for word in words: 
            if self.classHandler.isLegalElement(word):  # keep legal elements
                elements.add(self.classHandler.normalizeTag(word))
            elif (re.match("^\d+$", word)):  # ignore numbers
                pass  
            elif ((not self.organizedByDate)  # TODO: Delegate to Organization.isIgnoredNamePart
                  and self.organizationStrategy.nameHandler.isNameLegal(word)):  # ignore names
                #print('ImageFilerModel.deriveElements matched a name!')
                pass
#             elif (self.organizedByDate  # TODO: Delegate to Organization.isIgnoredNamePart
#                   and re.match(self.organizationStrategy.DatePattern, word)):  # word is a date 
#                 parameters.logString('"%s" contains date %s where elements are expected\n' % (oldPath, word))
#                 pass 
            else:  # handle illegal elements
                if (keepIllegals):
                    elements.add(word)
                if (word in illegalElements):  # illegal element occurred before
                    illegalElements[word].append(oldPath) # add to list of occurrences
                else:  # first occurrence of illegal element
                    illegalElements[word] = [oldPath]  # create list of occurrences
        # add elements required by any element
        elements = self.classHandler.includeRequiredElements(elements)
        return(self.classHandler.elementsToString(elements))


    def getWordsInPathName(self, path):
        """Return all words in String path.
        """
        # TODO: align with MediaFiler.Organization.isIgnoredNamePart()
        words = []
        for word in re.split(r'[\W_/\\]+', path, flags=re.UNICODE):
            if ((word == '')  # emtpy string
                or (Entry.isLegalExtension(word))  # known file types
                or re.match(r'CAM|IMG|HPIM|DSC', word, re.IGNORECASE)):  # TODO: make known file names configurable
                pass  # these are ignored
            else:  # legal word
                words.append(word)
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
        logging.info('MediaCollection.cacheCollectionProperties()')
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
                if ((not self.cachedEarliestDate)
                    or (entryDate.getEarliestDateTime() < self.cachedEarliestDate)):
                    self.cachedEarliestDate = entryDate.getEarliestDateTime()
                if ((not self.cachedLatestDate)
                    or (self.cachedLatestDate < entryDate.getLatestDateTime())):
                    self.cachedLatestDate = entryDate.getLatestDateTime()
        logging.debug('MediaCollection.cacheCollectionProperties(): Date range from %s to %s' 
                      % (self.cachedEarliestDate, self.cachedLatestDate))
        logging.debug('MediaCollection.cacheCollectionProperties(): File size range from %s to %s' 
                      % (self.cachedMinimumSize, self.cachedMaximumSize))                
        logging.info('MediaCollection.cacheCollectionProperties() finished')
