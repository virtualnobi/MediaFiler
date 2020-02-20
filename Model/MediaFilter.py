'''MediaFilter

A observable which describes filter conditions for images.

It should be possible to display and set filters without having complete data on the media. 
I.e., the media size filter must be definable independent of knowledge of all media sizes. 
This will allow to make the media set lazy-loading, and only if the size filter is actually 
used, all media must be read. 

The following aspects of ImageFilter are observable:
- changed: Filter has changed (including changes to an inactive filter)
- filterChanged: Filter has changed in a way that may change the filtered media items

(c) by nobisoft 2016-
'''


## Imports
# standard
import logging
import copy
# contributed 
# nobi
from nobi.ObserverPattern import Observable
# project 



# Package Variables
Logger = logging.getLogger(__name__)



# Class
class MediaFilter(Observable):



# Constants
    DuplicateKey = 'Duplicate'
    SceneConditionKey = 'Scene'
    SingleConditionKey = 'Singleton'
    DateFromConditionKey = 'DateFrom'
    DateToConditionKey = 'DateTo'
    ConditionKeys = [DuplicateKey,
                     SingleConditionKey,
                     SceneConditionKey,
                     DateFromConditionKey,
                     DateToConditionKey]



# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        Observable.__init__(self, ['changed', 'filterChanged'])
        # initialize (cannot use self.clear() since instance variables not yet defined)
        self.model = model
        self.active = False
        self.conditionMap = {MediaFilter.DuplicateKey: None,
                             MediaFilter.SingleConditionKey: None,
                             MediaFilter.SceneConditionKey: None,
                             MediaFilter.DateFromConditionKey: None,
                             MediaFilter.DateToConditionKey: None}
        self.requiredElements = set()
        self.prohibitedElements = set()
        self.unknownElementRequired = False
        self.requiredUnknownTags = set()
        self.prohibitedUnknownTags = set()
        self.minimumSize = self.model.getMinimumSize()
        self.maximumSize = self.model.getMaximumSize()
        self.requiredMediaTypes = set()
        self.prohibitedMediaTypes = set()
        # special conditions for OrganzationByName
        self.singleCondition = None
        return(None)


# Setters
    def setConditions(self, active=None, 
                      required=None, prohibited=None, 
                      requiredUnknownTags=None, prohibitedUnknownTags=None, unknownRequired=None, 
                      minimum=None, maximum=None,
                      requiredMediaTypes=None, prohibitedMediaTypes=None, 
                      duplicate=None,
                      fromDate=None, toDate=None,
                      single=None, Scene=None):
        """Set conditions as specified. Not passing an argument does not change conditions.

        Setting conditions must be done in a single call/method as it will trigger filtering of media.
        
        TODO: Organization-specific conditions shall be captured in **kwargs and passed on to the respective organization.
    
        fromDate and toDate can be cleared by passing False.

        Boolean         active
        Set of String   required
        Set of String   prohibited
        Boolean         unknownRequired
        Number          minimum
        Number          maximum
        Boolean        duplicate filters Single which are duplicates (and containing groups)
        Boolean         single filters all groups (for organization by name)
        fromDate
        toDate
        
        Dictionary kwargs 
        """
        changed = (((active <> None) and (self.active <> active)) 
                   or ((required <> None) and (self.requiredElements <> required))
                   or ((prohibited <> None) and (self.prohibitedElements <> prohibited))
                   or ((requiredUnknownTags <> None) and (self.requiredUnknownTags <> requiredUnknownTags))
                   or ((prohibitedUnknownTags <> None) and (self.prohibitedUnknownTags <> prohibitedUnknownTags))
                   or ((unknownRequired <> None) and (self.unknownElementRequired <> unknownRequired))
                   or ((minimum <> None) and (self.minimumSize <> minimum))
                   or ((maximum <> None) and (self.maximumSize <> maximum))
                   or ((requiredMediaTypes <> None) and (self.requiredMediaTypes <> requiredMediaTypes))
                   or ((prohibitedMediaTypes <> None) and (self.prohibitedMediaTypes <> prohibitedMediaTypes))
                   or ((duplicate <> None) and (self.conditionMap[MediaFilter.DuplicateKey] <> duplicate))
                   or ((single <> None) and (self.singleCondition <> single))
                   or (self.setDateRange(DateFrom=fromDate, DateTo=toDate))
#                    or ((Scene <> None) 
#                        and (MediaFilter.SceneConditionKey in self.conditionMap) 
#                        and (Scene <> self.conditionMap[MediaFilter.SceneConditionKey]))
                   or (self.setScene(Scene=Scene)))
        if ((not self.active) and (active <> True)):
            filterChanged = False
        else:
            filterChanged = changed
        if (active <> None):
            self.active = active
        if (required <> None):
            self.requiredElements = required
            self.prohibitedElements.difference_update(required)
        if (prohibited <> None):
            self.prohibitedElements = prohibited
            self.requiredElements.difference_update(prohibited)
        if (requiredUnknownTags <> None):
            self.requiredUnknownTags = requiredUnknownTags
        if (prohibitedUnknownTags <> None):
            self.prohibitedUnknownTags = prohibitedUnknownTags
        if (unknownRequired <> None):
            self.unknownElementRequired = unknownRequired
        if (minimum <> None):
            self.minimumSize = minimum
        if (maximum <> None):
            self.maximumSize = maximum
        if (requiredMediaTypes <> None):
            self.requiredMediaTypes = requiredMediaTypes
            self.prohibitedMediaTypes.difference_update(requiredMediaTypes)
        if (prohibitedMediaTypes <> None):
            self.prohibitedMediaTypes = prohibitedMediaTypes
            self.requiredMediaTypes.difference_update(prohibitedMediaTypes)
        if (duplicate <> None):
            self.conditionMap[MediaFilter.DuplicateKey] = duplicate
        if (self.model.organizedByDate):  # TODO: move to MediaOrganization
            pass
        else:
            if (single <> None):
                self.singleCondition = single
#             if (Scene <> None):
#                 if (Scene == 0):
#                     if (MediaFilter.SceneConditionKey in self.conditionMap):
#                         del self.conditionMap[MediaFilter.SceneConditionKey]
#                 else:
#                     self.conditionMap[MediaFilter.SceneConditionKey] = Scene
        if (changed): 
            Logger.debug('MediaFiler.setConditions(): Throwing "changed"')
            self.changedAspect('changed')
            if (filterChanged):  # can only change the filtered media if it has changed at all
                Logger.debug('MediaFiler.setConditions(): Throwing "filterChanged"')
                self.changedAspect('filterChanged')
        Logger.debug('MediaFilter.setConditions() finished as %s' % self)


    def clear(self):
        """Clears the filter. Does not change the activation state.
        """
        self.setConditions(required=set(), 
                           prohibited=set(), 
                           requiredUnknownTags=set(),
                           prohibitedUnknownTags=set(),
                           unknownRequired=False, 
                           minimum=self.model.getMinimumSize(), 
                           maximum=self.model.getMaximumSize(),
                           requiredMediaTypes=set(),
                           prohibitedMediaTypes=set(),
                           duplicate=None,  # TODO: use generic keys
                           single=None,
                           fromDate=False,
                           toDate=False,
                           Scene=False)  # TODO: move to MediaOrganization
        Logger.debug('MediaFilter.clear() finished as %s' % self)


    def setFilterValueFor(self, conditionKey, conditionValue):
        """Set the filter for the given condition to the given value.
        
        String conditionKey must be in MediaFilter.ConditionKeys
        Object conditionValue
        """
        if (conditionKey in MediaFilter.ConditionKeys):
            if (self.conditionMap[conditionKey] <> conditionValue):
                self.conditionMap[conditionKey] = conditionValue
                self.changedAspect('changed')
                if (self.active):
                    self.changedAspect('filterChanged')
        else:
            raise ValueError, ('MediaFilter.setFilterValueFor(): Unknown condition key %s' % conditionKey)


    def setDateRange(self, **kwargs):
        """
        TODO: Move to OrganizationByDate
        TODO: use generic keys
        
        Return Boolean indicating the filter has changed
        """
        changed = False
        if ((MediaFilter.DateFromConditionKey in kwargs)
            and (kwargs[MediaFilter.DateFromConditionKey])):
            if (self.conditionMap[MediaFilter.DateFromConditionKey] <> kwargs[MediaFilter.DateFromConditionKey]):
                changed = True
            self.conditionMap[MediaFilter.DateFromConditionKey] = kwargs[MediaFilter.DateFromConditionKey]
        else:
            if (self.conditionMap[MediaFilter.DateFromConditionKey] <> None):
                changed = True
            self.conditionMap[MediaFilter.DateFromConditionKey] = None
        if ((MediaFilter.DateToConditionKey in kwargs)
            and (kwargs[MediaFilter.DateToConditionKey])):
            if (self.conditionMap[MediaFilter.DateToConditionKey] <> kwargs[MediaFilter.DateToConditionKey]):
                changed = True
            self.conditionMap[MediaFilter.DateToConditionKey] = kwargs[MediaFilter.DateToConditionKey]
        else:
            if (self.conditionMap[MediaFilter.DateToConditionKey] <> None):
                changed = True
            self.conditionMap[MediaFilter.DateToConditionKey] = None
        return(changed)


    def setScene(self, **kwargs):
        """
        TODO: Move to OrganizationByName
        
        Return Boolean indicating the filter has changed
        """
        changed = False
        if ((MediaFilter.SceneConditionKey in kwargs)
            and (kwargs[MediaFilter.SceneConditionKey])):
            if (self.conditionMap[MediaFilter.SceneConditionKey] <> kwargs[MediaFilter.SceneConditionKey]):
                changed = True
            self.conditionMap[MediaFilter.SceneConditionKey] = kwargs[MediaFilter.SceneConditionKey]
        else:
            if (self.conditionMap[MediaFilter.SceneConditionKey] <> None):
                changed = True
            self.conditionMap[MediaFilter.SceneConditionKey] = None
        return(changed)



# Getters
    def __repr__(self):
        """Return a string representing self.
        """
        duplicateString = ('duplicates' if (self.conditionMap[MediaFilter.DuplicateKey] == True) else
                           'no duplicates' if (self.conditionMap[MediaFilter.DuplicateKey] == False) else
                           '')
        result = (('active, ' if self.active else '')
                  + (('requires %s, ' % self.requiredElements) if 0 < len(self.requiredElements) else '')
                  + (('prohibits %s, ' % self.prohibitedElements) if 0 < len(self.prohibitedElements) else '')
                  + ('requires unknown, ' if self.unknownElementRequired else '')
                  + (('larger %s, ' % self.minimumSize) if self.minimumSize else '')
                  + (('smaller %s, ' % self.maximumSize) if self.maximumSize else '')
                  + (('isa %s, ' % self.requiredMediaTypes) if (0 < len(self.requiredMediaTypes)) else '')
                  + duplicateString + ', '
                  + (('from %s, ' % self.conditionMap[MediaFilter.DateFromConditionKey]) if self.conditionMap[MediaFilter.DateFromConditionKey] else '')  # TODO: Move to MediaOrganization
                  + (('to %s, ' % self.conditionMap[MediaFilter.DateToConditionKey]) if self.conditionMap[MediaFilter.DateToConditionKey] else '')
                  + ('single, ' if self.singleCondition else '')
                  + (('scene=%s, ' % self.conditionMap[MediaFilter.SceneConditionKey]) if (MediaFilter.SceneConditionKey in self.conditionMap) else '')
                  )
        if (result <> ''):
            result = result[:-2]
        result = ('MediaFilter(' + result + ')') 
        return(result)


    def isActive(self):
        """Return whether the filter should be applied.
        """
        return(self.active)


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
               {k: v for k, v in self.conditionMap.iteritems() if (v)})


    def getFilterValueFor(self, filterConditionKey):
        """Return filter value for a filter condition
        
        filterConditionKey is of the strings in MediaFilter.ConditionKeys[]
        
        String filterConditionKey 
        Return object
        """
        return(self.conditionMap[filterConditionKey])


    def getScene(self):
        try: 
            return(self.conditionMap[MediaFilter.SceneConditionKey])
        except: 
            return(None)


    def getRequiredUnknownTags(self):
        return(copy.copy(self.requiredUnknownTags))


    def getProhibitedUnknownTags(self):
        return(copy.copy(self.prohibitedUnknownTags))


    def getAnyUnknownTag(self):
        return(self.unknownElementRequired)


    def getMediaTypes(self):
        """
        Returns (required, prohibited) where
            set required
            set prohibited
        """
        return(copy.copy(self.requiredMediaTypes), 
               copy.copy(self.prohibitedMediaTypes))


    def getDuplicate(self):
        """
        Return Boolean (or None) indicating whether duplicates are required
        """
        return(self.conditionMap[MediaFilter.DuplicateKey])


    def getDateRange(self):
        """TODO: Move to MediaOrganization
        """
#         return(self.fromDate, self.toDate)
        return(self.conditionMap[MediaFilter.DateFromConditionKey], self.conditionMap[MediaFilter.DateToConditionKey])


    def getSingleton(self):
        """TODO: Move to MediaOrganization
        """
        return(self.singleCondition)


    def isEmpty(self):
        """Check whether the filter will reduce the set of media.
        
        Return True if no filter conditions are defined, False otherwise.
        """
        if (self.active):
            if ((len(self.requiredElements) > 0)
                or (len(self.prohibitedElements) > 0)
                or (len(self.requiredUnknownTags) > 0)
                or (len (self.prohibitedUnknownTags) > 0)
                or self.unknownElementRequired
                or (self.minimumSize > self.model.getMinimumSize())
                or (self.maximumSize < self.model.getMaximumSize())
                or (self.singleCondition <> None)
                or (self.conditionMap[MediaFilter.DateFromConditionKey])  # TODO: Move to MediaOrganization
                or (self.conditionMap[MediaFilter.DateToConditionKey])
                or (0 < len(self.requiredMediaTypes))
                or (0 < len(self.prohibitedMediaTypes))
                or (self.conditionMap[MediaFilter.DuplicateKey] <> None)
                or (self.conditionMap[MediaFilter.SceneConditionKey])):
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
            Logger.debug('MediaFilter.isFiltered(): No unknown element in "%s" of "%s"' % (entry.getUnknownElements(), entry))
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
        # duplicates
        if (self.conditionMap[MediaFilter.DuplicateKey] <> None):
            if (self.conditionMap[MediaFilter.DuplicateKey]):  # Entries without duplicates shall not appear
                if (0 == len(entry.getDuplicates())):
                    return(True)
            else:  # Entries with duplicates shall not appear
                if (0 <> len(entry.getDuplicates())):
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
        for required in (self.requiredElements.union(self.requiredUnknownTags)):
            if (required in classHandler.getClassNames()):  # class required, check whether one element of class is present
                if (len(set(classHandler.getElementsOfClassByName(required)).intersection(set(entry.getKnownElements()))) == 0):  # no common elements
                    #print ("%s filtered because it does not contain an element from class %s" % (entry.getPath(), required))
                    return (True) 
            else:  # element required, check if present
                if (required not in entry.getElements()):
                    #print (u'"%s" filtered because it does not contain %s' % (entry.getPath(), required))
                    return (True)
        # check whether no prohibited element is contained
        for prohibited in (self.prohibitedElements.union(self.prohibitedUnknownTags)):
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

