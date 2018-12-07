"""Product Trader Pattern

This class implements a simple version of the Product Trader Pattern:
A SimpleProductTrader manages a registry mapping specifications to classes. 
Strings are used as Specification. 
For each Product, a SimpleProductTrader is created. 
Subclasses of Product register with this SimpleProductTrader. 
To instantiate a (subclass of) Product, the appropriate class is retrieved 
from the SimpleProductTrader using the Specification. 

(c) by nobisoft 2015-
"""


# Imports
## Standard
import logging
## Contributed
## nobi
## Project


class SimpleProductTrader(object): 
    """Implement a simple Product Trader, using strings to specify the class to instantiate.
    """
    

# Constants



# Class Methods
#     @classmethod




# Lifecycle
    def __init__(self):
        """Create a SimpleProductTrader with empty registry.
        """
        # inheritance
        super(SimpleProductTrader, self).__init__()
        # internal state
        self.productRegistry = {}  # mapping String to Class
        # 
        return(None)



# Getters
    def isKnown(self, specString):
        """Return True is specString is a known specification, i.e., getClassFor() would return a valid class.
        
        String specString
        Return Boolean
        """
        return(specString in self.productRegistry)


    def getClassFor(self, specString):
        """Return the class to which specString is mapped.
        
        BaseException when specString was not registered.
        
        Returns Class
        """
        if (self.isKnown(specString)):
            return(self.productRegistry[specString])
        else:
            raise(BaseException('Specification "%s" not found in registry of SimpleProductTrader' % specString))
        
    
    def getClasses(self):
        """Return the set of classes registered.
        """
        return(set(self.productRegistry.values()))



# Setters
    def registerClassFor(self, clas, specString):
        """Inform the product trader that clas handles specString.
        """
        if (specString in self.productRegistry):
            # raise(BaseException('Specification "%s" already used in SimpleProductTrader' % specString))
            logging.warning('Overwriting specification "%s" in SimpleProductTrader' % specString) 
        self.productRegistry[specString] = clas


