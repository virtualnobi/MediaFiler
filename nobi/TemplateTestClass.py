#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2017-
"""
# Imports
## Standard
from __future__ import print_function
import unittest
## Contributed
## nobi
## Project



class TestPartialDateTime(unittest.TestCase):
    """unittest for the PartialDateTime class.
    """
    
    

# Constants
# Class Variables
# Class Methods
# Lifecycle
# Setters
# Getters
# Event Handlers
# Inheritance - Superclass
# Other API Functions
    def testCreateFromString(self):
        self.assertTrue(PartialDateTime(''), 'Empty string failed')
        self.assertFalse((PartialDateTime('') < PartialDateTime('')))
        self.assertEqual(datetime.datetime.now(), 
                         PartialDateTime(datetime.datetime.now()).getEarliestDateTime(), 
                         'Conversion of now() to earliest datetime failed')
        with self.assertRaises(ValueError):
            PartialDateTime('non-date string')



# Internal - to change without notice
# Class Initialization
pass



# Executable Script
if __name__ == '__main__':
    unittest.main()
