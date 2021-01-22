'''MediaFilter

A observable which describes filter conditions for images.

It should be possible to display and set filters without having complete data on the media. 
I.e., the media size filter must be definable independent of knowledge of all media sizes. 
This will allow to make the media set lazy-loading, and only if the size filter is actually 
used, all media must be read. 
Done for min/max media resolution.

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
    ConditionKeyDuplicate = 'duplicate'
    ConditionKeyResolutionMinimum = 'minimum'
    ConditionKeyResolutionMaximum = 'maximum'
    ConditionKeyMediaTypesRequired = 'requiredMediaTypes'
    ConditionKeyMediaTypesProhibited ='prohibitedMediaTypes' 
    ConditionKeysForSets = [ConditionKeyRequired,  # translate None<->set() in Set/GetFilterValueFor()
                            ConditionKeyProhibited,
                            ConditionKeyUnknownTagsRequired,
                            ConditionKeyUnknownTagsProhibited,
                            ConditionKeyMediaTypesRequired,
                            ConditionKeyMediaTypesProhibited]


# Class Methods
    @classmethod
    def getConditionKeys(cls):
        """Return a list of all keys for filter conditions, to be used with setConditions() etc.
        
        Return list of String
        """
        return([MediaFilter.ConditionKeyRequired,
                MediaFilter.ConditionKeyProhibited,
                MediaFilter.ConditionKeyUnknownRequired,
                MediaFilter.ConditionKeyUnknownTagsRequired,
                MediaFilter.ConditionKeyUnknownTagsProhibited,
                MediaFilter.ConditionKeyDuplicate,
                MediaFilter.ConditionKeyResolutionMinimum,
                MediaFilter.ConditionKeyResolutionMaximum])



# Lifecycle 
    def __init__ (self, model):
        """
        """
        # inheritance
        Observable.__init__(self, ['changed', 'filterChanged'])
        # initialize (cannot use self.clear() since instance variables not yet defined)
        self.model = model
        self.active = False
        self.conditionMap = {key: None for key in MediaFilter.getConditionKeys()}
        self.requiredUnknownTags = set()
        self.prohibitedUnknownTags = set()
        self.requiredMediaTypes = set()
        self.prohibitedMediaTypes = set()



# Setters
    def setConditions(self, active=None, **kwargs):
        """Set conditions as specified. Not passing an argument does not change conditions. Passing None for an argument clears this filter condition.

        Setting conditions must be done in a single call/method as it will trigger filtering of media.
        
        Boolean         active
        Set of String   required
        Set of String   prohibited
        Boolean         unknownRequired
        Number          minimum
        Number          maximum
        Boolean         duplicate filters Single which are duplicates (and containing groups)
        
        OrganizationByName:
        Boolean         single keeps only singletons (i.e., not in named group)
        String          scene keeps only media in named groups with this scene number
        
        OrganizationByDate:
        Date            fromDate filters media before this date        
        Date            toDate filters media after this date
        
        Dictionary kwargs 
        """
        wasEmpty = self.isEmpty()
        wasFiltering = self.isFiltering()
        conditionsChanged = self.setConditionsAndCalculateChange(**kwargs)
        # TODO: move media type handling into setConditionsAndCalculateChange()
        requiredMediaTypes = (kwargs['requiredMediaTypes'] if ('requiredMediaTypes' in kwargs) else None)
        if (requiredMediaTypes != None):
            self.requiredMediaTypes = requiredMediaTypes
            self.prohibitedMediaTypes.difference_update(requiredMediaTypes)
        prohibitedMediaTypes = (kwargs['prohibitedMediaTypes'] if ('prohibitedMediaTypes' in kwargs) else None)
        if (prohibitedMediaTypes != None):
            self.prohibitedMediaTypes = prohibitedMediaTypes
            self.requiredMediaTypes.difference_update(prohibitedMediaTypes)
            
        filterChanged = False
        if ((active != None)
            and (self.active != active)):  # activation of filter changes
            if (active):  # filter is turned on
                filterChanged = (conditionsChanged
                                 or (not wasEmpty))
                self.active = True
            else:  # filter is turned off
                filterChanged = wasFiltering 
                self.active = False
        else:  # activation has not changed
            filterChanged = (self.active and conditionsChanged)
        if (filterChanged or conditionsChanged): 
            Logger.debug('MediaFiler.setConditions(): Throwing "changed"')
            self.changedAspect('changed')
            if (filterChanged): 
                Logger.debug('MediaFiler.setConditions(): Throwing "filterChanged"')
                self.changedAspect('filterChanged')
        Logger.debug('MediaFilter.setConditions() finished as %s' % self)


    def clear(self):
        """Clears the filter. Does not change the activation state.
        
        Needs to use setConditions() to calculate whether filter has changed, and whether filtering results will change. 
        """
        kwargs = {# 'required': set(),  
                  # 'prohibited': set(), 
#                   'requiredUnknownTags': set(),  
#                   'prohibitedUnknownTags': set(),
#                   'minimum': None,  # self.model.getMinimumResolution(),
#                   'maximum': None,  # self.model.getMaximumResolution(),
                  'requiredMediaTypes': set(),  # TODO: use generic keys
                  'prohibitedMediaTypes': set()}
        for key in self.__class__.getConditionKeys():
            kwargs[key] = None
        self.setConditions(**kwargs)
        Logger.debug('MediaFilter.clear() finished as %s' % self)


    def setFilterValueFor(self, conditionKey, conditionValue):
        """Set the filter for the given condition to the given value.
        
        Translate the conditions represented by sets (of tags, or types) into None if empty set is passed
        
        String conditionKey must be in MediaFilter.getConditionKeys()
        Object conditionValue
        """
        if (conditionKey in MediaFilter.ConditionKeysForSets):
            if (conditionValue):
                if (0 == len(conditionValue)):
                    conditionValue = None
                elif (not isinstance(conditionValue, set)):
                    print('MediaFilter.setFilterValue(): Correcting value type to set for "%s"' % (conditionValue))
                    conditionValue = set(conditionValue)
        if (conditionKey in self.__class__.getConditionKeys()):
            if (self.conditionMap[conditionKey] != conditionValue):
                self.conditionMap[conditionKey] = conditionValue
                self.changedAspect('changed')
                if (self.active):
                    self.changedAspect('filterChanged')
        else:
            raise ValueError('MediaFilter.setFilterValueFor(): Unknown condition key "%s"' % conditionKey)



# Getters
    def __repr__(self):
        """Return a string representing self.
        """
        if (self.getFilterValueFor(MediaFilter.ConditionKeyRequired)):
            requiredTags = self.getFilterValueFor(MediaFilter.ConditionKeyRequired)
        else: 
            requiredTags = set()
        if (self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsRequired)):
            requiredTags.update(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsRequired))
        if (self.getFilterValueFor(MediaFilter.ConditionKeyProhibited)):
            prohibitedTags = self.getFilterValueFor(MediaFilter.ConditionKeyProhibited)
        else: 
            prohibitedTags = set()
        if (self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited)):
            prohibitedTags.update(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited))
        minResolution = self.getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum)
        maxResolution = self.getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum)
        duplicateString = ('duplicates' if (self.getDuplicate() == True) else
                           'no duplicates' if (self.getDuplicate() == False) else
                           '')
        result = (('active, ' if self.active else '')
                  + (('requires %s, ' % requiredTags) if (0 < len(requiredTags)) else '')
                  + (('prohibits %s, ' % prohibitedTags) if (0 < len(prohibitedTags)) else '')
                  + (('%s unknown, ' % ('requires' if self.conditionMap[MediaFilter.ConditionKeyUnknownRequired] else 'prohibits')) 
                     if (self.conditionMap[MediaFilter.ConditionKeyUnknownRequired] != None) else '')
                  + (('larger %s%%, ' % minResolution) if minResolution else '')
                  + (('smaller %s%%, ' % maxResolution) if maxResolution else '')
                  + (('isa %s, ' % self.requiredMediaTypes) if (0 < len(self.requiredMediaTypes)) else '')
                  + duplicateString + ', '
                  )
        if (result != ''):
            result = result[:-2]
        result = (self.__class__.__name__ + '(' + result + ')') 
        return(result)


    def isActive(self):
        """Return whether the filter should be applied.
        """
        return(self.active)


    def isFiltering(self):
        """Check whether the filter will reduce the set of media.
        
        Return True if no filter conditions are defined, False otherwise.
        """
        if (self.active):
            if ((0 < len(self.requiredMediaTypes))
                or (0 < len(self.prohibitedMediaTypes))
                ):
                return True
            return (not self.isEmpty())
        return True


    def getFilterValueFor(self, key):
        """Return filter value for a filter condition
        
        Translate the conditions represented by sets (of tags, or types) into empty set if it's None internally

        String key is one of the strings in MediaFilter.getConditionKeys() 
        Return object
        """
        if (key in self.conditionMap):
            result = self.conditionMap[key]
            if ((key in MediaFilter.ConditionKeysForSets)
                and (result == None)):
                result = set()
            return result
        else:
            raise ValueError('MediaFilter.getFilterValueFor(): Unknown condition key %s' % key)


    def getRequiredUnknownTags(self):  # TODO: replace by getFilterValueFor()
        return(copy.copy(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsRequired)))


    def getProhibitedUnknownTags(self):  # TODO: replace by getFilterValueFor()
        """"
        Return None or set of String (with at least one element)
        """
        return(copy.copy(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited)))


    def getIsUnknownTagRequired(self):  # TODO: replace by getFilterValueFor()
        return(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownRequired))


    def getMediaTypes(self):  # TODO: replace by getFilterValueFor()
        """
        Returns (required, prohibited) where
            set required
            set prohibited
        """
        return(copy.copy(self.requiredMediaTypes), 
               copy.copy(self.prohibitedMediaTypes))


    def getDuplicate(self):  # TODO: replace by getFilterValueFor()
        """
        Return Boolean (or None) indicating whether duplicates are required
        """
        return(self.getFilterValueFor(MediaFilter.ConditionKeyDuplicate))


    def filtersEntry(self, entry):
        """Check whether entry must be filtered. 
        
        Filtering of Group entries is defined elsewhere to depend on filter state of its children.
        
        Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (not self.active):  # shortcut for inactive filter
            return False
        return self.filteredByConditions(entry)  # checking conditions, obeying inheritance of MediaFilter



# Internal
    def isEmpty(self):
        """Check whether self contains filter conditions (independent of active state). 
        """
        for key in self.conditionMap:
            if (self.conditionMap[key] != None):
                return False
        return True


    def setConditionsAndCalculateChange(self, **kwargs):
        """Set conditions according to specified parameters, and return indicator whether conditions changed
        
        Return Boolean indicating whether self's conditions changed
        """
        changed = False
        for key in self.__class__.getConditionKeys():
            if ((key in kwargs)
                and (kwargs[key] != self.conditionMap[key])):
                self.setFilterValueFor(key, kwargs[key])
                changed = True
                if (key in MediaFilter.ConditionKeysForSets):  # ensure values in a set-based condition are removed from complementary set-based condition
                    if (key == MediaFilter.ConditionKeyRequired):
                        complementaryKey = MediaFilter.ConditionKeyProhibited
                    elif (key == MediaFilter.ConditionKeyProhibited):
                        complementaryKey = MediaFilter.ConditionKeyRequired
                    elif (key == MediaFilter.ConditionKeyUnknownTagsRequired):
                        complementaryKey = MediaFilter.ConditionKeyUnknownTagsProhibited
                    elif (key == MediaFilter.ConditionKeyUnknownTagsProhibited):
                        complementaryKey = MediaFilter.ConditionKeyUnknownTagsRequired
                    elif (key == MediaFilter.ConditionKeyMediaTypesRequired):
                        complementaryKey = MediaFilter.ConditionKeyMediaTypesProhibited
                    elif (key == MediaFilter.ConditionKeyMediaTypesProhibited):
                        complementaryKey = MediaFilter.ConditionKeyMediaTypesRequired
                    self.setFilterValueFor(complementaryKey, 
                                           self.getFilterValueFor(complementaryKey).difference(self.getFilterValueFor(key)))
        return changed 


    def filteredByConditions(self, entry):
        """Check whether entry must be filtered. 
        
        Filter (= self) is verified to be active.
        Filtering of Group entries is defined elsewhere to depend on filter state of its children.
        
        Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (entry.isGroup()): 
            raise ValueError('MediaFilter.isFiltered(): Defined only for Singles, but passed a Group!')
        # for unknown requirements
        requiredUnknown = self.getFilterValueFor(MediaFilter.ConditionKeyUnknownRequired)
        requiredUnknownTags = self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsRequired)
        prohibitedUnknownTags = self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited)
        unknownTags = entry.getUnknownTags()
        unknownOrganization = entry.getOrganizer().isUnknown()
        if (requiredUnknown == True): 
            if (not unknownOrganization):  # organization fully specified, needs to have unknown tag
                if (0 == len(requiredUnknownTags)):  # ensure existence of some unknown tags
                    if (0 == len(unknownTags)):
                        Logger.debug('MediaFilter.filteredByConditions(): Filtered "%s" - no unknown tag' % (entry))
                        return(True)
                else:  # requiredUnknownTags given, check their existence
                    if (not requiredUnknownTags.issubset(unknownTags)): 
                        Logger.debug('MediaFilter.filteredByConditions(): Filtered "%s" - unknown tags "%s" missing' % (entry, unknownTags))
                        return(True)
        elif (requiredUnknown == False):
            if (unknownOrganization):  # organization incomplete, must be filtered
                return(True)
            elif (0 == len(prohibitedUnknownTags)):  # ensure no unknown tags exist
                if (0 < len(unknownTags)):
                    Logger.debug('MediaFilter.filteredByConditions(): Filtered "%s" - unknown tags exist' % (entry))
                    return(True)
            else:  # requiredUnknownTags given, check their absence
                if (prohibitedUnknownTags.issubset(unknownTags)): 
                    Logger.debug('MediaFilter.filteredByConditions(): Filtered "%s" - unknown tags "%s" exist' % (entry, unknownTags))
                    return(True)
        # media type
        if (0 < len(self.requiredMediaTypes)):
            for cls in self.requiredMediaTypes:
                if (isinstance(entry, cls)):
                    break  # match!
            else:  # no match in the loop
                return(True)
        # known class elements
        if (self.filteredByElements(entry)):
            return(True)
        # image resolution requirements
        if ((self.getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum) != None)  # minimum resolution required 
            and (not entry.isGroup()) 
            and (entry.getResolution() < self.getFilterValueFor(MediaFilter.ConditionKeyResolutionMinimum))):
            return(True)
        if ((self.getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum) != None)  # maximum resolution requirement
            and (not entry.isGroup())
            and (self.getFilterValueFor(MediaFilter.ConditionKeyResolutionMaximum) < entry.getResolution())): 
            return(True)
        # duplicates
        if (self.getDuplicate() != None):
            if (self.getDuplicate()):  # Entries without duplicates shall not appear
                if (0 == len(entry.getDuplicates())):
                    return(True)
            else:  # Entries with duplicates shall not appear
                if (0 != len(entry.getDuplicates())):
                    return(True)
        return(False)

    
    def filteredByElements(self, entry):
        """Check whether entry shall be filtered due to class element conditions.

        Returns True if entry shall be hidden, or False otherwise
        """
        classHandler = self.model.getClassHandler()
        # check whether all required elements are contained
        requiredTags = self.getFilterValueFor(MediaFilter.ConditionKeyRequired)
        for required in (requiredTags.union(self.requiredUnknownTags)):
            if (required in classHandler.getClassNames()):  # class required, check whether one element of class is present
                if (len(set(classHandler.getElementsOfClassByName(required)).intersection(set(entry.getKnownTags()))) == 0):  # no common elements
                    #print ("%s filtered because it does not contain an element from class %s" % (entry.getPath(), required))
                    return (True) 
            else:  # element required, check if present
                if (required not in entry.getTags()):
                    #print (u'"%s" filtered because it does not contain %s' % (entry.getPath(), required))
                    return (True)
        # check whether no prohibited element is contained
        prohibitedTags = self.getFilterValueFor(MediaFilter.ConditionKeyProhibited)
        for prohibited in (prohibitedTags.union(self.prohibitedUnknownTags)):
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

