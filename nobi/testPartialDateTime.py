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
from nobi.PartialDateTime import PartialDateTime
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
        self.assertTrue(PartialDateTime(datetime.datetime.now()), 'Failed for datetime.now()')
        self.assertTrue(PartialDateTime(datetime.datetime.min), 'Failed for datetime.min')
        self.assertTrue(PartialDateTime(datetime.datetime.max), 'Failed for datetime.max')


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
            PartialDateTime(2000, 0, 1)


    def testComparison(self):
        self.assertFalse((PartialDateTime('') < PartialDateTime('')))
        self.assertTrue((PartialDateTime('') <= PartialDateTime('')))
        self.assertTrue((PartialDateTime('') == PartialDateTime('')))
        self.assertTrue((PartialDateTime('') >= PartialDateTime('')))
        self.assertFalse((PartialDateTime('') > PartialDateTime('')))
        self.assertFalse((PartialDateTime('') != PartialDateTime('')))

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

        self.assertTrue(PartialDateTime(datetime.date.today()) < PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) <= PartialDateTime(datetime.datetime.now()))
        self.assertFalse(PartialDateTime(datetime.date.today()) == PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) >= PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) > PartialDateTime(datetime.datetime.now()))
        self.assertTrue(PartialDateTime(datetime.date.today()) != PartialDateTime(datetime.datetime.now()))

        self.assertTrue(PartialDateTime(datetime.date.today()) < datetime.datetime.now())
        self.assertTrue(PartialDateTime(datetime.date.today()) <= datetime.datetime.now())
        self.assertTrue(PartialDateTime(datetime.date.today()) == datetime.datetime.now())
        self.assertTrue(PartialDateTime(datetime.date.today()) >= datetime.datetime.now())
        self.assertTrue(PartialDateTime(datetime.date.today()) > datetime.datetime.now())
        self.assertFalse(PartialDateTime(datetime.date.today()) != datetime.datetime.now())

        self.assertFalse(PartialDateTime(datetime.date.today()) < datetime.date.today())
        self.assertTrue(PartialDateTime(datetime.date.today()) <= datetime.date.today())
        self.assertTrue(PartialDateTime(datetime.date.today()) == datetime.date.today())
        self.assertTrue(PartialDateTime(datetime.date.today()) >= datetime.date.today())
        self.assertFalse(PartialDateTime(datetime.date.today()) > datetime.date.today())
        self.assertFalse(PartialDateTime(datetime.date.today()) != datetime.date.today())


    def testConversionDateTime(self):
        self.assertEqual(datetime.datetime.now(), 
                         PartialDateTime(datetime.datetime.now()).getEarliestDateTime(), 
                         'Conversion of now() to earliest datetime failed')
        self.assertEqual(datetime.datetime.now(), 
                         PartialDateTime(datetime.datetime.now()).getLatestDateTime(), 
                         'Conversion of now() to latest datetime failed')
        self.assertEqual(datetime.datetime(2017, 1, 1),
                         PartialDateTime(2017, None, None).getEarliestDateTime(),
                         'Conversion of year to earliest failed')
        self.assertEqual(datetime.datetime(2017, 12, 31, 23, 59, 59, 999999),
                         PartialDateTime(2017, None, None).getLatestDateTime(),
                         'Conversion of year to latest failed')
        self.assertEqual(datetime.datetime(2017, 4, 1),
                         PartialDateTime(2017, 4, None).getEarliestDateTime(),
                         'Conversion of month to earliest failed')
        self.assertEqual(datetime.datetime(2017, 4, 30, 23, 59, 59, 999999),
                         PartialDateTime(2017, 4, None).getLatestDateTime(),
                         'Conversion of month to latest failed')
        self.assertEqual(datetime.datetime(2017, 5, 1),
                         PartialDateTime(2017, 5, None).getEarliestDateTime(),
                         'Conversion of month to earliest failed')
        self.assertEqual(datetime.datetime(2017, 5, 31, 23, 59, 59, 999999),
                         PartialDateTime(2017, 5, None).getLatestDateTime(),
                         'Conversion of month to latest failed')
        self.assertEqual(datetime.datetime(2017, 4, 15, 0, 0, 0, 0),
                         PartialDateTime(2017, 4, 15).getEarliestDateTime(),
                         'Conversion of day to earliest failed')
        self.assertEqual(datetime.datetime(2017, 4, 15, 23, 59, 59, 999999),
                         PartialDateTime(2017, 4, 15).getLatestDateTime(),
                         'Conversion of day to latest failed')



# Internal - to change without notice
# Class Initialization
pass



# Executable Script
if __name__ == '__main__':
    unittest.main()
