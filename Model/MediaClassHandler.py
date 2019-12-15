"""Provides class and element handling functionality. 

(c) by nobisoft 2016-
"""


# Imports
## Standard
import sys
import copy
import re
import codecs
import logging
## Contributed
## nobi
## Project
#from .MediaOrganization import MediaOrganization


# Package Variables
Logger = logging.getLogger(__name__)



class MediaClassHandler(object):
    """
    """
    

# Constants
    KeyName = u'class'  # key in class dictionary mapping to class name
    KeyMultiple = u'multiple'  # key in class dictionary mapping to Boolean indicating whether multiple elements can be selected
    KeyElements = u'elements'  # key in class dictionary mapping to list of elements
    KeyRequired = u'required'  # key in class dictionary mapping to list of required elements
    KeyRequiredClasses = u'requiredClass'  # key in class dictionary mapping to list of required classes
    KeyProhibited = u'prohibited'  # key in class dictionary mapping to list of prohibited elements
    TagSeparator = u'.'  # character to introduce a tag/element
    RETagSeparatorsRecognized = ('[, _' + TagSeparator + '-]')
    ElementIllegal = u'illegal'  # special element signalling that a combination of elements is not legal
    ElementNew = u'new'  # special element signalling that the entry is new, i.e., just imported
    InitialFileContent = (u'# Classname Element+  # for classes with single-choice elements\n' +
                          u'# Classname [] Element+  # for classes with multiple-choice elements\n' +
                          u'# Classname +Element1 Element2+  # for a class which applies only if Element1 has been assigned')



# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, pathname):
        """Create a MediaClassHandler instance from the definitions in pathname.
        """
        # inheritance
        # internal state
        self.classes = []
        self.knownElements = []
        self.readClassesFromFile(pathname)
        return(None)



# Setters
# Getters
    def getClasses(self):
        """Return a list of all classes.
        """
        return(copy.copy(self.classes))

    
    def getClassNames(self):
        """Return a list of all class names.
        """
        return([aClass[self.__class__.KeyName] for aClass in self.classes])


    def isMultipleClass(self, aClass):
        """Return True if multiple elements of CLASSNAME may be selected. 
           Return False if at most one element of CLASSNAME may be selected. 
        """
        return((aClass <> None) 
               and (self.KeyMultiple in aClass)
               and (aClass[self.KeyMultiple]))

    
    def isMultipleClassByName(self, className):
        """Return True if multiple elements of CLASSNAME may be selected. 
           Return False if at most one element of CLASSNAME may be selected. 
        """
        return(self.isMultipleClass(self.getClassByName(className)))


    def getElementsOfClass(self, aClass):
        """
        dict aClass
        
        Return list of all tags in aClass, ordered as in definition. 
        """
        return(list(aClass[self.KeyElements]))

    
    def getElementsOfClassByName(self, className):
        """
        String className 

        Raises KeyError if no class exists with name className 
        
        Return list of all tags in className, ordered as in definition.
        """
        aClass = self.getClassByName(className)
        if (aClass == None):
            raise KeyError, ('No class named "%s" exists!' % className)
        else:
            return(self.getElementsOfClass(aClass))
    
    
    def getKnownElements(self):
        """Return a list of all known elements.
        """
        return(copy.copy(self.knownElements))


    def isLegalElement(self, element):
        """Return True if element is a legal class element, False otherwise.
        
        String element
        Return Boolean
        """
        return(self.normalizeTag(element) in self.getKnownElements())    

    

# Other API
    def normalizeTag(self, tag):
        """Normalize a tag (element), for example, when importing.
        
        This will compare the tag with all known tags in a case-insensitive way, 
        and return the defined spelling if found in the known tags.
        If not found in the known tags, it will be returned without changes.

        String tag
        Return Boolean
        """
        for knownTag in self.getKnownElements():
            if (knownTag.lower() == tag.lower()):
                return(knownTag)
        return(tag)


    def combineTagsWithPriority(self, tagSet, priorityTagSet):
        """Return the union of the two tag sets, except for single-selection tag classes where the second set has priority.
        
        Set of String tagSet
        Set of String priorityTagSet
        Return Set of String
        """
        result = set(tagSet)
        singleSelectionClasses = filter(lambda c: (not self.isMultipleClass(c)), self.getClasses())
        for priorityTag in priorityTagSet:
            priorityClass = self.getClassOfTag(priorityTag)
            if (priorityClass in singleSelectionClasses):
                result.difference_update(set(self.getElementsOfClass(priorityClass)))
            result.add(priorityTag)
        return(result)


    def getTagsOnChange(self, tagSet, addedTag, removedTags):
        """Determine new set of tags based on tags added and removed.
        
        Set of String tagSet
        String or None addedTag
        Set of String removedTags
        
        Return Set of String containing the tags after addition and removal
        """
        Logger.debug('MediaClassHandler.getTagsOnChange(%s +%s -%s)' % (tagSet, addedTag, removedTags))
        result = copy.copy(tagSet)
        if (addedTag):
            result.update(set([addedTag]))
            result = self.includeRequiredElements(result)
            Logger.debug('MediaClassHandler.getTagsOnChange(): Adding %s yields %s' % (addedTag, result.difference(tagSet)))
        for tag in removedTags:
            result.discard(tag)
            for aClass in self.getClasses():
                if (tag in self.getRequiredElementsOfClass(aClass)):
                    result.difference_update(set(self.getElementsOfClass(aClass)))
                if (((addedTag == None) or
                     (self.getClassOfTag(tag) != self.getClassOfTag(addedTag))) 
                    and (self.getClassOfTag(tag)[MediaClassHandler.KeyName] in self.getRequiredClassesOfClass(aClass))):
                    result.difference_update(set(self.getElementsOfClass(aClass)))
        Logger.debug('MediaClassHandler.getTagsOnChange(): Removed %s' % tagSet.difference(result))
        return(result)


    def includeRequiredElements(self, elements):
        """Add all required tags to a tagset.
        
        Set elements contains tags as String
        Return Set containing all tags as well as additional tags required by them 
        """
        result = set(elements)
        for aClass in self.getClasses():
            for anElement in self.getElementsOfClass(aClass):
                if (anElement in elements):
                    for requiredElement in self.getRequiredElementsOfClass(aClass):
                        result.add(requiredElement)
                    for requiredClassName in self.getRequiredClassesOfClass(aClass):
                        requiredTags = set(self.getElementsOfClassByName(requiredClassName))
                        if (len(requiredTags.intersection(elements)) == 0):
                            result.add(self.getElementsOfClassByName(requiredClassName)[0])  # requiredTags.pop())  # choose first tag from class definition
                    for prohibitedElement in self.getProhibitedElementsOfClass(aClass):
                        if (prohibitedElement in elements):
                            result.add(self.ElementIllegal)
        Logger.debug('MediaClassHandler.includeRequiredElements(%s): Added %s' % (elements, (result - elements)))
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
        
        Elements are introduced by TagSeparator (meaning the result is either empty or starts with a TagSeparator).
        """
        elements = self.orderElements(elementSet)
        result = (MediaClassHandler.TagSeparator.join(elements))
        if (not (result == '')):
            result = (MediaClassHandler.TagSeparator + result)
        return (result)


    def stringToElements(self, elementString):
        """Turn a (unicode) string into a set of (unicode) tags.
        
        String elementString contains a string of words
        Return a Set with all elements from ELEMENTSTRING   
        """
        elements = set(re.split(MediaClassHandler.RETagSeparatorsRecognized, elementString))
        if (u'' in elements):
            elements.remove(u'')
        return(elements) 


    def stringToKnownAndUnknownElements(self, elementString):
        """Turn a (unicode) string into (unicode) tags.
        
        Return (known, unknown) where
            Dictionary known maps class names to (unicode) tags
            Set unknown contains all remaining tags from elementString  
        """
        remainingElements = self.stringToElements(elementString)
        knownElements = {}
        # sort elements into class sequence
        for aClass in self.getClasses():
            className = aClass[self.KeyName]
            for classElement in self.getElementsOfClass(aClass):
                if (classElement in remainingElements):
                    remainingElements.remove(classElement)
                    if (className in knownElements.keys()):  # add known element...
                        knownElements[className].append(classElement)  # ...to an existing list
                    else:
                        knownElements[className] = [classElement]  # ...as a single-entry list
        return(knownElements, remainingElements)


# Event Handlers
# Internal - to change without notice
    def getClassByName(self, className):
        """Return a Dictionary defining the named class. 
           Return None if className does not exist.
        """
        for aClass in self.classes:
            if (aClass[self.KeyName] == className):
                return(aClass)
        return(None)


    def getClassOfTag(self, tagName):
        """Return the class to which the given tag belongs.

        String tagName
        Return Dictionary describing the class
            or None if tagName belongs to no class
        """
        for aClass in self.classes:
            if (tagName in self.getElementsOfClass(aClass)):
                return(aClass)
        return(None)


    def getRequiredElementsOfClass(self, aClass):
        """Return a list of all elements which must apply for aClass to be applicable. 
        """
        return(aClass[self.KeyRequired])
    

    def getRequiredClassesOfClass(self, aClass):
        """Return a list of all class names which must apply for aClass to be applicable.
        
        At least one tag from the resulting classes must be applied for aClass to be applicable.
        
        Return List of String
        """
        return(aClass[self.KeyRequiredClasses])

   
    def getProhibitedElementsOfClass(self, aClass):
        """Return a list of all elements which may not apply for className to be applicable. 
           Return None if className does not exist.
        """
        return(aClass[self.KeyProhibited])


    def readClassesFromFile(self, pathname):
        """Set self's internal state from the class definition in the given file.

        String pathname contains the file name
        """
        self.classes = []
        self.knownElements = []
        try:
            classFile = codecs.open(pathname, encoding=sys.getfilesystemencoding())
        except: 
            raise IOError, ('Cannot open "%s" to read tag classes!' % pathname) 
        for line in classFile:
            #print ("Read line >%s<" % line)
            line = line.strip()  # trim white space
            if ((len (line) == 0) or (line[0] == '#')): # empty or comment line, ignore
                #print ("Ignored empty or comment line")
                pass
            else: # non-comment, interpret
                tokens = line.split()
                className = tokens.pop(0) 
                Logger.debug('MediaClassHandler.readClassesFromFile(): Definition of "%s" is "%s"' % (className, tokens))
                multiple = False
                required = []
                requiredClasses = []
                prohibited = []
                elements = []
                while (len(tokens) > 0):
                    token = tokens.pop(0)
                    if (token == '[]'):  # this is a multiple-selection class
                        multiple = True
                    elif (token[0] == '+'):
                        name = token[1:]
                        if (self.isLegalElement(name)):
                            Logger.debug('MediaClassHandler.readClassesFromFile(): Required tag "%s"' % name)
                            required.append(name)
                        elif (self.getClassByName(name)):
                            Logger.debug('MediaClassHandler.readClassesFromFile(): Required class "%s"' % name)
                            requiredClasses.append(name)
                        else:
                            Logger.debug('MediaClassHandler.readClassesFromFile(): Requiring unknown tag "%s"' % name)
                            required.append(name)
                    elif (token[0] == '-'):
                        prohibited.append(token[1:])
                    else:
                        #print ("Adding element %s" % token)
                        elements.append(token)
                aClass = {self.KeyName:className, 
                          self.KeyRequired:required, 
                          self.KeyRequiredClasses:requiredClasses,
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


