#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
#import random
import re
#import copy
## Contributed
## nobi
## Project



class MediaNameHandler(object): 
    """Implements a storage for media (group) names. 
    """
    

# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, path):
        """Create a MediaNameHandler from the list of names in the given file. Assume all names are unused.
        
        String path names the file containing legal names
        """
        # inheritance
        super(MediaNameHandler, self).__init__()
        # internal state
        self.legalNames = self.readNamesFromFile(path)
        self.registerAllNamesAsFree()



# Setters
    def registerAllNamesAsFree(self):
        """Reset to initial state where all names are considered unused.
        """
        self.freeNames = self.legalNames.copy()

        
    def registerNameAsFree(self, name):
        """Register a name as not being used.
        """
        if (self.isNameLegal(name)):
            self.freeNames.add(name)
        else:
            raise ValueError('"%s" is not a legal name!' % name)


    def registerNameAsUsed(self, name):
        """Register a name as being used.
        """
        if (self.isNameLegal(name)):
            if (name in self.freeNames):
                self.freeNames.remove(name)
        else:
            raise ValueError('"%s" is not a legal name!' % name)  



# Getters
    def isValid(self): 
        """Return True if self contains a list of names.
        """
        if (self.legalNames 
            and (0 < len(self.legalNames))):
            return(True)
        else:
            return(False)


    def isNameLegal(self, name):
        """Return True name is a legal name, False otherwise.
        """
        if (name == None):  # illegal input 
            return (False)
        elif (name in self.legalNames):  # name is legal
            return (True)
        else:  # check whether name suffixed by digits
            return(self.trimNumberFromName(name) in self.legalNames) 


    def isNameFree(self, name):
        """Return True if name is legal and unused.
        """
        return (self.isNameLegal(name)
                and (name in self.freeNames))


    def getFreeName(self):
        """Return a free name, and remove it from the list of free names.
        
        Return String containing the free name, or None if all names are used.
        """
        try: 
            return(self.freeNames.pop()) 
        except: 
            return(None)


    def getNumberUsedNames(self):
        """Return the number of used names.
        """
        return(len(self.legalNames) - len(self.freeNames))


    def getNumberFreeNames(self):
        """Return the number of unused names.
        """
        return(len(self.freeNames))



# Event Handlers
# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
    def readNamesFromFile(self, path):
        """Read valid names from path.
        
        String path
        Return a set() of String
        """
        try:
            nameFile = open(path)
        except:  # no names file exists
            return(None)
        result = set()
        for line in nameFile:
            line = line.strip()  # trim white space
            if (0 < len(line)):  # non-empty line must be a name
                result.add(line)
        nameFile.close()
        return(result)


    def trimNumberFromName(self, name):
        """Remove a trailing number from name. 
        
        String name 
        Return String containing name without trailing number, or None
        """
        match = re.match('^([^\d]+)\d+$', name)
        if (match):  # digits exist
            nameWithoutDigits = match.group(1)
            return(nameWithoutDigits)
        else:  # no match
            return(None)



# Class Initialization
# Executable Script
if __name__ == "__main__":
    pass


