#! python


## Imports
# standard libraries
# public libraries
# nobi's libraries


## Constants


## Class
class Observable (object):
    """An Observable accepts registrations of an Observer, which will be notified when the Observable changes.
    
       Part of the Observer pattern. 
    
       Observers can register for changes of an aspect of the Observer (addObbserverForAspect) 
       and will be notified by a call to updateAspect(). 
       Observers can also register for all aspects at once (addObserver). 
    """


## Lifecycle
    def __init__ (self, allAspects):
        """Set up empty Observer lists.    
        ALLASPECTS is a sequence containing all aspects. Using an aspect outside this list will raise a KeyError.
        """
        super(Observable, self).__init__()
        self.allAspects = allAspects  # sequence of legal aspects
        self.observersAllAspects = []  # sequence of Observers 
        self.observersSpecificAspects = {}  # dictionary of a list of Observers (value) for specific aspects (key)
        return (None)


    def destroy(self):
        """Prepare deletion of self. Remove all observer relations. 
        """
        self.observersAllAspects = []
        self.observersSpecificAspects = {}
        
                
# section: Observer handling
    def addObserver (self, observer):
        """Register observer for self.
        Ensure no observer is registered twice.
        """
        self.removeObserver(observer)  # ensure no registration exists
        self.observersAllAspects.append(observer)  # now add a single registration


    def addObserverForAspect (self, observer, aspect):
        """Register observer for an aspect of self.
        Ensure no observer is registered twice for the same aspect.
        """
        if (not observer in self.observersAllAspects):
            if (aspect in self.allAspects):
                if (aspect in self.observersSpecificAspects.keys()): # aspect has observers registered
                    if (not observer in self.observersSpecificAspects [aspect]):
                        self.observersSpecificAspects [aspect].append(observer) # append new observer
                else: # no observers registered for this aspect
                    self.observersSpecificAspects [aspect] = [observer] # create new list of observers for aspect
            else:
                raise KeyError


    def removeObserver (self, observer):
        """Remove observer from self, for all aspects.
        """
        if (observer in self.observersAllAspects):
            self.observersAllAspects.remove(observer)
        for aspect in self.observersSpecificAspects.keys():
            if (observer in self.observersSpecificAspects [aspect]):
                self.observersSpecificAspects [aspect].remove(observer) 


    def changed (self):
        """Notify all observers that self has changed.
        """
        for aspect in self.allAspects:
            self.changedAspect(aspect)


    def changedAspect (self, aspect):
        """Notify observers that aspect of self has changed.
        """
        if (aspect in self.allAspects):
            # notify all observers registered for certain aspects only
            if (aspect in self.observersSpecificAspects.keys()):
                registeredObservers = []
                registeredObservers.extend(self.observersSpecificAspects[aspect])  # freeze list in case an observer un-/re-registers
                for observer in registeredObservers:
                    #print('%s notifies %s of %s change' % (self, observer, aspect))
                    observer.updateAspect(self, aspect)
            # notify all observers registered for all aspects
            for observer in self.observersAllAspects:
                observer.updateAspect(self, aspect)
        else:
            raise KeyError



class Observer (object):
    """ An Observer can register to be notified of changes of an Observable. 
    
    Part of the Observer pattern. 
    
    The Observer will be notified when an aspect the Observable changed.
    """


## Observer handling
    def updateAspect (self, observable, aspect):
        """Aspect of observable has changed.
        """
        pass


