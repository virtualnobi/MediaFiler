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
## Contributed
## nobi
## Project
#from Single import MRUOrderedDict



# Class
class MRUOrderedDict(OrderedDict):
    """Stores dictionary items in the order the keys were last added
    
    Python 3 version
    """
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)


    def getOldestItem(self):
        """Return the oldest item of self, i.e., the one added first.
        """
        return(list(self.items())[0])


class MRUOrderedDictPy2(OrderedDict):
    """Stores dictionary items in the order the keys were last added
    
    Python 2 version
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
    """This class keeps track of which objects use how much memory. 
    If too much memory is used, the least recently used objects are requested to free memory.
    
    The cache is organized into different numeric priorities (0 being highest priority), and when
    requesting memory to be freed, objects with lower priority are requested to free up their memory
    before objects with higher priority are considered.  
    """
    

# Constants
    MemoryMaximum = 5000000000
    MBFactor = (1024 * 1024)
    Logger = logging.getLogger(__name__)


# Class Variables
    MemoryUsed = 0
    CacheList = [MRUOrderedDict()]  # List of MRUOrderedDict, index corresponds to cache priority



# Class Methods
    @classmethod
    def clear(cls):
        """Clear the cache information.
        """
        cls.Logger.debug('CachingController.clear()')
        cls.MemoryUsed = 0
        cls.CacheList = [MRUOrderedDict()]


    @classmethod
    def cacheState(cls):
        """Return a String describing the cache state.
        """
        result = ('%dMB free, %dMB used' % (((cls.MemoryMaximum - cls.MemoryUsed) / cls.MBFactor), (cls.MemoryUsed / cls.MBFactor)))
        for index in range(0, len(cls.CacheList)):
            size = sum(cls.CacheList[index].values()) / cls.MBFactor
            result = (result + ', Priority %d: %dMB in %d items' % (index, size, len(cls.CacheList[index])))
        return(result)

        
    @classmethod
    def allocateMemory(cls, entry, imageSize, bitmap=False, cachePriority=-1):
        """Register that an Entry cached the specified bytes, and ask older entries to release memory if needed.
        
        MediaFiler.Entry entry just cached an image
        Number imageSize is the number of bytes consumed by entry
        Boolean bitmap indicates that a displayable bitmap (and not raw image data) has been cached
        Number cachePriority (>= 0) indicates cache priority
        """
        cls.Logger.debug('CachingController.allocateMemory(): %s\n  caching %3dMB for %s (prio %s) of "%s"', 
                         cls.cacheState(),
                         (imageSize / cls.MBFactor), 
                         ('bitmap' if bitmap else 'raw data'),
                         cachePriority, 
                         entry.getPath())
        if (cachePriority == -1):
            if (bitmap):
                cachePriority = 0
            else:  # raw data
                cachePriority = 2
        if ((len(cls.CacheList) <= cachePriority)
            or (cls.CacheList[cachePriority] == None)):
            for index in range(len(cls.CacheList), (cachePriority + 1)):
                cls.CacheList.append(MRUOrderedDict())
        cls.MemoryUsed = (cls.MemoryUsed + imageSize)
        currentPriority = (len(cls.CacheList) - 1)
        while (cls.MemoryMaximum < cls.MemoryUsed):
            if (len(cls.CacheList[currentPriority].keys()) == 0):
                if (currentPriority == 0):
                    cls.Logger.critical('CachingController.allocateMemory(): Not enough memory to cache "%s"',
                                        entry.getPath())
                    sys.exit()
                else:
                    currentPriority = (currentPriority - 1)
            else:
                (oldEntry, oldSize) = cls.CacheList[currentPriority].getOldestItem()  
                cls.Logger.debug('CachingController.allocateMemory(): Releasing %dMB of priority %d from "%s"',
                                 (oldSize / cls.MBFactor),
                                 currentPriority,
                                 entry.getPath())
                oldEntry.releaseCacheWithPriority(currentPriority)
        cls.CacheList[cachePriority][entry] = imageSize


    @classmethod
    def deallocateMemory(cls, entry, bitmap=False, cachePriority=-1):
        """Register that an Entry's cache has been cleared.
        
        MediaFiler.Entry entry just cleared its cache
        Boolean bitmap indicates that a displayable bitmap (and not raw image data) has been cleared
        Number cachePriority (>= 0) 
        """
        cls.Logger.debug('CachingController.deallocateMemory(): %s\n  clearing %s (prio %s) of "%s"',
                         cls.cacheState(),
                         ('bitmap' if bitmap else 'raw data'), 
                         cachePriority,
                         entry)
        if (cachePriority == -1):
            if (bitmap):
                cachePriority = 0
            else:  # raw data
                cachePriority = 2
        if (len(cls.CacheList) < cachePriority):
            cls.Logger.error('CachingController.deallocateMemory(): No priority %s cache found while deallocating "%s"!',
                             cachePriority,
                             entry)
        elif (entry in cls.CacheList[cachePriority]):
            cls.MemoryUsed = (cls.MemoryUsed - cls.CacheList[cachePriority][entry])
            del cls.CacheList[cachePriority][entry]
        else:
            cls.Logger.error('CachingController.deallocateMemory(): Priority %s cache contains no entry for "%s"!',
                             cachePriority,
                             entry)



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


