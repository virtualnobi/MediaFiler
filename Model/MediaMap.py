#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2018-
"""


# Imports
## Standard
from __future__ import print_function
import logging
import hashlib
## Contributed
## nobi
## Project
from .Entry import Entry
from .Single import Single



# Package Variables
Logger = logging.getLogger(__name__)



class MediaMap(object): 
    """Implements a mapping of media content to MediaFiler.Single objects, to detect duplicates.
    """
# Constants
    KeyLength = 512
    InputLength = 4096



# Class Variables
    Instances = {}  # mapping MediaCollections to instances of corresponding MediaMap



# Class Methods
    @classmethod
    def getMap(cls, aMediaCollection, aProgressIndicator=None):
        """Return a media map for aMediaCollection
        
        MediaFiler.MediaCollection aMediaCollection
        ProgressIndicator
        Return MediaMap
        """
        if (aMediaCollection in cls.Instances):
            return(cls.Instances[aMediaCollection])
        else:
#             instance = MediaMap(aMediaCollection, aProgressIndicator)
#             cls.Instances[aMediaCollection] = instance
#             return(instance)
            return(None)



# Lifecycle
    def __init__(self, aMediaCollection, aProgressIndicator=None):
        """Create a MediaMap containing all Single objects from aMediaCollection
        
        MediaFiler.MediaCollection
        ProgressIndicator
        """
        # inheritance
        super(MediaMap, self).__init__()
        # internal state
        self.mediaCollection = aMediaCollection
        self.mediaMapping = {}
        if (aProgressIndicator):
            aProgressIndicator.beginPhase(aMediaCollection.getCollectionSize())  # TODO: , _('Creating media map'))
        for entry in self.mediaCollection:
            if (isinstance(entry, Single)):
                if (aProgressIndicator):
                    aProgressIndicator.beginStep()
                self.addSingle(entry)
        Logger.debug('MediaMap(): %s collisions with %s items' % self.getCollisions())
        MediaMap.Instances[self.mediaCollection] = self



# Setters
    def addSingle(self, aSingle):
        """Add aSingle to self. 
        """
        key = aSingle.getKey()
        if (key in self.mediaMapping):
            if (not aSingle in self.mediaMapping[key]):
                self.mediaMapping[key].append(aSingle)
        else:
            self.mediaMapping[key] = [aSingle]



# Getters
    def contains(self, aSingle):
        """Check whether self already contains an entry identical to aSingle.
        
        Return a Single different from aSingle, but with identical content, if it exists
            or None if it does not exist
        """
        key = aSingle.getKey()
        if (key in self.mediaMapping):
            duplicate = None
            for candidate in self.mediaCollection[key]:
                if ((aSingle != candidate)
                    and (aSingle.isIdenticalContent(candidate))):
                    duplicate = candidate
                    break
            if (duplicate == None):
                Logger.info('MediaMap.contains(): Same key, but different files for %s' % aSingle)
            return(duplicate)
        else:
            return(None)


    def getDuplicates(self, aSingle):
        """Return a list of duplicates of aSingle.
        
        Return list of Single (empty if no duplicates exist)
        """
        key = aSingle.getKey()
        potentialDuplicates = self.mediaMapping[key]
        if (key in self.mediaMapping):
            return([duplicate 
                    for duplicate in potentialDuplicates 
                    if ((duplicate != aSingle) and (aSingle.isIdenticalContent(duplicate)))])
        else:
            return([])


    def getDuplicate(self, fileName):
        """Search for an Entry with identical media content as in the specified file.
        
        String fileName contains the absolute filename of the media file to check
        Return Single with identical media content, or None if none exists 
        """
        key = Single.getKeyFromFile(fileName)
        if (key in self.mediaMapping):
            candidates = self.mediaMapping[key] 
            Logger.debug('MediaMap.getDuplicate(): %s potential duplicates found for "%s"' % (len(candidates), fileName))
            subclass = Entry.getSubclassForPath(fileName)
            if (subclass):
                candidateRawImage = subclass.getRawImageFromPath(self.mediaCollection, fileName)
                for entry in candidates: 
                    try:
                        if (candidateRawImage.GetData() == entry.getRawImage().GetData()):
                            Logger.debug('MediaMap.getDuplicate(): Duplicate is "%s"' % entry)
                            return(entry)
                    except Exception as e:
                        Logger.warning('MediaMap.getDuplicate(): Failed to read "%s"' % fileName)
                        print('MediaMap.getDuplicate(): Failed to read "%s", error follows:\n%s' % (fileName, e))
                        return(None)
        return(None)
    
    
    def getCollisions(self):
        """Return the count of collisions with the count of objects involved.
        
        Return Sequence of Number (collisions, participants)
        """
        collisions = 0
        participants = 0
        for key, value in self.mediaMapping.items(): 
            if (1 < len(value)):
                collisions = (collisions + 1)
                participants = (participants + len(value) - 1)
                Logger.debug('MediaMap.getCollisions(): Collision at "%s" with \n\t%s\n\t%s' % (key, value[0], value[1]))
        return(collisions, participants)



# Event Handlers
#     def updateAspect(self, observable, aspect):
#         """
#         """
#         pass



# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
    def getKeyFromFile(self, path):
        """
        Return String
        """
#         # just use filesize
#         # use prefix of file content
#         with open(path, 'rb') as f:
#             key = f.read(MediaMap.KeyLength)
#         key = unicode(key, 'ascii', 'replace')
        # use hash of longer prefix of file content
        with open(path, 'rb') as f:
            prefix = f.read(MediaMap.InputLength)
        algorithm = hashlib.md5()
        algorithm.update(prefix)
        key = algorithm.hexdigest()
        return(key)



# Class Initialization
pass


