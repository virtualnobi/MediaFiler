#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2021-
"""


# Imports
## Standard
from __future__ import print_function
## Contributed
## nobi
## Project



def memoize(numberOfCalls):
    """Return a decorator which will memoize a function. 
    
    Beware of complex parameters to the function to memoize!
    
    int numberOfCalls specifies the number of most-recent calls to memoize (0 to indicate all history)
    Returns Callable usable as decorator
    """
    def decorator(function):
        history = []  # keep a history for memoized function, with tuples of parameters and result of memoized function
        def executor(*args, **kwargs):
            nonlocal history  
            # first, check whether a result for these parameters has been memoized
            for index in range(len(history)):
                if (history[index][0] == (args, kwargs)):  # found memorized call with identical parameters
                    call = history.pop(index)  # remove call from sequence
                    history.insert(0, call)  # add call again as last recent call
                    return(call[1])  # return memorized parameters
            # if not, ensure limit of history is observed
            if ((0 < numberOfCalls) 
                and (numberOfCalls <= len(history))):  # history is limited
                history = history[:(len(history) - 1)]  # remove oldest call
            # finally calculate and memoize result for new parameters
            result = function(*args, **kwargs)  # execute memorized function
            history.insert(0, ((args, kwargs), result))  # add call as last recent call
            return(result)  
        return(executor)
    return(decorator)


# Executable Script
if __name__ == "__main__":
    pass


