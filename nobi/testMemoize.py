#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2021-
"""


# Imports
## Standard
from __future__ import print_function
import unittest
## Contributed
## nobi
from nobi.Memoize import memoize
## Project



@memoize(2)
def plusOne(number):
    """Test function to be memoized
    """
    print('plusOne(%s) executed' % number)
    return (number + 1)



class testObject(object):
    """Test class to be used as parameter to memoized function
    """
    def __init__(self, name):
        self.name = name



@memoize(2)
def printAndChangeName(to):
    """Test function with object parameter to be memoized.
    """
    print('printName(%s) executed' % to.name)
    to.name = ('%s used' % to.name)
    return(to.name)



@memoize(2)
def noResult(numberOne, numberTwo):
    """Test function to memoize without return statement
    """
    print('noResult(%s, %s) executed' % (numberOne, numberTwo))



class TestMemoize(unittest.TestCase):
    """unittest for the memoize decorator.
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
    @memoize(2)
    def plusTwo(self, number):
        print('plusTwo(%s) executed' % number)
        return (number+2)


    def testFunction(self):
        """Test a simple function

        Should result in 4 printouts of "plusOne executed"
        """
        self.assertEqual(plusOne(1), 2, 'Incorrect result for initial 1 to function')
        self.assertEqual(plusOne(1), 2, 'Incorrect result for memoized 1 to function')
        self.assertEqual(plusOne(2), 3, 'Incorrect result for initial 2 to function')
        self.assertEqual(plusOne(2), 3, 'Incorrect result for memoized 2 to function')
        self.assertEqual(plusOne(3), 4, 'Incorrect result for initial 3 to function')
        self.assertEqual(plusOne(1), 2, 'Incorrect result for memoized 1 over history limit to function')
        # with self.assertRaises(ValueError):
        #     PartialDateTime('non-date string')
        # self.assertFalse((PartialDateTime('') < PartialDateTime('')))
        # self.assertTrue((PartialDateTime('') <= PartialDateTime('')))


    def testMethod(self):
        """Test an object method
        
        Should result in 4 printouts of "plusTwo executed"
        """
        self.assertEqual(self.plusTwo(1), 3, 'Incorrect result for initial 1 to method')
        self.assertEqual(self.plusTwo(1), 3, 'Incorrect result for memoized 1 to method')
        self.assertEqual(self.plusTwo(2), 4, 'Incorrect result for initial 2 to method')
        self.assertEqual(self.plusTwo(2), 4, 'Incorrect result for memoized 2 to method')
        self.assertEqual(self.plusTwo(3), 5, 'Incorrect result for initial 3 to method')
        self.assertEqual(self.plusTwo(1), 3, 'Incorrect result for memoized 1 over history limit to method')
    

    def testNoResult(self):
        """Test a function without return statement
        """
        self.assertIsNone(noResult(21, 21))


    def testObjectReference(self):
        """
        """
        to1 = testObject('Alfred')
        to2 = testObject('Bob')
        to3 = testObject('Alice')
        self.assertEqual(printAndChangeName(to1), 'Alfred used', 'Incorrect result for initial object reference')
        self.assertEqual(printAndChangeName(to1), 'Alfred used', 'Incorrect result for memoized object reference')
        self.assertEqual(printAndChangeName(to2), 'Bob used', 'Incorrect result for initial object reference')
        self.assertEqual(printAndChangeName(to3), 'Alice used', 'Incorrect result for initial object reference')
        self.assertEqual(printAndChangeName(to1), 'Alfred used used', 'Incorrect result for memoized object reference beyond history limit')

        
        
# Internal - to change without notice
# Class Initialization
pass



# Executable Script
if __name__ == '__main__':
    unittest.main()
