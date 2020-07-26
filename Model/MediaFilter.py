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
    ConditionKeyDuplicate = 'duplicate'
    ConditionKeyResolutionMinimum = 'minimum'  # TODO: turn into mapping parameters 
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
                MediaFilter.ConditionKeyDuplicate])



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
        self.minimumResolution = None  # self.model.getMinimumResolution()  # too costly
        self.maximumResolution = None  # self.model.getMaximumResolution()
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
#         requiredUnknownTags = (kwargs['requiredUnknownTags'] if ('requiredUnknownTags' in kwargs) else None)
#         prohibitedUnknownTags = (kwargs['prohibitedUnknownTags'] if ('prohibitedUnknownTags' in kwargs) else None)
        minimum = (kwargs['minimum'] if ('minimum' in kwargs) else None)
        maximum = (kwargs['maximum'] if ('maximum' in kwargs) else None)
        requiredMediaTypes = (kwargs['requiredMediaTypes'] if ('requiredMediaTypes' in kwargs) else None)
        prohibitedMediaTypes = (kwargs['prohibitedMediaTypes'] if ('prohibitedMediaTypes' in kwargs) else None)
#         duplicate = (kwargs['duplicate'] if ('duplicate' in kwargs) else None)

        conditionsChanged = self.setConditionsAndCalculateChange(**kwargs)
        filterChanged = False
        if ((active != None)
            and (self.active != active)):  # activation of filter changes
            if (active):  # filter is turned on
                self.active = True
                filterChanged = (conditionsChanged  # filtered media change if filter conditions have changed...
                                 or (not self.isEmpty()))  # ...or filter conditions existed up to now
            else:  # filter is turned off
                filterChanged = (not self.isEmpty())  # filtered media change if conditions existed up to now
                self.active = False
        else:  # activation has not changed
            filterChanged = (self.active and conditionsChanged)  # filtered media change if filter is active and conditions have changed
#         if (requiredUnknownTags != None):
#             self.requiredUnknownTags = requiredUnknownTags
#         if (prohibitedUnknownTags != None):
#             self.prohibitedUnknownTags = prohibitedUnknownTags
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
#         if (duplicate != None):
#             self.conditionMap[MediaFilter.ConditionKeyDuplicate] = duplicate
        if (filterChanged or conditionsChanged): 
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
        kwargs = {# 'required': set(),  
                  # 'prohibited': set(), 
#                   'requiredUnknownTags': set(),  
#                   'prohibitedUnknownTags': set(),
                  'minimum': None,  # self.model.getMinimumResolution(),  # TODO: use generic keys
                  'maximum': None,  # self.model.getMaximumResolution(),
                  'requiredMediaTypes': set(),
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
                    print('MediaFilter.setFilterValue(): Correcting list to set for "%s"' % (conditionValue))
                    conditionValue = set(conditionValue)
        if (conditionKey in MediaFilter.getConditionKeys()):
            if (self.conditionMap[conditionKey] != conditionValue):
                self.conditionMap[conditionKey] = conditionValue
                self.changedAspect('changed')
                if (self.active):
                    self.changedAspect('filterChanged')
        else:
            raise ValueError('MediaFilter.setFilterValueFor(): Unknown condition key %s' % conditionKey)



# Getters
    def __repr__(self):
        """Return a string representing self.
        """
        duplicateString = ('duplicates' if (self.getDuplicate() == True) else
                           'no duplicates' if (self.getDuplicate() == False) else
                           '')
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
        result = (('active, ' if self.active else '')
                  + (('requires %s, ' % requiredTags) if (0 < len(requiredTags)) else '')
                  + (('prohibits %s, ' % prohibitedTags) if (0 < len(prohibitedTags)) else '')
#                   + (('%s unknown, ' % ('requires' if self.conditionMap[MediaFilter.ConditionKeyUnknownRequired] else 'prohibits')) 
#                      if (self.conditionMap[MediaFilter.ConditionKeyUnknownRequired] != None) else '')
                  + (('larger %s, ' % self.minimumResolution) if self.minimumResolution else '')
                  + (('smaller %s, ' % self.maximumResolution) if self.maximumResolution else '')
                  + (('isa %s, ' % self.requiredMediaTypes) if (0 < len(self.requiredMediaTypes)) else '')
                  + duplicateString + ', '
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
        
        Translate the conditions represented by sets (of tags, or types) into empty set if it's None internally

        String key is one of the strings in MediaFilter.getConditionKeys() 
        Return object
        """
        if (key == MediaFilter.ConditionKeyResolutionMinimum):
            return(self.minimumResolution)
        elif (key == MediaFilter.ConditionKeyResolutionMaximum):
            return(self.maximumResolution)
        elif (key in self.conditionMap):
            result = self.conditionMap[key]
            if ((key in MediaFilter.ConditionKeysForSets)
                and (result == None)):
                result = set()
            return result
        else:
            raise ValueError('MediaFilter.getFilterValueFor(): Unknown condition key %s' % key)


    def getRequiredUnknownTags(self):
#         return(copy.copy(self.requiredUnknownTags))
        return(copy.copy(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsRequired)))


    def getProhibitedUnknownTags(self):
        """"
        Return None or set of String (with at least one element)
        """
#         return(copy.copy(self.prohibitedUnknownTags))
        return(copy.copy(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownTagsProhibited)))


    def getIsUnknownTagRequired(self):
        return(self.getFilterValueFor(MediaFilter.ConditionKeyUnknownRequired))


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
        return(self.getFilterValueFor(MediaFilter.ConditionKeyDuplicate))


    def isEmpty(self):
        """Check whether the filter will reduce the set of media.
        
        Return True if no filter conditions are defined, False otherwise.
        """
        if (self.active):
            if (# (len(self.requiredUnknownTags) > 0)
                # or (len (self.prohibitedUnknownTags) > 0)
                # or (self.conditionMap[MediaFilter.ConditionKeyUnknownRequired] != None)
                # or (self.conditionMap[MediaFilter.ConditionKeyUnknownTagsRequired] != None)
                # or (self.conditionMap[MediaFilter.ConditionKeyUnknownTagsProhibited] != None)  # or...
                ((self.minimumResolution != None) and (self.minimumResolution > self.model.getMinimumResolution()))
                or ((self.maximumResolution != None) and (self.maximumResolution < self.model.getMaximumResolution()))
                or (0 < len(self.requiredMediaTypes))
                or (0 < len(self.prohibitedMediaTypes))
                ):
                return(False)
            for key in self.conditionMap:
                if (self.conditionMap[key] != None):
                    return(False)
        return True


    def isFiltering(self, entry):
        """Check whether entry must be filtered. 
        
        Filtering of Group entries is defined elsewhere to depend on filter state of its children.
        
        Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (not self.active):  # shortcut for inactive filter
            return False
        return self.filteredByConditions(entry)  # checking conditions, obeying inheritance of MediaFilter



# Internal
    def setConditionsAndCalculateChange(self, **kwargs):
        """Set conditions according to specified parameters, and return indicator whether conditions changed
        
        Return Boolean indicating whether self's conditions changed
        """
        changed = False
        for key in MediaFilter.getConditionKeys():
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
        if (0 < len(requiredUnknownTags)):
            if (not requiredUnknownTags.issubset(unknownTags)): 
                return(True)
        elif (0 < len(prohibitedUnknownTags)):
            if (not prohibitedUnknownTags.isdisjoint(unknownTags)):
                return(True)
        elif (requiredUnknown == True):
            if ((0 == len(unknownTags))
                and (not entry.getOrganizer().isUnknown())):
#                Logger.debug('MediaFilter.isFiltered(): Filtered "%s" - no unknown element in "%s"' % (entry, entry.getUnknownTags()))
                return(True)
        elif (requiredUnknown == False):
            if ((0 < len(unknownTags))
                or (entry.getOrganizer().isUnknown())):
#                Logger.debug('MediaFilter.isFiltered(): Filtered "%s" - unknown element in "%s"' % (entry, entry.getUnknownTags()))
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
        if ((self.minimumResolution != None)  # minimum resolution required 
            and (not entry.isGroup()) 
            and (entry.getResolution() < self.minimumResolution)):
            return(True)
        if ((self.maximumResolution != None)  # maximum resolution requirement
            and (not entry.isGroup())
            and (self.maximumResolution < entry.getResolution())): 
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

