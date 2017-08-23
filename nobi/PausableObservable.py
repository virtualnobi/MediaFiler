#! python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
import inspect
## Contributed
## nobi
import ObserverPattern
## Project



class PausableObservable(ObserverPattern.Observable): 
    """An Observable which can be paused, i.e., on which the update process can be paused and resumed.
    
    Which updates are paused may depend on 
    - the class or instance of the observable, 
    - the aspect to be updated,
    - the class or instance of the observer.
    
    Pausing updates is controlled by the class methods pauseUpdates() and resumeUpdates().
    """
    

# Constants
# Class Variables
    PausedTriples = []



# Class Methods
    @classmethod
    def pauseUpdates(clas, observable, aspect, observer):
        """Pause updates as specified.
        
        If observable, aspect or observer is None, it acts as a wildcard, matching all.
        
        object observable pause all updates from this object (if it's a class, pause updates from all instances) 
        String/Unicode aspect specifies which aspect to pause.
        object observer pause all updates at this object (if it's a class, pause updates on all instances)
        """
        if ((aspect <> None)
            and (not isinstance(aspect, str))
            and (not isinstance(aspect, unicode))):
            raise TypeError, 'pauseUpdates(): aspect must be either None, str or unicode!'
        clas.PausedTriples.append((observable, aspect, observer))


    @classmethod
    def resumeUpdates(clas, observable, aspect, observer):
        """Resume updates as specified. 
        
        The triple observer, aspect, observable must correspond to parameter of a prior call to pauseUpdates(), 
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
            raise ValueError, 'Trying to resume an observer specification which has not been paused!'



# Lifecycle
# Setters
# Other API Functions
    def doUpdateAspect(self, observer, aspect):
        """Call the updateAspect method of an observer, if updates are not paused.
        """
        stop = False
        for triple in self.__class__.PausedTriples: 
            if (self.matches(triple[0], self)
                and ((triple[1] == None)
                     or (triple[1] == aspect))
                and self.matches(triple[2], observer)):
                print('PausableObservable: Paused update of aspect "%s" of %s to %s' % (aspect, self, observer))
                stop = True
                break
        if (not stop):
            observer.updateAspect(self, aspect)


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
               or (inspect.isclass(matchingSpec)
                   and isinstance(matchingObject, matchingSpec)))



# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass


