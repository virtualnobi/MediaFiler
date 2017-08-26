#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
from __future__ import print_function
import sys
import logging
from collections import OrderedDict
from __builtin__ import classmethod
## Contributed
## nobi
## Project
#from Single import MRUOrderedDict



# Class
class MRUOrderedDict(OrderedDict):
    """Stores dictionary items in the order the keys were last added
    """
    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)


    def getOldestItem(self):
        """Return the oldest item of self, i.e., the one added first.
        """
        return(self.items()[0])



class CachingController(object): 
    """This class keeps track of memory usage. 

    If too much memory is used, the least recently used Singles are requested to free memory. 
    """
    

# Constants
    MemoryMaximum = 1000000000
    MBFactor = (1024 * 1024)



# Class Variables
    MemoryUsed = 0
    CachedRawData = None
    CachedBitmaps = None



# Class Methods
    @classmethod
    def clear(cls):
        """Clear the cache information.
        """
        cls.MemoryUsed = 0
        cls.CachedRawData = MRUOrderedDict()
        cls.CachedBitmaps = MRUOrderedDict()

        
    @classmethod
    def allocateMemory(cls, entry, imageSize, bitmap=False):
        """Register that an Entry cached the specified bytes, and ask older entries to release memory if needed.
        
        MediaFiler.Entry entry just cached an image
        Number imageSize is the number of bytes consumed by entry
        Boolean bitmap indicates that a displayable bitmap (and not raw image data) has been cached
        """
        logging.debug('CachingController.allocateMemory(): %3dMB used in %d bitmaps and %d raw data, %3dMB free,\n caching %3dMB for %s of "%s"' 
                      % ((cls.MemoryUsed / cls.MBFactor),
                         len(cls.CachedBitmaps),
                         len(cls.CachedRawData), 
                         ((cls.MemoryMaximum - cls.MemoryUsed) / cls.MBFactor), 
                         (imageSize / cls.MBFactor), 
                         ('bitmap' if bitmap else 'raw data'), 
                         entry.getPath()))
        if (bitmap):
            cls.CachedBitmaps[entry] = imageSize
        else:
            cls.CachedRawData[entry] = imageSize    
        cls.MemoryUsed = (cls.MemoryUsed + imageSize)
        while ((cls.MemoryMaximum < cls.MemoryUsed)
               and (0 < len(cls.CachedRawData))):
            (oldEntry, oldSize) = cls.CachedRawData.getOldestItem()  # @UnusedVariable
            oldEntry.releaseRawDataCache()
        while ((cls.MemoryMaximum < cls.MemoryUsed)
               and (0 < len(cls.CachedBitmaps))):
            (oldEntry, oldSize) = cls.CachedBitmaps.getOldestItem()  # @UnusedVariable
            if (oldEntry <> entry):
                oldEntry.releaseBitmapCache()
            elif (1 == len(cls.CachedBitmaps)):  # only entry cached
                logging.error('CachingController.allocateMemory(): Not enough memory to cache "%s"' % entry.getPath())
                sys.exit()


    @classmethod
    def deallocateMemory(cls, entry, bitmap=False):
        """Register that an Entry's cache has been cleared.
        
        MediaFiler.Entry entry just cleared its cache
        Boolean bitmap indicates that a displayable bitmap (and not raw image data) has been cleared
        """
        logging.debug('CachingController.deallocateMemory(): Clearing %s of "%s"' 
                      % (('bitmap' if bitmap else 'raw data'), 
                         entry.getPath()))
        freeMemory = 0
        if (bitmap):
            if (entry in cls.CachedBitmaps):
                freeMemory = cls.CachedBitmaps[entry]
                del cls.CachedBitmaps[entry]
            else:
                logging.error('CachingControl.deallocateMemory(): Not bitmap found for "%s"!' % entry.getPath())
        else:
            if (entry in cls.CachedRawData):
                freeMemory = cls.CachedRawData[entry]
                del cls.CachedRawData[entry]
            else:
                logging.error('CachingControl.deallocateMemory(): No raw data found for "%s"!' % entry.getPath())
        cls.MemoryUsed = (cls.MemoryUsed - freeMemory)



# Lifecycle
    def __init__(self):
        """
        """
        raise NotImplementedError


# # Setters
#     def setAttribute(self, value):
#         """
#         """
#         pass
#     
#     
# 
# # Getters
#     def getAttribute(self):  # inherited from SuperClass
#         """
#         """
#         pass
#     
#     
# 
# # Event Handlers
#     def updateAspect(self, observable, aspect):
#         """
#         """
#         pass
# 
# 
# 
# # Inheritance - Superclass
# 
# 
# 
# # Other API Functions
# 
# 
# 
# # Internal - to change without notice
#     pass


# Class Initialization
CachingController.clear()



# Executable Script
if __name__ == "__main__":
    pass


