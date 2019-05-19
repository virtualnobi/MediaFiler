#!python
# -*- coding: latin-1 -*-
"""
Taken from the Python 2.7.10 documentation
"""


# Imports
## Standard
from __future__ import print_function
from collections import OrderedDict
## Contributed
## nobi
## Project



class LastUpdateOrderedDict(OrderedDict):
    """Store items in the order the keys were added, last addition is last entry.
    """



# Lifecycle
# Getters
# Setters
    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)



# Inheritance - Superclass
# Other API Functions
# Internal - to change without notice
# Class Initialization
# Executable Script
if __name__ == "__main__":
    pass

