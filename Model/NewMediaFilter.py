#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2018-
"""


# Imports
## Standard
from __future__ import print_function
import logging
import gettext
import os.path
import glob
import json
## Contributed
## nobi
from nobi.ObserverPattern import Observable
## Project
import UI  # to access UI.PackagePath
from Model.MediaFilter import MediaFilter
import Model.Installer
#from Model.Single import Single
import Model.Single



# Internationalization  # requires "PackagePath = UI/__path__[0]" in _init_.py
try:
    LocalesPath = os.path.join(UI.PackagePath, '..', 'locale')
    Translation = gettext.translation('MediaFiler', LocalesPath)
except BaseException as e:  # likely an IOError because no translation file found
    try:
        language = os.environ['LANGUAGE']
    except:
        print('%s: No LANGUAGE environment variable found!' % (__file__))
    else:
        print('%s: No translation found at "%s"; using originals instead of locale %s. Complete error:' % (__file__, LocalesPath, language))
        print(e)
    def _(message): return message
else:
    _ = Translation.gettext
def N_(message): return message



# Package Variables
Logger = logging.getLogger(__name__)

ConditionOperatorAnd = "AND"
ConditionOperatorOr = "OR"
ConditionOperatorNot = "NOT"
ConditionOperators = [ConditionOperatorAnd, ConditionOperatorOr, ConditionOperatorNot]

ConditionModePositive = _('required')
ConditionModeNegative = _('prohibited')
ConditionModes = [ConditionModePositive, ConditionModeNegative]



class Condition(object): 
    """New-style filter condition on media
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self):
        """
        """
        # internal state


# Setters
# Getters
    def getString(self):
        """Return a string representing self's condition
        """
        raise NotImplementedError


    def filtersEntry(self, entry):
        """Check whether entry must be filtered. 
        
        Filtering of Group entries is defined elsewhere to depend on filter state of its children.
        
        Model.Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        raise NotImplementedError
    

# Event Handlers
# Other API Functions
# Internal - to change without notice
    pass


class ConditionComplex(Condition): 
    """New-style filter condition on media: Boolean Operators
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, operator, conditions):
        """
        str operator specifies the operator: "AND", "OR", "NOT"
        """
        # internal state
        if (not operator in ConditionOperators):
            raise ValueError('Operator of Condition can only be one of %s' % ConditionOperators)
        self.operator = operator
        if (0 == len(conditions)):
            raise ValueError('ConditionComplex(): Needs at least on sub-condition!')
        if ((self.operator == ConditionOperatorNot)
            and (1 < len(conditions))):
            raise ValueError('ConditionComplex(): NOT condition accepts at most one sub-condition, %s given!' % len(conditions))
        for c in conditions: 
            if (not isinstance(c, Condition)):
                raise ValueError('ComplexCondition(): "%s" is not a Condition!' % c)
            c.addObserverforAspect(self, 'changed')
        self.conditions = conditions



# Setters
# Getters
    def getOperator(self):
        return self.operator


    def getString(self):
        """Return a string representing self's condition
        """
        return self.operator

    
    def filtersEntry(self, entry):  # inherited
        """
        """
        if (self.operator == ConditionOperatorAnd):
            for condition in self.conditions:
                if (not condition.filtersEntry(entry)):
                    return False
            return True
        elif (self.operator == ConditionOperatorOr):
            for condition in self.conditions:
                if (condition.filtersEntry(entry)):
                    return True
            return False
        elif (self.operator == ConditionOperatorNot):
            return (not self.conditions[0].filtersEntry(entry))
        else:
            raise ValueError('FilterConditionComplex has illegal internal state: operator is %s' % self.operator)



# Event Handlers
# Other API Functions
# Internal - to change without notice



# Class
class ConditionTag(Condition): 
    """New-style filter conditions on media: Tag (non-)existence
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, tag, mode):
        """
        str tag
        MediaFilter.ConditionTag* mode
        """
        # inheritance
        super(Condition, self).__init__()
        # internal state
        if (isinstance(tag, str)):
            self.tag = tag
        else:
            raise ValueError('Illegal tag value when creating ConditionTag object: "%s"' % tag)
        if (mode in ConditionModes):
            self.mode = mode
        else:
            raise ValueError('Illegal mode when creating ConditionTag object: "%s"' % mode)


# Setters
# Getters
    def getString(self):
        """Return a string representing self's condition
        """
        return (_('Tag %s %s' % (self.tag, self.mode)))

    
    def filtersEntry(self, entry):  
        """
        """
        if (self.mode == NewMediaFilter.ConditionModePositive):
            return (self.tag in entry.getTags())
        elif (self.mode == NewMediaFilter.ConditionModeNegative):
            return (not self.tag in entry.getTags())
        else:
            raise ValueError('ConditionTag.filtersEntry(): Illegal internal state: mode is %s' % self.mode)


# Event Handlers
# Other API Functions
# Internal - to change without notice


# Class
class ConditionClass(Condition): 
    """New-style filter conditions on media: Class (non-)existence
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, cls, mode):
        """
        String cls
        MediaFilter.ConditionTag* mode
        """
        # inheritance
        super(Condition, self).__init__()
        # internal state
        if (isinstance(cls, str)):
            self.className = cls
        else:
            raise ValueError('Illegal class name when creating ConditionClass: "%s"' % cls)
        if (mode in ConditionModes):
            self.mode = mode
        else:
            raise ValueError('Illegal mode when creating ConditionClass: "%s"' % mode)


# Setters
# Getters
    def getString(self):
        """Return a string representing self's condition
        """
        return (_('Class %s %s' % (self.className, self.mode)))

    
    def filtersEntry(self, entry):  
        """
        """
        if (self.mode == NewMediaFilter.ConditionModePositive):
            # TOOD: one of the tags of entry must be in self.className
            # return (self.tag in entry.getTags())
            pass
        elif (self.mode == NewMediaFilter.ConditionModeNegative):
            # TOOD: none of the tags of entry must be in self.className
            # return (not self.tag in entry.getTags())
            pass


# Event Handlers
# Other API Functions
# Internal - to change without notice


# Class
class ConditionAnyUnknown(Condition): 
    """Requires something unknown about the entry, which might also depend on the MediaOrganization.
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self):
        """
        """
        super(Condition, self).__init__()
        # internal state


# Setters
# Getters
    def getString(self):
        """Return a string representing self's condition
        """
        return (_('Unknown tag required'))


    def filtersEntry(self, entry):
        """Check whether entry must be filtered. 
        
        Model.Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (0 < len(entry.getUnknownTags())):
            return True
        if (entry.getOrganizer().isUnknown()):
            return True
        return False


# Event Handlers
# Other API Functions
# Internal - to change without notice
    pass




# Class
class ConditionMediaType(Condition): 
    """Requires (or not) a certain media type.
    """
# Constants
    MediaTypes = [c.getMediaTypeName() for c in Model.Single.Single.__subclasses__()]  # @UndefinedVariable
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, mediaType, mode):
        """
        String mediaType specifies media type to filter
        String mode
        """
        super(Condition, self).__init__()
        # internal state
        if (mediaType in ConditionMediaType.MediaTypes):
            self.type = mediaType
        else:
            raise ValueError('Illegal media type when creating ConditionMediaType object: "%s"' % mediaType)
        if (mode in ConditionModes):
            self.mode = mode
        else:
            raise ValueError('Illegal mode when creating ConditionMediaType object: "%s"' % mode)


# Setters
# Getters
    def filtersEntry(self, entry):
        """Check whether entry must be filtered. 
        
        Model.Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (0 < len(entry.getUnknownTags())):
            return True
        if (entry.getOrganizer().isUnknown()):
            return True
        return False


# Event Handlers
# Other API Functions
# Internal - to change without notice
    pass




# Class
class ConditionSize(Condition): 
    """Requires a minimum or maximum media resolution.
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, percent, minMax):
        """
        """
        super(Condition, self).__init__()
        # internal state
        if (isinstance(percent, int)
            and (0 <= percent)
            and (percent <= 100)):
            self.percent = percent
        else:
            raise ValueError('Illegal percentage when creating ConditionSize object: "%s"' % percent)
        if (minMax in ['min', 'max']):
            self.minMax = minMax
        else:
            raise ValueError('Illegal minMax creating ConditionSize object: "%s"' % minMax)



# Setters
# Getters
    def getString(self):
        """Return a string representing self's condition
        """
        return (_('Size %s %s%%' % (self.minMax, self.percent)))


    def filtersEntry(self, entry):
        """Check whether entry must be filtered. 
        
        Model.Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        percentage = (entry.getResolution() / entry.getModel().getMaximumResolution())
        if (self.minMax == 'min'):
            return (self.percent <= percentage)
        elif (self.minMax == 'max'):
            return (percentage <= self.percent)
        else:
            ValueError('ConditionSize.filtersEntry(): Illegal internal state, minMax is %s' % self.minMax)


# Event Handlers
# Other API Functions
# Internal - to change without notice
    pass




# Class
class ConditionDuplicate(Condition): 
    """Filter media when doubles (do not) exist
    """
# Constants
# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, mode):
        """
        ConditionMode* mode
        """
        # inheritance
        super(Condition, self).__init__()
        # internal state
        if (mode in ConditionModes):
            self.mode = mode
        else:
            raise ValueError('Illegal mode when creating ConditionDouble object: "%s"' % mode)



# Setters
# Getters
    def getString(self):
        """Return a string representing self's condition
        """
        return (_('Duplicates %s') % (_('exist') if (self.mode == ConditionModePositive) else _('don''t exist')))


    def filtersEntry(self, entry):  
        """
        """
        if (self.mode == NewMediaFilter.ConditionModePositive):
            return (0 < len(entry.getDuplicates()))
        elif (self.mode == NewMediaFilter.ConditionModeNegative):
            return (0 == len(entry.getDuplicates()))
        else:
            raise ValueError('ConditionTag.filtersEntry(): Illegal internal state: mode is %s' % self.mode)

    

# Event Handlers
# Other API Functions
# Internal - to change without notice




# Class
class NewMediaFilter(Observable):
    """
    """


# Constants
    # ConditionKeyRequired = 'required'  
    # ConditionKeyProhibited = 'prohibited'
    # ConditionKeyUnknownRequired = 'unknownRequired'
    # ConditionKeyUnknownTagsRequired = 'requiredUnknownTags'
    # ConditionKeyUnknownTagsProhibited = 'prohibitedUnknownTags'
    # ConditionKeyDuplicate = 'duplicate'
    # ConditionKeyResolutionMinimum = 'minimum'
    # ConditionKeyResolutionMaximum = 'maximum'
    # ConditionKeyMediaTypesRequired = 'requiredMediaTypes'
    # ConditionKeyMediaTypesProhibited ='prohibitedMediaTypes' 
    # ConditionKeysForSets = [ConditionKeyRequired,  # translate None<->set() in Set/GetFilterValueFor()
    #                         ConditionKeyProhibited,
    #                         ConditionKeyUnknownTagsRequired,
    #                         ConditionKeyUnknownTagsProhibited,
    #                         ConditionKeyMediaTypesRequired,
    #                         ConditionKeyMediaTypesProhibited]
    #
    # Filenames = ['one', 'two']



# Class Methods
    @classmethod
    def getUsedFilterNames(self):
        """Return the filter names used on disk.
        
        Return a Set of Strings
        """
        dirName = os.path.join(Model.Installer.getFilterPath(), '*')
        try: 
            pathNames = glob.glob(dirName)
        except Exception as exc:
            Logger.warn('MediaFilter.getUsedFilterNames(): Error reading filter directory "%s" (error follows)\n%s' % (dirName, exc))
            pathNames = []
        filterNames = [os.path.basename(pn) for pn in pathNames]
        Logger.debug('MediaFilter.getUsedFilterNames(): Returning %s' % filterNames)
        return(set(filterNames))


    # @classmethod
    # def fromOldMediaFilter(cls, aMediaFilter):
    #     """Create a NewMediaFilter from an old MediaFilter.
    #
    #     Return NewMediaFilter
    #     """
    #
    #     self.setFilterName(aMediaFilter.getFilterName())
    #     firstLevelConditions = []
    #     tags = aMediaFilter.get
    #     newFilter = NewMediaFilter(aMediaFilter.getModel(), aMediaFilter.getName())
    #     newFilter.setCon    
    #     return newFilter
    
# Lifecycle 
    def __init__ (self, model, filterName=None):
        """
        Observable aspects:
        changed - self has changed and needs redisplay. The filtering effects of self did not change.
        filterChanged - the filtering effects of self have changed. Thrown in addition to changed.
        
        Model.MediaCollection model specifies the collection (to derive filters)
        String filterName specifies the name of the filter to load
        """
        # inheritance
        Observable.__init__(self, ['changed', 'filterChanged'])
        # initialize (cannot use self.clear() since instance variables not yet defined)
        self.model = model
        self.active = False
        self.condition = None
        self.name = filterName
        self.filterIsSaved = False
        # 
        if (filterName):
            Logger.debug('MediaFiler.__init__(): Loading file "%s"' % filterName)


    def saveFile(self):
        """Store a representation of self.
        
        Do not optimize the saved filter definition for brevity - loadFromFile() 
        depends on the complete list of condition types to reset unspecified filters.  
        
        Return True if successful, False otherwise
        """
        if (not self.filterName):
            raise ValueError('No name defined for media filter!')
        Logger.debug('MediaFilter.saveFile(): Saving as "%s"', self.filterName)
        fileName = os.path.join(Model.Installer.getFilterPath(), self.filterName)
        try:
            with open(fileName, "w") as aStream:
                self.condition.write(aStream)
        except Exception as e: 
            Logger.warn('NewMediaFilter.saveFile(): Failed to save filter "%s", error follows\n%s' % (self.filterName, e))
            return(False)
        self.filterIsSaved = True
        return(True)


    def loadFromFile(self, filename):
        """Load a filter definition from the specified absolute filename.
        
        str filename
        """
        Logger.debug('MediaFilter.loadFromFile(): Loading filter from "%s"' % filename)
        loadedConditionMap = {}  # no conditions recognized so far; to replace self's conditionMap in case of success
        complexConditionEmbedding = []  # no complex conditions (and, or, not) so far
        try:
            with open(filename, "r") as f:
                line = f.readline().rstrip()
                while (line != ''):
                    Logger.debug('MediaFilter.loadFromFile(): Processing "%s"' % line)
                    whitespaces = (len(line) - len(line.lstrip()))
                    if (whitespaces < len(complexConditionEmbedding)):  # close one latest complex condition
                        Logger.warn('MediaFilter.loadFromFile(): closing complex conditions not yet implemented!')
                    elif (whitespaces == len(complexConditionEmbedding)):  # continue with current complex condition
                        (key, space, rest) = line.lstrip().partition(' ')  # @UnusedVariable
                        if (key == ConditionOperatorAnd):  # TODO: add other complex condition types
                            if (len(complexConditionEmbedding) == 0):
                                complexConditionEmbedding.append(ConditionOperatorAnd)
                            else:
                                raise RuntimeError('Incorrect MediaFilter file format: Only one occurence of AND currently supported!')
                        elif (key in self.getConditionKeys()):
                            if (key in NewMediaFilter.ConditionKeysForSets):
                                loadedObject = set(json.loads(rest))
                            else:
                                loadedObject = json.loads(rest)
                            loadedConditionMap[key] = loadedObject
                    else:  # indicating additional embedding without prior condition marker
                        raise RuntimeError('Incorrect MediaFilter file format: Added embedding to level %s without condition keyword!' % whitespaces)
                    line = f.readline().rstrip()
        except Exception as exc: 
            Logger.warn('MediaFilter.loadFromFile(): Cannot load filter from file "%s" (error follows)\n%s' % (filename, exc))
            raise RuntimeError('MediaFilter cannot be loaded from file "%s"' % filename)
        (head, tail) = os.path.split(filename)  # @UnusedVariable
        self.setFilterName(tail)
        self.filterIsSaved = True
        self.setConditions(**loadedConditionMap)
        Logger.debug('MediaFilter.loadFromFile(): Closed file')



# Setters
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


    def setConditions(self, active=None, **kwargs):
        """Set conditions as specified. ConditionKey* constants are used as identifiers in KWARGS.
        - Not passing a condition key does not change this condition. 
        - Passing None for a condition key clears this condition.

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
        
        Dictionary kwargs mapping String to value 
        """
        wasEmpty = (not self.condition)
        wasFiltering = self.isFiltering()
        conditionsChanged = self.setConditionsAndCalculateChange(**kwargs)
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


    def setFilterValueFor(self, conditionKey, conditionValue, raiseChangedEvent=True):
        """Set the filter for the given condition to the given value.
        
        Translate the conditions represented by sets (of tags, or types) into None if empty set is passed
        
        String conditionKey must be in MediaFilter.getConditionKeys()
        Object conditionValue
        Boolean raiseChangedEvent indicates that 'changed' and 'filterChanged' events shall be raised if appropriate (internal use only)
        """
        if (conditionKey in NewMediaFilter.ConditionKeysForSets):
            if (conditionValue):
                if (0 == len(conditionValue)):
                    conditionValue = None
                elif (not isinstance(conditionValue, set)):
                    print('MediaFilter.setFilterValue(): Correcting value type to set for "%s"' % (conditionValue))
                    conditionValue = set(conditionValue)
        if (conditionKey in self.__class__.getConditionKeys()):
            if (self.conditionMap[conditionKey] != conditionValue):
                self.conditionMap[conditionKey] = conditionValue
                if (raiseChangedEvent):
                    self.changedAspect('changed')
                    if (self.active):
                        self.changedAspect('filterChanged')
        else:
            raise ValueError('MediaFilter.setFilterValueFor(): Unknown condition key "%s"' % conditionKey)



# Getters
    def __repr__(self):
        """Return a string representing self.
        """
        result = (self.__class__.__name__ + '(' + '' + ')') 
        return(result)


    def getModel(self):
        """Return the MediaCollection for which self is a MediaFilter.
        """
        return(self.model)


    def isActive(self):
        """Return whether the filter should be applied.
        """
        return(self.active)


    def isFiltering(self):
        """Check whether the filter will reduce the set of media.
        
        Return True if filter is active and conditions are defined, False otherwise.
        """
        return (self.isActive() 
                and (self.condition))


    def getFilterValueFor(self, key):
        """Return filter value for a filter condition
        
        Translate the conditions represented by sets (of tags, or types) into empty set if it's None internally

        String key is one of the strings in MediaFilter.getConditionKeys() 
        Return object
        """
        if (key in self.conditionMap):
            result = self.conditionMap[key]
            if ((key in NewMediaFilter.ConditionKeysForSets)
                and (result == None)):
                result = set()
            return result
        else:
            raise ValueError('MediaFilter.getFilterValueFor(): Unknown condition key %s' % key)


    def filtersEntry(self, entry):
        """Check whether entry must be filtered. 
        
        
        
        
        
        
        Filtering of Group entries is defined elsewhere to depend on filter state of its children.
        
        Single entry
        Returns True if entry shall be hidden, or False otherwise
        """
        if (not self.active):  # shortcut for inactive filter
            return False
        return self.condition.filtersEntry(entry) 



# Internal
    def createSimpleCondition(self, key, value):
        """
        """
        if (key == MediaFilter.ConditionKeyRequired):
            return ConditionTag(value, ConditionModePositive)
        elif (key == MediaFilter.ConditionKeyProhibited):
            return ConditionTag(value, ConditionModeNegative)
        elif (key == MediaFilter.ConditionKeyUnknownRequired):
            return ConditionAnyUnknown()
        elif (key == MediaFilter.ConditionKeyUnknownTagsRequired):
            return ConditionTag(value, ConditionModePositive)
        elif (key == MediaFilter.ConditionKeyUnknownTagsProhibited):
            return ConditionTag(value, ConditionModeNegative)
        elif (key == MediaFilter.ConditionKeyResolutionMinimum):
            return ConditionSize(value, 'min')
        elif (key == MediaFilter.ConditionKeyResolutionMaximum):
            return ConditionSize(value, 'max')
        elif (key == MediaFilter.ConditionKeyDuplicate):
            return ConditionDuplicate(ConditionModePositive)



    def setConditionsAndCalculateChange(self, **kwargs):
        """Set conditions according to specified parameters, and return indicator whether conditions changed
        
        Return Boolean indicating whether self's conditions changed
        """
        changed = False
        for key in self.__class__.getConditionKeys():
            if ((key in kwargs)
                and (kwargs[key] != self.conditionMap[key])):
                self.setFilterValueFor(key, kwargs[key], raiseChangedEvent=False)
                changed = True
                # if (key in MediaFilter.ConditionKeysForSets):  # ensure values in a set-based condition are removed from complementary set-based condition
                #     if (key == MediaFilter.ConditionKeyRequired):
                #         complementaryKey = MediaFilter.ConditionKeyProhibited
                #     elif (key == MediaFilter.ConditionKeyProhibited):
                #         complementaryKey = MediaFilter.ConditionKeyRequired
                #     elif (key == MediaFilter.ConditionKeyUnknownTagsRequired):
                #         complementaryKey = MediaFilter.ConditionKeyUnknownTagsProhibited
                #     elif (key == MediaFilter.ConditionKeyUnknownTagsProhibited):
                #         complementaryKey = MediaFilter.ConditionKeyUnknownTagsRequired
                #     elif (key == MediaFilter.ConditionKeyMediaTypesRequired):
                #         complementaryKey = MediaFilter.ConditionKeyMediaTypesProhibited
                #     elif (key == MediaFilter.ConditionKeyMediaTypesProhibited):
                #         complementaryKey = MediaFilter.ConditionKeyMediaTypesRequired
                #     self.setFilterValueFor(complementaryKey, 
                #                            self.getFilterValueFor(complementaryKey).difference(self.getFilterValueFor(key)),
                #                            raiseChangedEvent=False)
        return changed 



# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass


