"""Provides class and element handling functionality. 

(c) by nobisoft 2016-
"""


# Imports
## Standard
import sys
import copy
import re
import codecs
## Contributed
## nobi
## Project
from .Entry import Entry
from .Organization import MediaOrganization



class MediaClassHandler(object):
    """
    """
    

# Constants
    KeyName = u'class'  # key in class dictionary mapping to class name
    KeyMultiple = u'multiple'  # key in class dictionary mapping to Boolean indicating whether multiple elements can be selected
    KeyElements = u'elements'  # key in class dictionary mapping to list of elements
    KeyRequired = u'required'  # key in class dictionary mapping to list of required elements
    KeyProhibited = u'prohibited'  # key in class dictionary mapping to list of prohibited elements
    ElementIllegal = u'illegal'  # special element signalling that a combination of elements is not legal
    ElementNew = u'new'  # special element signalling that the entry is new, i.e., just imported
    InitialFileContent = (u'# Classname Element+  # for classes with single-choice elements\n' +
                          u'# Classname [] Element+  # for classes with multiple-choice elements\n' +
                          u'# Classname +Element1 Element2+  # for a class which applies only if Element1 has been assigned')



# Class Variables



# Class Methods
    @classmethod
    def classMethod(clas):
        """
        """
        pass



# Lifecycle
    def __init__(self, pathname):
        """Create a MediaClassHandler instance from the definitions in pathname.
        """
        # inheritance
        #ObserverPattern.Observable.__init__(self, ['startFiltering', 'stopFiltering', 'selection'])
        # internal state
        self.classes = []
        self.knownElements = []
        self.readClassesFromFile(pathname)
        return(None)



# Setters
    def setAttribute(self, value):
        """
        """
        pass
    
    

# Getters
    def getClasses(self):
        """Return a list of all classes.
        """
        return(copy.copy(self.classes))

    
    def getClassNames(self):
        """Return a list of all class names.
        """
        return([aClass[self.__class__.KeyName] for aClass in self.classes])


    def getClassByName(self, className):
        """Return a Dictionary defining the named class. 
           Return None if className does not exist.
        """
        for aClass in self.classes:
            if (aClass[self.KeyName] == className):
                return(aClass)
        return(None)


    def isMultipleClassByName(self, className):
        """Return True if multiple elements of CLASSNAME may be selected. 
           Return False if at most one element of CLASSNAME may be selected. 
           Return None if CLASSNAME does not exist.
        """
        aClass = self.getClassByName(className)
        if (aClass <> None):
            return(aClass[self.KeyMultiple])
        else: 
            return(None)

    
    def getKnownElements(self):
        """Return a list of all known elements.
        """
        return(copy.copy(self.knownElements))


    def getElementsOfClass(self, aClass):
        """Return a list of all elements in aClass. 
        """
        return(aClass[self.KeyElements])

    
    def getElementsOfClassByName(self, className):
        """Return a list of all elements in className. 
           Return None if className does not exist.
        """
        aClass = self.getClassByName(className)
        if (aClass == None):
            raise KeyError, ('No class named "%s" exists!' % className)
        else:
            return(self.getElementsOfClass(aClass))
    
    
    def getRequiredElementsOfClass(self, aClass):
        """Return a list of all elements which must apply for className to be applicable. 
           Return None if className does not exist.
        """
        return(aClass[self.KeyRequired])
    
    
    def getRequiredElementsOfClassByName(self, className):
        """Return a list of all elements which must apply for className to be applicable. 
           Return None if className does not exist.
        """
        aClass = self.getClassByName(className)
        if (aClass == None):
            return(None)
        else:
            return(self.getRequiredElementsOfClass(aClass))
    
    
    def getProhibitedElementsOfClass(self, aClass):
        """Return a list of all elements which may not apply for className to be applicable. 
           Return None if className does not exist.
        """
        return(aClass[self.KeyProhibited])

    
    def getProhibitedElementsOfClassByName(self, className):
        """Return a list of all elements which may not apply for className to be applicable. 
           Return None if className does not exist.
        """
        aClass = self.getClassByName(className)
        if (aClass == None):
            return(None)
        else:
            return(self.getProhibitedElementsOfClass(aClass))


    def isLegalElement(self, element):
        """Return True if element is a legal class element, False otherwise.
        
        String element
        """
        return(element in self.getKnownElements())    


# Element Handling
    def includeRequiredElements(self, elements):
        """Add all required elements. 
        
        Sequence elements contains elements
        
        Return a Set containing elements as well as additional elements required by them 
        """
        result = set(elements)
        for aClass in self.getClasses():
            for anElement in self.getElementsOfClass(aClass):
                if (anElement in elements):
                    for requiredElement in self.getRequiredElementsOfClass(aClass):
                        result.add(requiredElement)
                    for prohibitedElement in self.getProhibitedElementsOfClass(aClass):
                        if (prohibitedElement in elements):
                            result.add(self.ElementIllegal)
        return(result)
    

    def orderElements(self, elementSet):
        """Order the elements specified according to class definition.
        
        Returns a List of String.
        """
        result = []
        elements = copy.copy(elementSet)
        for aClass in self.getClasses():
            for element in self.getElementsOfClass(aClass):
                if (element in elements):
                    result.append(element)
                    elements.remove(element)
        for element in sorted(elements):
            result.append(element)
        return (result)


    def elementsToString(self, elementSet):
        """Return a String containing all elements in ELEMENTSET in canonical order.
        
        Elements are introduced by ELEMENTSEPARATOR (meaning the result is either empty or starts with a ELEMENTSEPARATOR).
        """
        elements = self.orderElements(elementSet)
        result = (MediaOrganization.ElementSeparator.join(elements))
        if (not (result == '')):
            result = (Entry.NameSeparator + result)
        return (result)


    def stringToElements(self, elementString):
        """Turn a string into a set of elements.
        
        String elementString contains a string of words
        Return a Set with all elements from ELEMENTSTRING   
        """
        elements = set(re.split(Entry.RESeparatorsRecognized, elementString))
        if ('' in elements):
            elements.remove('')
        #print('"%s" split into %s' % (elementString, elements))
        return(elements)


    def stringToKnownAndUnknownElements(self, elementString):
        """Distribute elements in ELEMENTSTRING to known and unknown elements.
        
        Return (KNOWN, UNKNOWN) where
            KNOWN is a dictionary mapping class names to elements
            UNKNOWN is a set containing all remaining elements from ELEMENTSTRING   
        """
        elements = self.stringToElements(elementString)
        knownElements = {}
        # sort elements into class sequence
        for aClass in self.getClasses():
            className = aClass[self.KeyName]
            for classElement in self.getElementsOfClass(aClass):
                if (classElement in elements):
                    elements.remove(classElement)
                    if (className in knownElements.keys()):  # add known element...
                        knownElements[className].append(classElement)  # ...to an existing list
                    else:
                        knownElements[className] = [classElement]  # ...as a single-entry list
        unknownElements = set(elements)
        return(knownElements, unknownElements)


# Event Handlers
# Internal - to change without notice
    def readClassesFromFile(self, pathname):
        """Set self's internal state from the class definition in the given file.

        String pathname contains the file name
        """
        self.classes = []
        self.knownElements = []
        try:
            classFile = codecs.open(pathname, encoding=sys.getfilesystemencoding())
        except: # file cannot be opened, create an empty file
#             (folder, fname) = os.path.split(pathname)
#             os.makedir(folder)
#             
            return() 
        #print ("Opened class file %s" % pathname)
        for line in classFile:
            #print ("Read line >%s<" % line)
            line = line.strip()  # trim white space
            if ((len (line) == 0) or (line[0] == '#')): # empty or comment line, ignore
                #print ("Ignored empty or comment line")
                pass
            else: # non-comment, interpret
                tokens = line.split()
                className = tokens.pop(0) 
                #print ("Interpreting definition of class %s to be %s" % (className, tokens))
                multiple = False
                required = []
                prohibited = []
                elements = []
                while (len(tokens) > 0):
                    token = tokens.pop(0)
                    if (token == '[]'):  # this is a multiple-selection class
                        multiple = True
                    elif (token[0] == '+'):
                        #print ("Adding required token %s" % token[1:])
                        required.append(token[1:])
                    elif (token[0] == '-'):
                        #print ("Adding prohibited token %s" % token[1:])
                        prohibited.append(token[1:])
                    else:
                        #print ("Adding element %s" % token)
                        elements.append(token)
                aClass = {self.KeyName:className, 
                          self.KeyRequired:required, 
                          self.KeyProhibited:prohibited,
                          self.KeyMultiple:multiple, 
                          self.KeyElements:elements}
                #print ("Found definition of %s" % aClass)
                self.classes.append(aClass) 
                self.knownElements.extend(elements)  # extend list of all known elements for filtering
        classFile.close()



# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass


