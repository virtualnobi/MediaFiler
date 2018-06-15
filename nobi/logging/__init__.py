"""
Extensions to the wxPython module.

(c) by nobisoft 2018-
"""


from __future__ import print_function
import cProfile
import pstats
import StringIO
import logging


def profiledOnLogger(logger, sort='time'):
    """Return a decorator which will profile a function and log the profiling information (at the DEBUG level). 

    Sorting the function calls can be done by
    'time' for the total time spent in a function, excluding sub-functions
    'cumulative' for the total time spent in a function, including time spent in sub-functions
        
    logging.Logger logger to emit the message to
    String sort passed to pstats.sort_stats()
    Returns Callable usable as decorator
    """
    def decorator(function):
        def executor(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            result = function(*args, **kwargs)
            profiler.disable()
            resultStream = StringIO.StringIO()
            ps = pstats.Stats(profiler, stream=resultStream)  
            ps.strip_dirs()  # remove module paths
            ps.sort_stats(sort)
            ps.print_stats(20)  # print top 20 
            logger.debug('---Profiling Results for %s' % function)
            logger.debug(resultStream.getvalue())
            logger.debug('---')
            return(result)
        return(executor)
    return(decorator)


def profiled(function):
    """Return a function which will profile the execution of the specified function and print the stats to stdout.
    
    function function
    Returns function
    """
    def executor(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = function(*args, **kwargs)
        profiler.disable()
        resultStream = StringIO.StringIO()
        ps = pstats.Stats(profiler, stream=resultStream)  
        ps.strip_dirs()  # remove module paths
        # ps.sort_stats('cumulative')  # sort according to time per function call, including called functions
        ps.sort_stats('time')  # sort according to time per function call, excluding called functions
        ps.print_stats(20)  # print top 20 
        print('---Profiling Results for %s' % function)
        print(resultStream.getvalue())
        print('---')
        return(result)
    return(executor)

