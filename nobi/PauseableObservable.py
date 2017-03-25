#! python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
#import gettext
## Contributed
## nobi
import ObserverPattern
## Project



class PauseableObservable(ObserverPattern.Observable): 
    """An Observable which can be paused, i.e., on which the update process can be paused and resumed.
    
    Which updates are paused may depend on 
    - the class or instance of the observable, 
    - the aspect to be updated,
    - the class or instance of the observer.
    """
    

# Constants
# Class Variables
    PausedTriples = []



# Class Methods
    @classmethod
    def pauseUpdates(clas, observable, aspect, observer):
        """Pause updates as specified.
        
        If any of observable, aspect, observer is None, it acts as a wildcard, matching all.
        
        object observable pause all updates from this object (if it's a class, pause updates from all instances) 
        String aspect specifies which aspect to pause.
        object observer pause all updates at this object (if it's a class, pause updates on all instances)
        """
        # TODO: check that observable and observer are either class or instance
        if ((aspect <> None)
            and (not isinstance(aspect, str))
            and (not isinstance(aspect, unicode))):
            raise TypeError
        clas.PausedTriples.append((observable, aspect, observer))


    @classmethod
    def resumeUpdates(clas, observable, aspect, observer):
        """Resume updates as specified. 
        
        The triple observer, aspect, observable must correspond to a prior call to pauseUpdates, 
        otherwise a ValueError is raised.

        object observable  
        String aspect 
        object observer 
        """
        toRemove = None
        for triple in clas.PausedTriples:
            if ((triple[0] == observable)
                and (triple[1] == aspect)
                and (triple[2] == observer)):
                toRemove = triple
                break
        if (toRemove):
            clas.PausedTriples.remove(toRemove)
        else: 
            raise ValueError



# Lifecycle
    def __init__(self, allAspects):
        """
        """
        # inheritance
        super(PauseableObservable, self).__init__(allAspects)
        # internal state
        return(None)



# Setters
    def changedAspect (self, aspect):
        """Notify observers that aspect of self has changed.

        Check whether this update is paused, and if so, stop it.
        """
        stop = False
        for triple in self.__class__.PausedTriples: 
            if (self.matches(triple[0], self)
                and ((triple[1] == None)
                     or (triple[1] == aspect))):
                print('PauseableObservable: Update stopped for aspect "%s" on %s' % (aspect, self))
                stop = True
                break
        if (not stop):
            super(PauseableObservable, self).changedAspect(aspect)


    def doUpdateAspect(self, observer, aspect):
        """Call the updateAspect method of an observer, if updates are not paused.
        """
        stop = False
        for triple in self.__class__.PausedTriples: 
            if self.matches(triple[2], observer):
                print('PauseableObservable: Update not delivered to %s' % observer)
                stop = True
                break
        if (not stop):
            observer.updateAspect(self, aspect)



# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
    def matches(self, matchingSpec, matchingObject):
        """Check whether an object matches the specification given. 
        
        The object will match if it is equal to the matchingSpec, or its class is. 
        None as matchingSpec will match all objects. 
        
        object matchingSpec a set of class instances
        object matchingObject
        
        Return Boolean
        """
        return((None == matchingSpec)
               or (matchingSpec == matchingObject)
               or isinstance(matchingObject, matchingSpec))



# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass


