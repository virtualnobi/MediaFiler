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
# Globals
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


def makeUnique(path):
    """Return a unique filename based on path. 
    
    If path does not exist, return it unchanged. If it exists, add a counter to make it unique.
    
    String path
    Return String path
    """
    if (os.path.exists(path)):
        (root, ext) = os.path.splitext(path)
        count = 1
        newPath = os.path.join('%s-%d%s' % (root, count, ext))  
        while (os.path.exists(newPath)):
            count = (count + 1)
            newPath = os.path.join('%s-%d%s' % (root, count, ext))  
        return(newPath)
    else:
        return(path)


# def makeUnique2(path, countFormat='-%d'):  # TODO: create test infrastructure
#     """Return a unique filename based on path. 
#     
#     path must contain '%s' where the unique number is inserted. 
#     If path (with '%s' replaced by the empty string) exists, 
#     successively larger numbers will be inserted in place of '%s'
#     until there is no file with this number. 
#     The unique path is returned. 
#     
#     If path does not exist, return it unchanged. If it exists, add a counter to make it unique.
#     
#     String path must contain '%s' 
#     String countFormat specifies how the number is formatted
#     Raises ValueError if path does not contain '%s'
#     Return String path
#     """
#     if (path.index('%s') == -1):
#         raise ValueError, ('Path argument does not contain ''%s''!')
#     if (countFormat.index('%d') == -1):
#         raise ValueError, ('Format argument does not contain ''%d''!')
#     if (os.path.exists(path % '')):
#         count = 1
#         newPath = os.path.join(path % (countFormat % count))  
#         while (os.path.exists(newPath)):
#             count = (count + 1)
#             newPath = os.path.join(path % (countFormat % count))  
#     else:
#         return(path % '')



# Executable Script
if __name__ == "__main__":
    import datetime
    import time
    (testDir, dummy) = os.path.split(__file__)
    # test touch()
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
        print('Testing nobi.os.touch() successful!')
    else:
        print('Cannot test nobi.os.touch() as "%s" already exists!' % testFile)   
    # test makeUnique()
    testFile = os.path.join(testDir, 'unique.txt')
    uniqueFile = os.path.join(testDir, 'unique-1.txt')
    assert (makeUnique(testFile) == testFile), ('nobi.os.makeUnique(): Wrong filename when it does not exist - "%s"' % makeUnique(testFile)) 
    touch(testFile)
    assert (makeUnique(testFile) == uniqueFile), ('nobi.os.makeUnique(): Wrong filename when it does exist - "%s"' % makeUnique(testFile))
    os.remove(testFile) 
    print('Testing nobi.os.makeUnique)() successful!')
         
    
