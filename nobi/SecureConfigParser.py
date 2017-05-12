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
    
    A design issue whether the filename to read and write from should be given in the constructor (as done currently), 
    or whether it can be derived from calls to .read() and .write(). 
    The second option might end up with the .set() method called before the filename is known.
    """
    

# Constants
    EncodingName = 'UTF-8'


# Class Variables
# Class Methods
# Lifecycle
    def __init__(self, filename):
        """
         
        String filename names the file to store the configuration in
        """
#         super(SecureConfigParser, self).__init__()
        SafeConfigParser.__init__(self)
        self.filename = filename  # TODO: ensure this is the filename used for reading
        return(None)



# Setters
# Getters
# Event Handlers
# Inheritance - Superclass
#     def read(self, filenames):
#         """
#         """
#         result = SafeConfigParser.read(self, filenames)
#         if (len(result) > 0):
#             if (result[0] <> self.filename):
#                 raise 'File "%s" to store configuration is not the first successfully read configuration file!'
#             self.filename = result[0]
#         return(result)
# 
# 
#     def write(self, fileobject):
#         """
#         """
#         result = SafeConfigParser.write(fileobject)
#         return(result)


    def set(self, section, option, value):
        """Set an option in a section to a value, and save the configuration.
        
        String section
        String option
        unicode value
        """
        encodedValue = unicode(value).encode(self.EncodingName, 'replace')
#        super(SecureConfigParser, self).set(section, option, encodedValue)
        SafeConfigParser.set(self, section, option, encodedValue)
        with open(self.filename, 'w') as f:
            self.write(f)

    
    def get(self, section, option):
#        encodedValue = super(SecureConfigParser, self).get(section, option)
        encodedValue = SafeConfigParser.get(self, section, option)
        value = encodedValue.decode(self.EncodingName, 'replace')
        return(value)
    


# Other API Functions
# Internal - to change without notice
# Class Initialization
# Executable Script
if __name__ == "__main__":
    pass


    
