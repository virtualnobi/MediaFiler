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
# Class Methods
# Lifecycle
    def __init__(self, aMediaCollection):
        """Create a MediaMap containing all Single objects from aMediaCollection
        """
        # inheritance
        super(MediaMap, self).__init__()
        # internal state
        self.mediaCollection = aMediaCollection
        self.mediaMapping = {}
        for entry in self.mediaCollection: 
            if (isinstance(entry, Single)):
                self.addSingle(entry)
        Logger.debug('MediaMap(): %s collisions with %s participants' % self.getCollisions())



# Setters
    def addSingle(self, aSingle):
        """
        """
        key = self.getKeyFromFile(aSingle.getPath())
        if (key in self.mediaMapping):
            self.mediaMapping[key].append(aSingle)
        else:
            self.mediaMapping[key] = [aSingle]



# Getters
    def getDuplicate(self, fileName, fileSize):
        """Search for an Entry with identical media content as in the specified file.
        
        String fileName contains the absolute filename of the media file to check
        Number fileSize contains the filesize of the media file to check
        Return Single with identical media content, or None if none exists 
        """
        key = self.getKeyFromFile(fileName)
        if (key in self.mediaMapping):
            candidates = self.mediaMapping[key] 
            Logger.debug('MediaMap.getDuplicate(): %s potential duplicates found for "%s"' % (len(candidates), fileName))
            subclass = Entry.getSubclassForPath(fileName)
            if (subclass):
                candidateRawImage = subclass.getRawImageFromPath(self.mediaCollection, fileName)
                for entry in candidates: 
                    if (candidateRawImage.GetData() == entry.getRawImage().GetData()):
                        Logger.debug('MediaMap.getDuplicate(): Duplicate is "%s"' % entry)
                        return(entry)
        return(None)
    
    
    def getCollisions(self):
        """Return the count of collisions with the count of objects involved.
        
        Return Sequence (collisions, participants)
        """
        collisions = 0
        participants = 0
        for key, value in self.mediaMapping.items(): 
            if (1 < len(value)):
                collisions = (collisions + 1)
                participants = (participants + len(value))
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


