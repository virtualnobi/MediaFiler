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
#import Model.Installer  # to resolve import sequence issues  
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

        self.checkDeriveDateFromPath('/test/2000-04-01.rest', '2000', '04', '01', '.rest')
        self.checkDeriveDateFromPath('/test/00-04-01.rest', '2000', '04', '01', '.rest')
#        self.checkDeriveDateFromPath('/test/01.04.2000.rest', '2000', '04', '01')
#        self.checkDeriveDateFromPath('/test/01.04.00.rest', '2000', '04', '01')
        self.checkDeriveDateFromPath('/test/nobi.2005.rest', '2005', None, None, '.rest')

        self.checkDeriveDateFromPath('\\test\\1980-03.Algerien\\234.jpg', '1980', '03', None, '.Algerien\\234.jpg')
        self.checkDeriveDateFromPath('\\test\\2015-02.Schwellbrunn\\IMG_1980.jpg', '2015', '02', None, '.Schwellbrunn\\IMG_1980.jpg')
        self.checkDeriveDateFromPath('/test/IMG_1957.JPG', '1957', None, None, '.JPG')

        self.checkDeriveDateFromPath('/test/2005.nobi.rest', '2005', None, None, '.nobi.rest')
        self.checkDeriveDateFromPath('/test/2008-nobi-Holger.png', '2008', None, None, '-nobi-Holger.png')
        self.checkDeriveDateFromPath('\\test\\0000\\0000-001.rest', '0000', None, None, '-001.rest')

#        self.checkDeriveDateFromPath('/test/20150930-_MG_2425.rest', '2015', '09', '30')
#        self.checkDeriveDateFromPath('/test/IMG_20150809_175625.jpg', '2015', '08', '09')
#        self.checkDeriveDateFromPath('\\test\\2015-02.Schwellbrunn\\IMG_20150219_175347.jpg', '2015', '02', '19')



# Internal - to change without notice
    def verifyInvalidDate(self, path):
        """
        """
        self.checkDeriveDateFromPath(path, OrganizationByDate.UnknownDateName, None, None, None)


    def checkDeriveDateFromPath(self, path, targetYear, targetMonth, targetDay, targetRest=None):
        """
        """
        log = StringIO.StringIO()
        (year, month, day, rest) = OrganizationByDate.deriveDateFromPath(log, path)
        self.assertEqual((year, month, day), 
                         (targetYear, targetMonth, targetDay),
                         ('Failure at "%s": %s-%s-%s with rest "%s"' % (path, year, month, day, rest)))
        if (targetRest <> None):
            self.assertEqual(targetRest, rest, ('Failure at "%s": Rest "%s" unequal to "%s"' % (path, rest, targetRest)))



# Class Initialization
pass



# Executable Script
if __name__ == '__main__':
    unittest.main()
