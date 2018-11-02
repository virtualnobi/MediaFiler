#!python
# -*- coding: latin-1 -*-
"""
(c) by nobisoft 2016-
"""


# Imports
## Standard
from ConfigParser import SafeConfigParser 
## Contributed
## nobi
## Project



class SecureConfigParser(SafeConfigParser):
    """A subclass of SafeConfigParser which adds two security features: 
    - it will save all changes to the configuration immediately (i.e., when .set() is called)
    - it will assume all values are unicode() and encode them using UTF-8 before saving
    
    A design issue is whether the filename to read and write from should be given in the 
    constructor (as done currently), or whether it can be derived from calls to .read() and .write(). 
    The second option might end up with the .set() method called before the filename is known, and 
    thus no possibility to save the value immediately.
    
    There is no validation of the filenames; it is possible to read the configuration from different
    files than the one which is used to store the configuration. 
    """
    

# Constants
    EncodingName = 'UTF-8'


# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, filename):
        """Create a new SecureConfigParser.

        String filename specifies the configuration file to write any changes to.
        """
        SafeConfigParser.__init__(self)
        self.filename = filename
        return(None)



# Setters
# Getters
# Event Handlers
# Inheritance - Superclass
    def set(self, section, option, value):
        """Set an option in a section to a value, and save the configuration.
        
        Encodes value as UTF-8.
        
        String section
        String option
        unicode value
        """
        encodedValue = unicode(value).encode(self.EncodingName, 'replace')
        SafeConfigParser.set(self, section, option, encodedValue)
        with open(self.filename, 'w') as f:
            self.write(f)


    def get(self, section, option):
        """Read the configuration value for option in section. 
        
        Returns decoded String
        """
        encodedValue = SafeConfigParser.get(self, section, option, raw=True)
        value = encodedValue.decode(self.EncodingName, 'replace')
        return(value)
    


# Other API Functions
# Internal - to change without notice
# Class Initialization
# Executable Script
if __name__ == "__main__":
    pass


    
