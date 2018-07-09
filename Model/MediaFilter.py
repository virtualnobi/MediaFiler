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
#import re
import logging
import copy
# public libraries 
# nobi's libraries
from nobi.ObserverPattern import Observable
# project 
#from .MediaClassHandler import MediaClassHandler



# Class
class MediaFilter(Observable):



# Constants
    Logger = logging.getLogger(__name__)
    SceneConditionIndex = 'Scene'
    SingleConditionIndex = 'Singleton'
    ConditionKeys = [SingleConditionIndex,
                     SceneConditionIndex]



# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        Observable.__init__(self, ['changed'])
        # initialize (cannot use self.clear() since instance variables not yet defined)
        self.model = model
        self.active = False
        self.conditionMap = {MediaFilter.SingleConditionIndex: None,
                             MediaFilter.SceneConditionIndex: None}
        self.requiredElements = set()
        self.prohibitedElements = set()
        self.unknownElementRequired = False
        self.minimumSize = self.model.getMinimumSize()
        self.maximumSize = self.model.getMaximumSize()
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
                      fromDate=None, toDate=None,
                      Scene=None):
        """Set conditions as specified. Not passing an argument does not change conditions.
        
        fromDate and toDate can be cleared by passing False.
        
        Boolean active
        Set of String required
        Set of String prohibited
        Boolean unknownRequired
        Number minimum
        Number maximum
        Boolean single filters all groups (for organization by name)
        fromDate
        toDate
        
        Dictionary kwargs 
        """
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
                       or ((toDate <> None) and (self.toDate <> toDate))
                       or ((Scene <> None) and (Scene <> self.conditionMap[MediaFilter.SceneConditionIndex])))
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
        if (self.model.organizedByDate):  # TODO: move to MediaOrganization
            if (fromDate == False):
                self.fromDate = None
            elif (fromDate <> None):
                self.fromDate = fromDate
            if (toDate == False):
                self.toDate = None
            elif (toDate <> None):
                self.toDate = toDate
        else:
            if (single <> None):
                self.singleCondition = single
            if (Scene <> None):
                if (Scene == 0):
                    if (MediaFilter.SceneConditionIndex in self.conditionMap):
                        del self.conditionMap[MediaFilter.SceneConditionIndex]
                else:
                    self.conditionMap[MediaFilter.SceneConditionIndex] = Scene
        if (changed): 
            self.changedAspect('changed')
        MediaFilter.Logger.debug('MediaFilter.setCondition() finished as %s' % self)


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
                           single=None,
                           fromDate=False,
                           toDate=False,
                           Scene=None)  # TODO: move to MediaOrganization
        MediaFilter.Logger.debug('MediaFilter.clear() finished as %s' % self)



# Getters
    def __repr__(self):
        """Return a string representing self.
        """
        result = ('MediaFilter(' 
                  + ('active, ' if self.active else '')
                  + (('requires %s, ' % self.requiredElements) if 0 < len(self.requiredElements) else '')
                  + (('prohibits %s, ' % self.prohibitedElements) if 0 < len(self.prohibitedElements) else '')
                  + ('requires unknown, ' if self.unknownElementRequired else '')
                  + (('larger %s ' % self.minimumSize) if self.minimumSize else '')
                  + (('smaller %s ' % self.maximumSize) if self.maximumSize else '')
                  + (('isa %s ' % self.requiredMediaTypes) if (0 < len(self.requiredMediaTypes)) else '') 
                  + (('from %s ' % self.fromDate) if self.fromDate else '')
                  + (('to %s ' % self.toDate) if self.toDate else '')
                  + ('single' if self.singleCondition else '')
                  + (('scene=%s' % self.conditionMap[MediaFilter.SceneConditionIndex]) if (MediaFilter.SceneConditionIndex in self.conditionMap) else '')
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
               self.toDate,
               {k: v for k, v in self.conditionMap.iteritems() if (v)})


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
                or (0 < len(self.prohibitedMediaTypes))
                or (self.conditionMap[MediaFilter.SceneConditionIndex])):
                return(False)
        return(True)


    def isFiltered(self, entry):
        """Check whether entry must be filtered. 
        
        Entry entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (not self.active):
            return(False)
        # keep groups which have unfiltered subentries
        if (entry.isGroup()): 
            return(len(entry.getSubEntries(filtering=True)) == 0)
        # for unknown requirement
        if (self.unknownElementRequired
            and (0 == len(entry.getUnknownElements()))
            and (not entry.getOrganizer().isUnknown())):
            return(True)
        # known class elements
        if (self.filteredByElements(entry)):
            return(True)
        # file size requirements
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
        # organization-specific conditions
        if (entry.getOrganizer().isFilteredBy(self)):
            return(True)
        return(False)



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

