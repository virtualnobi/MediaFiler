#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""
# Imports
## Standard
from __future__ import print_function
import unittest
import StringIO
## Contributed
## nobi
## Project
import Model.Installer  # to resolve import sequence issues  TODO:
from OrganizationByDate import OrganizationByDate



class TestOrganizationByDate(unittest.TestCase):
    """
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
    def testDeriveDateFromPath(self):
#         self.assertTrue(True, 'message')
#         self.assertFalse(False, 'message')
#         with self.assertRaises(ValueError):
#             PartialDateTime('non-date string')
        self.verifyInvalidDate('/test/548183.rest')
        self.verifyInvalidDate('/test/IMG_1957.JPG')
        self.verifyInvalidDate('/test/nobi.2005.rest')
        self.verifyInvalidDate('/test/01.04.00.rest')

        self.checkDeriveDateFromPath('/test/2000-04-01.rest', '2000', '04', '01')
        self.checkDeriveDateFromPath('/test/00-04-01.rest', '2000', '04', '01')
        self.checkDeriveDateFromPath('/test/01.04.2000.rest', '2000', '04', '01')
        self.checkDeriveDateFromPath('/test/01.04.00.rest', '2000', '04', '01')

        self.checkDeriveDateFromPath('\\test\\1980-03.Algerien\\234.jpg', '1980', '03', None)
        self.checkDeriveDateFromPath('\\test\\2015-02.Schwellbrunn\\IMG_1980.jpg', '2015', '02', None)

        self.checkDeriveDateFromPath('/test/2005.nobi.rest', '2005', None, None)
        self.checkDeriveDateFromPath('/test/2008-nobi-Holger.png', '2008', None, None)

        self.checkDeriveDateFromPath('/test/20150930-_MG_2425.rest', '2015', '09', '30')
        self.checkDeriveDateFromPath('/test/IMG_20150809_175625.jpg', '2015', '08', '09')
        self.checkDeriveDateFromPath('\\test\\2015-02.Schwellbrunn\\IMG_20150219_175347.jpg', '2015', '02', '19')



# Internal - to change without notice
    def verifyInvalidDate(self, path):
        """
        """
        self.checkDeriveDateFromPath(path, OrganizationByDate.UnknownDateName, None, None)


    def checkDeriveDateFromPath(self, path, targetYear, targetMonth, targetDay):
        """
        """
        log = StringIO.StringIO()
        (year, month, day, rest) = OrganizationByDate.deriveDateFromPath2(log, path)
        if ((year, month, day, rest) <> OrganizationByDate.deriveDateFromPath(log, path)):
            print('Derived dates differ for "%s"' % path)
        self.assertEqual((year, month, day), 
                         (targetYear, targetMonth, targetDay),
                         ('Failure at "%s" with rest "%s"' % (path, rest)))



# Class Initialization
pass



# Executable Script
if __name__ == '__main__':
    unittest.main()
