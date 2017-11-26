"""
Extensions to the os module.

(c) by nobisoft 2016-
"""

# Imports
## Standard
from __future__ import print_function
import subprocess
import os
## Contributed
## nobi



# Constants
ConstantName = 'value'



# Globals
var = 'value'


# Functions
def touch(path):
    """Create an empty file for path, if it does not yet exist. Change the file's modification time to now.
    """
    if (os.name == 'nt'):
        noFile = open(os.devnull)
        if (not os.path.exists(path)):
            subprocess.call(('type nul > %s' % path), stdout=noFile, stderr=noFile, shell=True)
        else:
            subprocess.call(('copy /b %s+,, %s' % (path, path)), stdout=noFile, stderr=noFile, shell=True) 
    else:
        raise('nobi.os.touch(): Unsuppported (as of yet) OS "%s"' % os.name)



# Executable Script
if __name__ == "__main__":
    import datetime
    import time
    # test touch()
    (testDir, dummy) = os.path.split(__file__)
    testFile = os.path.join(testDir, 'touched')
    if (not os.path.exists(testFile)):
        touch(testFile)
        assert os.path.exists(testFile), ('nobi.os.touch(): Creation of "%s" failed!' % testFile)
        currentTime = datetime.datetime.now()
        time.sleep(1)
        touch(testFile)
        fileAccessTime = datetime.datetime.fromtimestamp(os.stat(testFile).st_mtime)
        assert (currentTime < fileAccessTime), ('nobi.os.touch(): Touching "%s" did not update its access time' % testFile)
        os.remove(testFile)
    else:
        print('Cannot test nobi.os.touch() as "%s" already exists!' % testFile)        
    
