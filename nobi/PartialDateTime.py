#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
from __future__ import print_function
import datetime
from __builtin__ import str
from numbers import Number
import re
## Contributed
## nobi
## Project



class PartialDateTime(object): 
    """Defines a generalization of the datetime.datetime objects, which allows to leave time, day, month, or year
    unspecified. 
    
    When comparing, a partial date will be smaller than a more specific (partial) date. 
    So, 2017 will be smaller than 2017-01, which in turn will be smaller than 2017-01-01.  
    
    Consider PartialDateTime objects as unmutable.
    """
    

# Constants
    ConstantName = 'value'


# Class Variables



# Class Methods
# Lifecycle
    def __init__(self, *args):
        """Return a new PartialDateTime representing a (possibly imprecise) timestamp.
        
        There are different ways to create the timestamp: 
        - using a single datetime.datetime object
        - using a single datetime.date object
        - using a string (str or unicode object) of the form "YYYY-MM-DD"
        - using year, month, day as a triple of Numbers or None
        In the latter two cases, the precision can be reduced by shorter strings or passing None. Of course, 
        shorter periods must be unpsecified if longer periods are unspecified (i.e., day must be None if 
        month is None). 
        PartialDateTime('') is a completely unspecified timestamp, 
        and PartialDateTime(2000, None, None) is specified only for the year. 
        
        As far as periods are specified, they must conform to datetime.datetime requirements regarding 
        value ranges and consistency. Raises ValueError if the parameters are incorrect. 
        
        Comparing PartialDateTime objects is based on the idea that a partial timestamp will be both earlier 
        and later than a more precise timestamp. So '2000' will be smaller and larger than '2000-02', which in 
        turn is smaller and larger than '2000-02-15'. 
        """
        # inheritance
        super(PartialDateTime, self).__init__()
        # internal state
        self.year = None
        self.month = None
        self.day = None
        self.time = None
        if (len(args) == 1):
            arg = args[0]
            if (isinstance(arg, datetime.datetime)):
                self.year = arg.year
                self.month = arg.month
                self.day = arg.day
                self.time = arg.time
            elif (isinstance(arg, datetime.date)):
                self.year = arg.year
                self.month = arg.month
                self.day = arg.day
            elif (isinstance(arg, str)):
                match = re.match('^(?:(\d\d\d\d)(?:-(\d\d)(?:-(\d\d))?)?)?$', arg)
                if (match):
                    if (match.group(1)):
                        self.year = int(match.group(1))
                        if (match.group(2)):
                            self.month = int(match.group(2))
                            if (match.group(3)):
                                self.day = int(match.group(3))
                else:
                    raise ValueError
            else:
                raise ValueError
        elif (len(args) == 3):
            if (isinstance(args[0], Number)):
                self.year = args[0]
                if (isinstance(args[1], Number)):
                    self.month = args[1]
                    if (isinstance(args[2], Number)):
                        self.day = args[2]
                    elif (args[2] != None):
                        raise ValueError
                elif (args[1] == None):
                    if (args[2] != None):
                        raise ValueError
                else:
                    raise ValueError 
            elif (args[0] == None):
                if ((args[1] != None)
                    or (args[2] != None)):
                    raise ValueError
            else:
                raise ValueError 
        else:
            raise ValueError
        if (self.year
            and ((self.year < datetime.MINYEAR)
                 or (datetime.MAXYEAR < self.year))):
            raise ValueError
        if (self.month
            and ((self.month < 1)
                 or (12 < self.month))):
            raise ValueError
        if (self.day
            and ((self.day < 1)
                 or (31 < self.day))):  # TODO: correctly check for max day of month
            raise ValueError
        return(None)



# Setters
# Getters
    def getYear(self):
        return(self.year)
        
        
    def getMonth(self):
        return(self.month)
        

    def getDay(self):
        return(self.day)


    def getTime(self):
        return(self.time)



# Event Handlers
# Inheritance - Superclass
# Other API Functions
    def __lt__(self, other):
        """
        """
        if (self.year == other.year):
            if (self.month == other.month):
                if (self.day == other.day):
                    if (self.time == other.time):
                        return(False)
                    elif (self.time == None):
                        return(True)
                    elif (other.time == None):
                        return(False)
                    else: 
                        return(self.time < other.time)
                elif (self.day == None):
                    return(True)
                elif (other.day == None):
                    return(False)
                else: 
                    return(self.day < other.day)
            elif (self.month == None):
                return(True)
            elif (other.month == None):
                return(False)
            else: 
                return(self.month < other.month)
        elif (self.year == None):
            return(True)
        elif (other.year == None):
            return(False)
        else: 
            return(self.year < other.year)


    def __le__(self, other):
        """
        """
        if (self.year == other.year):
            if (self.month == other.month):
                if (self.day == other.day):
                    if (self.time == other.time):
                        return(True)
                    elif (self.time == None):
                        return(True)
                    elif (other.time == None):
                        return(False)
                    else: 
                        return(self.time <= other.time)
                elif (self.day == None):
                    return(True)
                elif (other.day == None):
                    return(False)
                else: 
                    return(self.day <= other.day)
            elif (self.month == None):
                return(True)
            elif (other.month == None):
                return(False)
            else: 
                return(self.month <= other.month)
        elif (self.year == None):
            return(True)
        elif (other.year == None):
            return(False)
        else: 
            return(self.year <= other.year)


    def __gt__(self, other):
        """
        """
        if (self.year == other.year):
            if (self.month == other.month):
                if (self.day == other.day):
                    if (self.time == other.time):
                        return(False)
                    elif (self.time == None):
                        return(True)
                    elif (other.time == None):
                        return(False)
                    else: 
                        return(self.time > other.time)
                elif (self.day == None):
                    return(True)
                elif (other.day == None):
                    return(False)
                else: 
                    return(self.day > other.day)
            elif (self.month == None):
                return(True)
            elif (other.month == None):
                return(False)
            else: 
                return(self.month > other.month)
        elif (self.year == None):
            return(True)
        elif (other.year == None):
            return(False)
        else: 
            return(self.year > other.year)


    def __ge__(self, other):
        """
        """
        if (self.year == other.year):
            if (self.month == other.month):
                if (self.day == other.day):
                    if (self.time == other.time):
                        return(True)
                    elif (self.time == None):
                        return(True)
                    elif (other.time == None):
                        return(False)
                    else: 
                        return(self.time >= other.time)
                elif (self.day == None):
                    return(True)
                elif (other.day == None):
                    return(False)
                else: 
                    return(self.day >= other.day)
            elif (self.month == None):
                return(True)
            elif (other.month == None):
                return(False)
            else: 
                return(self.month >= other.month)
        elif (self.year == None):
            return(True)
        elif (other.year == None):
            return(False)
        else: 
            return(self.year >= other.year)


    def __eq__(self, other):
        """
        """
        if ((self.year == other.year)
            and (self.month == other.month)
            and (self.day == other.day)
            and (self.time == other.time)): 
            return(True)
        else:
            return(False)


    def __ne__(self, other):
        """
        """
        return(not (self == other))


        
# Internal - to change without notice
    pass


# Class Initialization
pass



# Executable Script
if __name__ == "__main__":
    pass


