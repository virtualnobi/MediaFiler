#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
from __future__ import print_function
import unittest
import datetime
## Contributed
## nobi
from PartialDateTime import PartialDateTime
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
        self.assertTrue(PartialDateTime('2000'), 'Year string failed')
        self.assertTrue(PartialDateTime('2000-01'), 'Year-Month string failed')
        self.assertTrue(PartialDateTime('2000-01-24'), 'Year-Month-Day string failed')
        with self.assertRaises(ValueError):
            PartialDateTime('non-date string')


    def testCreationFromDateTime(self):
        self.assertTrue(PartialDateTime(datetime.datetime.now()), 'datetime.now() failed')


    def testCreationFromDate(self):
        self.assertTrue(PartialDateTime(datetime.date.today()), 'date.today() failed')


    def testCreationFromNumbers(self):
        self.assertTrue(PartialDateTime(None, None, None), '3xNone failed')
        self.assertTrue(PartialDateTime(2000, None, None), '2xNone failed')
        self.assertTrue(PartialDateTime(2000, 1, None), '1xNone failed')
        self.assertTrue(PartialDateTime(2000, 1, 24), '0xNone failed')
        with self.assertRaises(ValueError):
            PartialDateTime(-10)
            PartialDateTime(2000, 13)
            PartialDateTime(2000, -1)
            PartialDateTime(2000, 1, 40)
            PartialDateTime(2000, 1, -2)
            PartialDateTime(2000, None, 24)


    def testComparison(self):
        self.assertFalse((PartialDateTime('') < PartialDateTime('')))
        self.assertTrue((PartialDateTime('') <= PartialDateTime('')))
        self.assertTrue((PartialDateTime('') == PartialDateTime('')))
        self.assertTrue((PartialDateTime('') >= PartialDateTime('')))
        self.assertFalse((PartialDateTime('') > PartialDateTime('')))
        self.assertFalse((PartialDateTime('') != PartialDateTime('')))

        self.assertTrue(PartialDateTime(datetime.date.today()) < PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) <= PartialDateTime(datetime.datetime.now()))
        self.assertFalse(PartialDateTime(datetime.date.today()) == PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) >= PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) > PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) != PartialDateTime(datetime.datetime.now()))

        self.assertFalse((PartialDateTime('') < PartialDateTime(None, None, None)))
        self.assertTrue((PartialDateTime('') <= PartialDateTime(None, None, None)))
        self.assertTrue((PartialDateTime('') == PartialDateTime(None, None, None)))
        self.assertTrue((PartialDateTime('') >= PartialDateTime(None, None, None)))
        self.assertFalse((PartialDateTime('') > PartialDateTime(None, None, None)))
        self.assertFalse((PartialDateTime('') != PartialDateTime(None, None, None)))
        
        self.assertFalse((PartialDateTime('2000-01-24') < PartialDateTime(2000, 1, 24)))
        self.assertTrue((PartialDateTime('2000-01-24') <= PartialDateTime(2000, 1, 24)))
        self.assertTrue((PartialDateTime('2000-01-24') == PartialDateTime(2000, 1, 24)))
        self.assertTrue((PartialDateTime('2000-01-24') >= PartialDateTime(2000, 1, 24)))
        self.assertFalse((PartialDateTime('2000-01-24') > PartialDateTime(2000, 1, 24)))
        self.assertFalse((PartialDateTime('2000-01-24') != PartialDateTime(2000, 1, 24)))
        
        self.assertTrue((PartialDateTime('2000') < PartialDateTime('2000-01')))
        self.assertTrue((PartialDateTime('2000') <= PartialDateTime('2000-01')))
        self.assertFalse((PartialDateTime('2000') == PartialDateTime('2000-01')))
        self.assertTrue((PartialDateTime('2000') >= PartialDateTime('2000-01')))
        self.assertTrue((PartialDateTime('2000') > PartialDateTime('2000-01')))
        self.assertTrue((PartialDateTime('2000') != PartialDateTime('2000-01')))

        self.assertTrue((PartialDateTime('2000-01') < PartialDateTime('2000-01-24')))
        self.assertTrue((PartialDateTime('2000-01') <= PartialDateTime('2000-01-24')))
        self.assertFalse((PartialDateTime('2000-01') == PartialDateTime('2000-01-24')))
        self.assertTrue((PartialDateTime('2000-01') >= PartialDateTime('2000-01-24')))
        self.assertTrue((PartialDateTime('2000-01') > PartialDateTime('2000-01-24')))
        self.assertTrue((PartialDateTime('2000-01') != PartialDateTime('2000-01-24')))
        
        self.assertFalse((PartialDateTime('2000-01-24') < PartialDateTime('2000-01')))
        self.assertFalse((PartialDateTime('2000-01-24') <= PartialDateTime('2000-01')))
        self.assertFalse((PartialDateTime('2000-01-24') == PartialDateTime('2000-01')))
        self.assertFalse((PartialDateTime('2000-01-24') >= PartialDateTime('2000-01')))
        self.assertFalse((PartialDateTime('2000-01-24') > PartialDateTime('2000-01')))
        self.assertTrue((PartialDateTime('2000-01-24') != PartialDateTime('2000-01')))


# Internal - to change without notice
# Class Initialization
pass



# Executable Script
if __name__ == '__main__':
    unittest.main()
