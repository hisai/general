#!/bin/env blue-python2.7
import os
import sys
import subprocess
import logging
import fcntl
import time
from optparse import OptionParser
from contextlib import contextmanager
'''
This script contains common functions that will be used others for logging, RUNNING cmd etc
'''

# A dummy exception class to tag the pkgeventerror
class PkgeventError(Exception): 
    pass

def get_logger(logger_name, log_file):
    '''
    Expect the logfile to write to and return the logger object 
    '''
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    #streamHandler = logging.StreamHandler()
    #streamHandler.setFormatter(formatter)

    l.setLevel(20)
    l.addHandler(fileHandler)
    #l.addHandler(streamHandler) 


@contextmanager
def get_lock(lockfile):
    '''this basically yields a lock on the
    '''
    try:
        fd = open(lockfile, 'w+')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except IOError:
        raise



def run_cmd( cmd, logger, cmd_out=False):
    '''
    Expects 
    cmd    - the actual command to run
    logger - the logging object to write the log to
    '''
    start_ts = time.time()
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    out = p.communicate()[0]
    if p.returncode != 0:
        logger.info("[FAIL] [exit code %s]  %s" % (p.returncode,' '.join(cmd)))
        for line in out.decode('utf8').split("\n"):
            if not line:
                next
            line = line.strip()
            logger.info(" `-> %s", line)
        raise PkgeventError('[ERROR] in run_cmd() - %s' % line)
    
    end_ts = time.time()
    approx_runtime = end_ts - start_ts
    logger.info("[SUCCESS] approx runtime - %f seconds, cmd - %s" % (approx_runtime, ' '.join(cmd)))
    if cmd_out == True:
        return out
    else:
        return True

def updaterepos(repos, logger):
    '''expects a list of directories to run createrepo on'''

    crepo      = '/usr/bin/createrepo_c'
    crepo_lock = 'createrepo.lock'
    crepo_args = [ '--update', '--workers=10' ]
    action     = 'UPDATE_REPO'
    for repo in set(repos):
        repo = repo.strip()
        cmd = sum([ [crepo], crepo_args, [repo] ], [])
        lockfile=os.path.join(repo, crepo_lock)
        try:
            with get_lock(lockfile):
                logger.info("[RUNNING] %s on %s" % (action, repo))
                run_cmd(cmd, logger)
        except:
            e = sys.exc_info()
            logger.info("[FAIL] %s could not be grabbed. Exception: %s" % (lockfile, e))
            raise PkgeventError('%s' % e)

if __name__ == '__main__':
    print "This is a helper functions script"
    
