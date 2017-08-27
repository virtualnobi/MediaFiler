'''MediaFilter

A observable which describes filter conditions for images.  

It should be possible to display and set filters without having complete data on the media. 
I.e., the media size filter must be definable independent of knowledge of all media sizes. 
This will allow to make the media set lazy-loading, and only if the size filter is actually 
used, all media must be read. 

The following aspects of ImageFilter are observable:
- changed: Filter has changed

(c) by nobisoft 2016-
'''


## Imports
# standard libraries
import re
import logging
import copy
# public libraries 
# nobi's libraries
from nobi.ObserverPattern import Observable
# project 



# Class
class MediaFilter(Observable):


# Constants
# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        Observable.__init__(self, ['changed'])
        # initialize (cannot use self.clear() since instance variables not yet defined)
        self.model = model
        self.active = False
        self.requiredElements = set()
        self.prohibitedElements = set()
        self.unknownElementRequired = False
        self.minimumSize = self.model.getMinimumSize()  # TODO: make lazy-loadable
        self.maximumSize = self.model.getMaximumSize()  # TODO: make lazy-loadable
        self.requiredMediaTypes = set()
        self.prohibitedMediaTypes = set()
        # special conditions for OrganizationByDate
        self.fromDate = None
        self.toDate = None
        # special conditions for OrganzationByName
        self.singleCondition = None
        return(None)


# Setters
    def setConditions(self, active=None, 
                      required=None, prohibited=None, unknownRequired=None, minimum=None, maximum=None,
                      requiredMediaTypes=None, prohibitedMediaTypes=None, 
                      single=None,
                      fromDate=None, toDate=None):
        """Set conditions as specified. Not passing an argument does not change conditions.
        
        Boolean active
        Set of String required
        Set of String prohibited
        Boolean unknownRequired
        Number minimum
        Number maximum
        Boolean single filters all groups (for organization by name)
        fromDate
        toDate
        """
        print('MediaFilter.setConditions: %s +%s, -%s, unknown %s, size %s - %s%s' 
              % (active, required, prohibited, unknownRequired, minimum, maximum, (', single' if single else '')))
        if ((not self.active) and (active <> True)):
            changed = False
        else:
            changed = (((active <> None) and (self.active <> active)) 
                       or ((required <> None) and (self.requiredElements <> required))
                       or ((prohibited <> None) and (self.prohibitedElements <> prohibited))
                       or ((unknownRequired <> None) and (self.unknownElementRequired <> unknownRequired))
                       or ((minimum <> None) and (self.minimumSize <> minimum))
                       or ((maximum <> None) and (self.maximumSize <> maximum))
                       or ((requiredMediaTypes <> None) and (self.requiredMediaTypes <> requiredMediaTypes))
                       or ((prohibitedMediaTypes <> None) and (self.prohibitedMediaTypes <> prohibitedMediaTypes))
                       or ((single <> None) and (self.singleCondition <> single))
                       or ((fromDate <> None) and (self.fromDate <> fromDate))
                       or ((toDate <> None) and (self.toDate <> toDate)))
        if (active <> None):
            self.active = active
        if (required <> None):
            self.requiredElements = required
        if (prohibited <> None):
            self.prohibitedElements = prohibited
        if (unknownRequired <> None):
            self.unknownElementRequired = unknownRequired
        if (minimum <> None):
            self.minimumSize = minimum
        if (maximum <> None):
            self.maximumSize = maximum
        if (requiredMediaTypes <> None):
            self.requiredMediaTypes = requiredMediaTypes
        if (prohibitedMediaTypes <> None):
            self.prohibitedMediaTypes = prohibitedMediaTypes
        if (single <> None):
            if (self.model.organizedByDate):
                logging.error('MediaFilter.setConditions(): Single/group filtering only allowed for media organized by name!')
            else:  # organized by name
                self.singleCondition = single
        if (fromDate <> None):
            if (self.model.organizedByDate):
                self.fromDate = fromDate
            else:  # organized by name
                logging.error('MediaFilter.setConditions(): Only images organized by date can be filtered by date!')
        if (toDate <> None):
            if (self.model.organizedByDate):
                self.toDate = toDate
            else:
                logging.error('MediaFilter.setConditions(): Only images organized by date can be filtered by date!')
#         print('         final conditions: %s +%s, -%s, unknown %s, size %s - %s%s' 
#               % (self.active, self.requiredElements, self.prohibitedElements, self.unknownElementRequired, 
#                  self.minimumSize, self.maximumSize, (', single' if self.singleCondition else '')))
        if (changed): 
            self.changedAspect('changed')
        print('MediaFilter.setCondition() finished as %s' % self)


    def clear(self):
        """Clears the filter. Does not change the activation state.
        """
        self.setConditions(required=set(), 
                           prohibited=set(), 
                           unknownRequired=False, 
                           minimum=self.model.getMinimumSize(), 
                           maximum=self.model.getMaximumSize(),
                           requiredMediaTypes=set(),
                           prohibitedMediaTypes=set(),
                           single=None)


    def setMediaTypes(self, required=None, prohibited=None):
        """Set a filter on media types. 

        set or None required
        set or None prohibited
        """
        print('MediaFilter.setMediaTypes() deprecated!')
        changed = (((required <> None)
                    and (required <> self.requiredMediaTypes))
                   or ((prohibited <> None)
                       and (prohibited <> self.prohibitedMediaTypes)))
        if (required <> None):
            self.requiredMediaTypes = required
        else:
            self.requiredMediaTypes = set()
        if (prohibited <> None):
            self.prohibitedMediaTypes = prohibited
        else:
            self.prohibitedMediaTypes = set()
        if (changed):
            self.changedAspect('changed')



# Getters
    def __str__(self):
        """Return a string representing self.
        """
        result = ('MediaFilter(' 
                  + ('active ' if self.active else '')
                  + (('requires %s ' % self.requiredElements) if 0 < len(self.requiredElements) else '')
                  + (('prohibits %s ' % self.prohibitedElements) if 0 < len(self.prohibitedElements) else '')
                  + ('requires unknown ' if self.unknownElementRequired else '')
                  + (('larger %s ' % self.minimumSize) if self.minimumSize else '')
                  + (('smaller %s ' % self.maximumSize) if self.maximumSize else '')
                  + (('isa %s ' % self.requiredMediaTypes) if (0 < len(self.requiredMediaTypes)) else '') 
                  + (('from %s ' % self.fromDate) if self.fromDate else '')
                  + (('to %s ' % self.toDate) if self.toDate else '')
                  + ('single' if self.singleCondition else '')
                  + ')')
        return(result)


    def getFilterConditions(self):
        """ Return a list with all filter conditions.
        
        Return a list containing
            Boolean active
            Set of String required
            Set of String prohibited
            Boolean unknownRequired
            Number minimum
            Number maximum
            Boolean single filters all groups (for organization by name)
            fromDate
            toDate
        """
        return(self.active,
               self.requiredElements,
               self.prohibitedElements,
               self.unknownElementRequired,
               self.minimumSize,
               self.maximumSize,
               self.singleCondition,
               self.fromDate,
               self.toDate)


    def getMediaTypes(self):
        """
        Returns (required, prohibited) where
            set required
            set prohibited
        """
        return(copy.copy(self.requiredMediaTypes), 
               copy.copy(self.prohibitedMediaTypes))
    

    def isEmpty(self):
        """Check whether the filter will reduce the set of media.
        
        Return True if no filter conditions are defined, False otherwise.
        """
        if (self.active):
            if ((len(self.requiredElements) > 0)
                or (len(self.prohibitedElements) > 0)
                or self.unknownElementRequired
                or (self.minimumSize > self.model.getMinimumSize())
                or (self.maximumSize < self.model.getMaximumSize())
                or (self.singleCondition <> None)
                or (self.fromDate <> None)
                or (self.toDate <> None)
                or (0 < len(self.requiredMediaTypes))
                or (0 < len(self.prohibitedMediaTypes))):
                return(False)
        return(True)


    def isFiltered(self, entry):
        """Check whether entry must be filtered. 
        
        Entry entry
        
        Returns True if entry shall be hidden, or False otherwise
        """
        entryFiltered = False  # assume entry will pass the filter, i.e., not be hidden
        if (self.active):
            # keep groups which have unfiltered subentries
            if (entry.isGroup()): 
                return(len(entry.getSubEntries(True)) == 0)
            # check for single/group requirement
            if (not self.model.organizedByDate):
                if (self.singleCondition == True):
                    if (not entry.isSingleton()):
                        return(True)
                elif (self.singleCondition == False):
                    if (entry.isSingleton()):
                        return(True)
                else:  # singleCondition == None
                    pass
            # check for unknown requirement
            if (self.unknownElementRequired): 
                if (self.model.organizedByDate):  # TODO: move to Organization
                    entryFiltered = (entry.getYear() <> entry.organizer.__class__.UnknownDateName)
                else: # organized by name, illegal name will satisfy unknown element requirement
                    match = re.match(r'([^\d]+)\d*', entry.getName())  # isolate name in name+number identifiers
                    if ((match <> None)
                        and (entry.organizer.nameHandler.isNameLegal(match.group(1)))  # legal name 
                        and (entry.getScene() <> entry.organizer.__class__.NewIndicator)):  # not a "new" scene
                        entryFiltered = True
                if (entryFiltered):
                    entryFiltered = (len(entry.getUnknownElements()) == 0)
            # check known class elements
            if (self.filteredByElements(entry)):
                return(True)
            # check file size requirements
            if ((0 < self.minimumSize)  # minimum size required 
                and (not entry.isGroup()) 
                and (entry.getFileSize() < self.minimumSize)):   # file smaller than that
                return(True)
            if ((0 < self.maximumSize)  # maximum size requirement
                and (not entry.isGroup())
                and (self.maximumSize < entry.getFileSize())):  # file larger than that
                return(True)
            # media type
            if (0 < len(self.requiredMediaTypes)):
                for cls in self.requiredMediaTypes:
                    if (isinstance(entry, cls)):
                        break  # match!
                else:  # no match in the loop
                    return(True)
            # date range 
            if ((self.fromDate)
                and (entry.organizer.getDateTaken() <= self.fromDate)):
                print('MediaFilter.isFiltered(): %s later than "%s"' % (self.fromDate, entry.getPath()))
                return(True)
            if ((self.toDate)
                and (entry.organizer.getDateTaken() >= self.toDate)):
                print('MediaFilter.isFiltered(): %s earlier than "%s"' % (self.fromDate, entry.getPath()))
                return(True)
            # single/group
            if (self.singleCondition <> None):
                if (self.singleCondition == entry.isGroup()):
                    return(True)
        return(entryFiltered)



# Internal
    def filteredByElements(self, entry):
        """Check whether entry shall be filtered due to class element conditions.

        Returns True if entry shall be hidden, or False otherwise
        """
        classHandler = self.model.getClassHandler()
        # check whether all required elements are contained
        for required in self.requiredElements:
            if (required in classHandler.getClassNames()):  # class required, check whether one element of class is present
                if (len(set(classHandler.getElementsOfClassByName(required)).intersection(set(entry.getKnownElements()))) == 0):  # no common elements
                    #print ("%s filtered because it does not contain an element from class %s" % (entry.getPath(), required))
                    return (True) 
            else:  # element required, check if present
                if (required not in entry.getElements()):
                    #print (u'"%s" filtered because it does not contain %s' % (entry.getPath(), required))
                    return (True)
        # check whether no prohibited element is contained
        for prohibited in self.prohibitedElements:
            if (prohibited in classHandler.getClassNames()):  # class prohibited, check that none of its elements is present
                if (len(set(classHandler.getElementsOfClassByName(prohibited)).intersection(set(entry.getKnownElements()))) > 0):  # common element
                    #print ("%s filtered because it contains an element from class %s" % (entry.getPath(), prohibited))
                    return (True)                    
            else:  # element prohibited, check that it is not present
                if (prohibited in entry.getElements()):
                    #print ("%s filtered because it contains %s" % (entry.getPath(), prohibited))
                    return (True)
        # getting here means no constraint was violated
        return (False)         

