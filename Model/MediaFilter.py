'''MediaFilter

A observable which describes filter conditions for images.

#TODO: It should be possible to display and set filters without having complete data on the media. 
I.e., the media size filter must be definable independent of knowledge of all media sizes. 
This will allow to make the media set lazy-loading, and only if the size filter is actually 
used, all media must be read. 

The following aspects of ImageFilter are observable:
- changed: Filter has changed (including changes to an inactive filter). Listen to this for display of the filter.
- filterChanged: Filter has changed in a way that may change the filtered media items. Listen to this for any filtering.

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
    ConditionKeyRequired = 'required'
    ConditionKeyProhibited = 'prohibited'
    ConditionKeyUnknownRequired = 'unknownRequired'
    ConditionKeyUnknownTagsRequired = 'requiredUnknownTags'
    ConditionKeyUnknownTagsProhibited = 'prohibitedUnknownTags'
    ConditionKeyResolutionMinimum = 'minimum'
    ConditionKeyResolutionMaximum = 'maximum'
    ConditionKeyMediaTypesRequired = 'requiredMediaTypes'
    ConditionKeyMediaTypesProhibited ='prohibitedMediaTypes' 
    ConditionKeyDuplicate = 'Duplicate'
    ConditionKeyDateFrom = 'fromDate'  # TODO: move to OrganizsationByDate
    ConditionKeyDateTo = 'toDate'    
    SceneConditionKey = 'scene'  # TODO: move to OrganizationByName
    SingleConditionKey = 'Singleton'
    ConditionKeys = [ConditionKeyDuplicate,
                     SingleConditionKey,
                     SceneConditionKey,
                     ConditionKeyDateFrom,
                     ConditionKeyDateTo]



# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        Observable.__init__(self, ['changed', 'filterChanged'])
        # initialize (cannot use self.clear() since instance variables not yet defined)
        self.model = model
        self.active = False
        self.conditionMap = {key: None for key in MediaFilter.ConditionKeys}
        self.requiredElements = set()
        self.prohibitedElements = set()
        self.unknownElementRequired = False
        self.requiredUnknownTags = set()
        self.prohibitedUnknownTags = set()
        self.minimumResolution = 0  # self.model.getMinimumResolution()  # too costly
        self.maximumResolution = 1  # self.model.getMaximumResolution()
        self.requiredMediaTypes = set()
        self.prohibitedMediaTypes = set()
        # special conditions for OrganzationByName
        self.singleCondition = None


# Setters
    def setConditions(self, active=None, 
                      required=None, prohibited=None, 
                      requiredUnknownTags=None, prohibitedUnknownTags=None, unknownRequired=None, 
                      minimum=None, maximum=None,
                      requiredMediaTypes=None, prohibitedMediaTypes=None, 
                      duplicate=None,
                      fromDate=None, toDate=None,
                      single=None, scene=None):
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
        Boolean         duplicate filters Single which are duplicates (and containing groups)
        Boolean         single filters all groups (for organization by name)
        fromDate
        toDate
        
        Dictionary kwargs 
        """
        changed = (((active != None) and (self.active != active)) 
                   or ((required != None) and (self.requiredElements != required))
                   or ((prohibited != None) and (self.prohibitedElements != prohibited))
                   or ((requiredUnknownTags != None) and (self.requiredUnknownTags != requiredUnknownTags))
                   or ((prohibitedUnknownTags != None) and (self.prohibitedUnknownTags != prohibitedUnknownTags))
                   or ((unknownRequired != None) and (self.unknownElementRequired != unknownRequired))
                   or ((minimum != None) and (self.minimumResolution != minimum))
                   or ((maximum != None) and (self.maximumResolution != maximum))
                   or ((requiredMediaTypes != None) and (self.requiredMediaTypes != requiredMediaTypes))
                   or ((prohibitedMediaTypes != None) and (self.prohibitedMediaTypes != prohibitedMediaTypes))
                   or ((duplicate != None) and (self.conditionMap[MediaFilter.ConditionKeyDuplicate] != duplicate))
                   or (self.setDateRange(DateFrom=fromDate, DateTo=toDate))
                   or ((single != None) and (self.singleCondition != single))
                   or (self.setScene(scene=scene))
                   )
        kwargs = {'required': required,
                  'prohibited': prohibited,
                  'requiredUnknownTags': requiredUnknownTags,
                  'prohibitedUnknownTags': prohibitedUnknownTags,
                  'unknownRequired': unknownRequired, 
                  'minimum': minimum,
                  'maximum': maximum,
                  'requiredMediaTypes': requiredMediaTypes,
                  'prohibitedMediaTypes': prohibitedMediaTypes, 
                  'duplicate': duplicate,
                  'fromDate': fromDate, 
                  'toDate': toDate,
                  'single': single, 
                  'scene': scene
                  }
        filterChanged=False
        if (self.active != active):  # filtered elements will change if activation of filter changes
            filterChanged = True
        testChanged = self.setConditionsAndCalculateChange(active, **kwargs)
        if (testChanged != changed): 
            print('MediaFilter.setConditions(): Test function (%s) differs in result (%s,\n %s)' % (testChanged, changed, kwargs))
        if (changed and self.active):  # filtered elements will change if content changes for active filter
            filterChanged = True
        #TODO: should become obsolete if no deviations are reported by test above
        if (active != None):
            self.active = active
        if (required != None):
            self.requiredElements = required
            self.prohibitedElements.difference_update(required)
        if (prohibited != None):
            self.prohibitedElements = prohibited
            self.requiredElements.difference_update(prohibited)
        if (requiredUnknownTags != None):
            self.requiredUnknownTags = requiredUnknownTags
        if (prohibitedUnknownTags != None):
            self.prohibitedUnknownTags = prohibitedUnknownTags
        if (unknownRequired != None):
            self.unknownElementRequired = unknownRequired
        if (minimum != None):
            self.minimumResolution = minimum
        if (maximum != None):
            self.maximumResolution = maximum
        if (requiredMediaTypes != None):
            self.requiredMediaTypes = requiredMediaTypes
            self.prohibitedMediaTypes.difference_update(requiredMediaTypes)
        if (prohibitedMediaTypes != None):
            self.prohibitedMediaTypes = prohibitedMediaTypes
            self.requiredMediaTypes.difference_update(prohibitedMediaTypes)
        if (duplicate != None):
            self.conditionMap[MediaFilter.ConditionKeyDuplicate] = duplicate
        if (self.model.organizedByDate):  # TODO: move to MediaOrganization
            pass
        else:
            if (single != None):
                self.singleCondition = single
        if (changed): 
            Logger.debug('MediaFiler.setConditions(): Throwing "changed"')
            self.changedAspect('changed')
            if (filterChanged):  # can only change the filtered media if it has changed at all
                Logger.debug('MediaFiler.setConditions(): Throwing "filterChanged"')
                self.changedAspect('filterChanged')
        Logger.debug('MediaFilter.setConditions() finished as %s' % self)


    def clear(self):
        """Clears the filter. Does not change the activation state.
        
        Needs to use setConditions() to calculate whether filter has changed, and whether filtering results will change. 
        """
        self.setConditions(required=set(), 
                           prohibited=set(), 
                           requiredUnknownTags=set(),
                           prohibitedUnknownTags=set(),
                           unknownRequired=False, 
                           minimum=self.model.getMinimumResolution()(), 
                           maximum=self.model.getMaximumResolution()(),
                           requiredMediaTypes=set(),
                           prohibitedMediaTypes=set(),
                           duplicate=None,  # TODO: use generic keys
                           single=None,
                           fromDate=False,
                           toDate=False,
                           scene=False)  # TODO: move to MediaOrganization
        Logger.debug('MediaFilter.clear() finished as %s' % self)


    def setFilterValueFor(self, conditionKey, conditionValue):
        """Set the filter for the given condition to the given value.
        
        String conditionKey must be in MediaFilter.ConditionKeys
        Object conditionValue
        """
        if (conditionKey in MediaFilter.ConditionKeys):
            if (self.conditionMap[conditionKey] != conditionValue):
                self.conditionMap[conditionKey] = conditionValue
                self.changedAspect('changed')
                if (self.active):
                    self.changedAspect('filterChanged')
        else:
            raise ValueError('MediaFilter.setFilterValueFor(): Unknown condition key %s' % conditionKey)


    def setDateRange(self, **kwargs):
        """
        TODO: Move to OrganizationByDate
        TODO: use generic keys
        
        Return Boolean indicating the filter has changed
        """
        changed = False
        if ((MediaFilter.ConditionKeyDateFrom in kwargs)
            and (kwargs[MediaFilter.ConditionKeyDateFrom])):
            if (self.conditionMap[MediaFilter.ConditionKeyDateFrom] != kwargs[MediaFilter.ConditionKeyDateFrom]):
                changed = True
            self.conditionMap[MediaFilter.ConditionKeyDateFrom] = kwargs[MediaFilter.ConditionKeyDateFrom]
        else:
            if (self.conditionMap[MediaFilter.ConditionKeyDateFrom] != None):
                changed = True
            self.conditionMap[MediaFilter.ConditionKeyDateFrom] = None
        if ((MediaFilter.ConditionKeyDateTo in kwargs)
            and (kwargs[MediaFilter.ConditionKeyDateTo])):
            if (self.conditionMap[MediaFilter.ConditionKeyDateTo] != kwargs[MediaFilter.ConditionKeyDateTo]):
                changed = True
            self.conditionMap[MediaFilter.ConditionKeyDateTo] = kwargs[MediaFilter.ConditionKeyDateTo]
        else:
            if (self.conditionMap[MediaFilter.ConditionKeyDateTo] != None):
                changed = True
            self.conditionMap[MediaFilter.ConditionKeyDateTo] = None
        return(changed)


    def setScene(self, **kwargs):
        """
        TODO: Move to OrganizationByName
        
        Return Boolean indicating the filter has changed
        """
        changed = False
        if ((MediaFilter.SceneConditionKey in kwargs)
            and (kwargs[MediaFilter.SceneConditionKey])):
            if (self.conditionMap[MediaFilter.SceneConditionKey] != kwargs[MediaFilter.SceneConditionKey]):
                changed = True
            self.conditionMap[MediaFilter.SceneConditionKey] = kwargs[MediaFilter.SceneConditionKey]
        else:
            if (self.conditionMap[MediaFilter.SceneConditionKey] != None):
                changed = True
            self.conditionMap[MediaFilter.SceneConditionKey] = None
        return(changed)



# Getters
    def __repr__(self):
        """Return a string representing self.
        """
        duplicateString = ('duplicates' if (self.conditionMap[MediaFilter.ConditionKeyDuplicate] == True) else
                           'no duplicates' if (self.conditionMap[MediaFilter.ConditionKeyDuplicate] == False) else
                           '')
        result = (('active, ' if self.active else '')
                  + (('requires %s, ' % self.requiredElements) if 0 < len(self.requiredElements) else '')
                  + (('prohibits %s, ' % self.prohibitedElements) if 0 < len(self.prohibitedElements) else '')
                  + ('requires unknown, ' if self.unknownElementRequired else '')
                  + (('larger %s, ' % self.minimumResolution) if self.minimumResolution else '')
                  + (('smaller %s, ' % self.maximumResolution) if self.maximumResolution else '')
                  + (('isa %s, ' % self.requiredMediaTypes) if (0 < len(self.requiredMediaTypes)) else '')
                  + duplicateString + ', '
                  + (('from %s, ' % self.conditionMap[MediaFilter.ConditionKeyDateFrom]) if self.conditionMap[MediaFilter.ConditionKeyDateFrom] else '')  # TODO: Move to MediaOrganization
                  + (('to %s, ' % self.conditionMap[MediaFilter.ConditionKeyDateTo]) if self.conditionMap[MediaFilter.ConditionKeyDateTo] else '')
                  + ('single, ' if self.singleCondition else '')
                  + (('scene=%s, ' % self.conditionMap[MediaFilter.SceneConditionKey]) if (MediaFilter.SceneConditionKey in self.conditionMap) else '')
                  )
        if (result != ''):
            result = result[:-2]
        result = ('MediaFilter(' + result + ')') 
        return(result)


    def isActive(self):
        """Return whether the filter should be applied.
        """
        return(self.active)


    def getFilterValueFor(self, key):
        """Return filter value for a filter condition
        
        String key is of the strings in MediaFilter.ConditionKeys[] 
        Return object
        """
        if (key == MediaFilter.ConditionKeyRequired):
            return(self.requiredElements)
        elif (key == MediaFilter.ConditionKeyProhibited):
            return(self.prohibitedElements)
        elif (key == MediaFilter.ConditionKeyResolutionMinimum):
            return(self.minimumResolution)
        elif (key == MediaFilter.ConditionKeyResolutionMaximum):
            return(self.maximumResolution)
        elif (key in self.conditionMap):
            return(self.conditionMap[key])
        else:
            raise ValueError('MediaFilter.getFilterValueFor(): Unknown condition key %s' % key)


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
        return(self.conditionMap[MediaFilter.ConditionKeyDuplicate])


    def getDateRange(self):
        """TODO: Move to MediaOrganization
        """
#         return(self.fromDate, self.toDate)
        return(self.conditionMap[MediaFilter.ConditionKeyDateFrom], self.conditionMap[MediaFilter.ConditionKeyDateTo])


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
                or (self.minimumResolution > self.model.getMinimumResolution())
                or (self.maximumResolution < self.model.getMaximumResolution())
                or (self.singleCondition != None)
                or (self.conditionMap[MediaFilter.ConditionKeyDateFrom])  # TODO: Move to MediaOrganization
                or (self.conditionMap[MediaFilter.ConditionKeyDateTo])
                or (0 < len(self.requiredMediaTypes))
                or (0 < len(self.prohibitedMediaTypes))
                or (self.conditionMap[MediaFilter.ConditionKeyDuplicate] != None)
                or (self.conditionMap[MediaFilter.SceneConditionKey])):
                return(False)
        return(True)


    def isFiltered(self, entry):
        """Check whether entry must be filtered. 
        
        Filtering of Group entries is defined elsewhere to depend on filter state of its children.
        
        Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (not self.active):
            return(False)
        # keep groups which have unfiltered subentries
        if (entry.isGroup()): 
            raise ValueError('MediaFilter.isFiltered(): Defined only for Singles, but passed a Group!')
            return(len(entry.getSubEntries(filtering=True)) == 0)
        # for unknown requirement
        if (self.unknownElementRequired
            and (0 == len(entry.getUnknownTags()))
            and (not entry.getOrganizer().isUnknown())):
            Logger.debug('MediaFilter.isFiltered(): No unknown element in "%s" of "%s"' % (entry.getUnknownTags(), entry))
            return(True)
        # known class elements
        if (self.filteredByElements(entry)):
            return(True)
        # image resolution requirements
        if ((0 < self.minimumResolution)  # minimum resolution required 
            and (not entry.isGroup()) 
            and (entry.getResolution() < self.minimumResolution)):
            return(True)
        if ((0 < self.maximumResolution)  # maximum resolution requirement
            and (not entry.isGroup())
            and (self.maximumResolution < entry.getResolution())): 
            return(True)
        # media type
        if (0 < len(self.requiredMediaTypes)):
            for cls in self.requiredMediaTypes:
                if (isinstance(entry, cls)):
                    break  # match!
            else:  # no match in the loop
                return(True)
        # duplicates
        if (self.conditionMap[MediaFilter.ConditionKeyDuplicate] != None):
            if (self.conditionMap[MediaFilter.ConditionKeyDuplicate]):  # Entries without duplicates shall not appear
                if (0 == len(entry.getDuplicates())):
                    return(True)
            else:  # Entries with duplicates shall not appear
                if (0 != len(entry.getDuplicates())):
                    return(True)
        # organization-specific conditions
        if (entry.getOrganizer().isFilteredBy(self)):
            return(True)
        return(False)



# Internal
    def setConditionsAndCalculateChange(self, active, **kwargs):
        """Set conditions according to specified parameters, and return indicator whether conditions changed
        
        Boolean active indicates whether filter shall be active
        Return Boolean indicating whether self's conditions changed
        """
        changed = False
        for key in MediaFilter.ConditionKeys:
            if ((key in kwargs)
                and (kwargs[key] != self.conditionMap[key])):
                self.conditionMap[key] = kwargs[key]
                changed = True
                if (key == MediaFilter.ConditionKeyRequired):
                    self.conditionMap[key].difference_update(self.conditionMap[MediaFilter.ConditionKeyProhibited])
                elif (key == MediaFilter.ConditionKeyProhibited):
                    self.conditionMap[key].difference_update(self.conditionMap[MediaFilter.ConditionKeyRequired])
                elif (key == MediaFilter.ConditionKeyUnknownTagsRequired):
                    self.conditionMap[key].difference_update(self.conditionMap[MediaFilter.ConditionKeyUnknownTagsProhibited])
                elif (key == MediaFilter.ConditionKeyUnknownTagsProhibited):
                    self.conditionMap[key].difference_update(self.conditionMap[MediaFilter.ConditionKeyUnknownTagsRequired])
                elif (key == MediaFilter.ConditionKeyMediaTypesRequired):
                    self.conditionMap[key].difference_update(self.conditionMap[MediaFilter.ConditionKeyMediaTypesProhibited])
                elif (key == MediaFilter.ConditionKeyMediaTypesProhibited):
                    self.conditionMap[key].difference_update(self.conditionMap[MediaFilter.ConditionKeyMediaTypesRequired])
        if ((active != None) 
            and (self.active != active)):
            self.active = active
            changed = True                
        return(changed)


    def filteredByElements(self, entry):
        """Check whether entry shall be filtered due to class element conditions.

        Returns True if entry shall be hidden, or False otherwise
        """
        classHandler = self.model.getClassHandler()
        # check whether all required elements are contained
        for required in (self.requiredElements.union(self.requiredUnknownTags)):
            if (required in classHandler.getClassNames()):  # class required, check whether one element of class is present
                if (len(set(classHandler.getElementsOfClassByName(required)).intersection(set(entry.getKnownTags()))) == 0):  # no common elements
                    #print ("%s filtered because it does not contain an element from class %s" % (entry.getPath(), required))
                    return (True) 
            else:  # element required, check if present
                if (required not in entry.getTags()):
                    #print (u'"%s" filtered because it does not contain %s' % (entry.getPath(), required))
                    return (True)
        # check whether no prohibited element is contained
        for prohibited in (self.prohibitedElements.union(self.prohibitedUnknownTags)):
            if (prohibited in classHandler.getClassNames()):  # class prohibited, check that none of its elements is present
                if (len(set(classHandler.getElementsOfClassByName(prohibited)).intersection(set(entry.getKnownTags()))) > 0):  # common element
                    #print ("%s filtered because it contains an element from class %s" % (entry.getPath(), prohibited))
                    return (True)                    
            else:  # element prohibited, check that it is not present
                if (prohibited in entry.getTags()):
                    #print ("%s filtered because it contains %s" % (entry.getPath(), prohibited))
                    return (True)
        # getting here means no constraint was violated
        return (False)         

